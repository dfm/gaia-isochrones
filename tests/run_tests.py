#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import contextlib

import requests
import numpy as np
import pandas as pd
import astropy.units as u
from astropy.io import ascii, fits
from astropy.coordinates import SkyCoord

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gaia_isochrones.stellar import (  # NOQA
    _parse_gaia_data,
    get_gaia_data,
    fit_gaia_data,
)

gaia_kepler_url = (
    "https://www.dropbox.com/s/xo1n12fxzgzybny/kepler_dr2_1arcsec.fits?dl=1"
)
gaia_kepler_path = "data/kepler_dr2_1arcsec.fits"

if not os.path.exists(gaia_kepler_path):
    r = requests.get(gaia_kepler_url)
    r.raise_for_status()
    with open(gaia_kepler_path, "wb") as f:
        f.write(r.content)

with fits.open(gaia_kepler_path) as f:
    xmatch = f[1].data


def get_gaia_data_for_kepid(kepid):
    matches = xmatch[xmatch["kepid"] == kepid]
    if not len(matches):
        return None
    ind = np.argmin(matches["kepler_gaia_ang_dist"])
    r = matches[ind]
    try:
        return _parse_gaia_data(r)
    except ValueError:
        return None


def get_gaia_data_for_kepids(prefix, kepids):
    return [
        row
        for row in (
            (
                "{0}/kic{1}".format(prefix, kepid),
                get_gaia_data_for_kepid(kepid),
            )
            for kepid in kepids
        )
        if row[1] is not None
    ]


def get_cks_data():
    df = pd.read_csv("data/cks_physical_merged.csv")
    kepids = np.unique(np.array(df.id_kic, dtype=int))
    return get_gaia_data_for_kepids("cks", kepids)


def get_chaplin_data():
    tab = ascii.read("data/chaplin_table4.txt")
    dwarfs = tab[(tab["Radius"] < 2) & (~tab["Radius"].mask)]
    ids1 = np.array(dwarfs["KIC"], dtype=int)

    tab = ascii.read("data/chaplin_table5.txt")
    dwarfs = tab[(tab["Radius"] < 2) & (~tab["Radius"].mask)]
    ids2 = np.array(dwarfs["KIC"], dtype=int)
    kepids = np.unique(np.concatenate((ids1, ids2)))

    return get_gaia_data_for_kepids("chaplin", kepids)


def get_mann_data():
    table = ascii.read("data/Tables5_6_7.txt")
    datasets = []
    for name, ra, dec, mag in zip(
        table["Name"], table["RAdeg"], table["DEdeg"], table["Gaiamag"]
    ):
        datasets.append(
            ("mann/{0}".format(name), {"ra": ra, "dec": dec, "mag": mag})
        )

    return datasets


def run_fit(args):
    output_dir, gaia_data = args
    output_dir = os.path.join("results", output_dir)
    os.makedirs(output_dir, exist_ok=True)

    if "ra" in gaia_data:
        coord = SkyCoord(gaia_data["ra"], gaia_data["dec"], unit=u.deg)
        try:
            gaia_data = get_gaia_data(
                coord, approx_mag=gaia_data["mag"], radius=1 * u.arcmin
            )
        except ValueError:
            return

    with open(os.path.join(output_dir, "stdout.log"), "w") as stdout:
        with open(os.path.join(output_dir, "stderr.log"), "w") as stderr:
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    results = fit_gaia_data(gaia_data, output_dir=output_dir)
                    del results


if __name__ == "__main__":
    import tqdm
    import argparse
    from multiprocessing import Pool, cpu_count

    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=["cks", "chaplin", "mann"])
    parser.add_argument("--threads", "-t", type=int, default=None)
    args = parser.parse_args()

    print("Running '{0}'...".format(args.group))
    if args.group == "cks":
        datasets = get_cks_data()
    elif args.group == "chaplin":
        datasets = get_chaplin_data()
    elif args.group == "mann":
        datasets = get_mann_data()
    else:
        raise RuntimeError("Unknown group")

    print("Found {0} datasets".format(len(datasets)))

    threads = cpu_count()
    if args.threads is not None:
        threads = int(args.threads)
    print("Running in {0} threads".format(threads))

    with tqdm.tqdm(total=len(datasets)) as bar:
        with Pool(threads) as pool:
            for _ in pool.imap_unordered(run_fit, datasets):
                bar.update()
