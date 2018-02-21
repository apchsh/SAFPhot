#Script to print out the header of FITS files

import sys
import argparse

from astropy.io import fits
from copy import copy
from os.path import basename

if __name__ == '__main__':

    #Collect arguments from command line
    parser = argparse.ArgumentParser(
        description='FITS file header print out',
        epilog='''Run using ... ''')
    parser.add_argument('-f', metavar='file', help='File path and name',
                        type=str, action='append')
    args = parser.parse_args()

file_ = args.f[0]

f = fits.open(file_)
f_hdr = copy(f[0].header)
f.close()

print (repr(f_hdr))
