#!/usr/bin/python
import numpy as np
import argparse

from fitsio import FITS
from astropy.table import Table
from glob import glob
from os.path import join

''' Script to convert FITS table files into ASCII .dat files '''

if __name__ == "__main__":

    #Parse arguments from command line
    parser = argparse.ArgumentParser(
        description='FITS to ASCII .dat file converter')
    parser.add_argument('dir_in', metavar='dir_in', help='Input directory',
            type=str, action='store')
    args = parser.parse_args()

    # Get fits files to convert
    file_list = glob(join(args.dir_in, "*_comp*.fits"))

    # Iterate over files
    for file_ in file_list:

        # Read fits data
        with FITS(file_) as f:
            data = f[1].read()

        # Covert data to Table
        t = Table(data)

        # Write table data as ascii
        t.write(file_.replace(".fits", ".dat"), format="ascii")
