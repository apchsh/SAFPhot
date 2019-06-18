#!/usr/bin/env python

'''
SAFPhot - SAAO SHOC REDUCTION AND PHOTOMETRY PIPELINE

An automated pipeline to produce photometry for SAAO 1m, 1.9m telescopes.

This the main script to run the pipeline. Parameters that are passed into the 
scripts are as follows: 

Mandatory:
    - Input directory: folder containing the calibration and science frames
    - Mode: mode the pipeline should run in

Optional:
    - Pattern: prefix pattern for input FITS files, used to select certain
      files

'''

import argparse
import photsort as ps   #SAFPhot script
import reduction as red #SAFPhot script
import unpack as up     #SAFPhot script
import phot as ph       #SAFPhot script
import params           #SAFPhot script

from os.path import join
from os import walk

if __name__ == '__main__':

    #Parse arguments from command line
    parser = argparse.ArgumentParser(
        description='Reduction and photometry pipeline for SHOC data')
    parser.add_argument('dir_in', metavar='dir_in', help='Input directory',
            type=str, action='store')
    parser.add_argument('mode', metavar='mode', 
            help='Mode: [reduction, photometry, both]', type=str, action='store')   
    parser.add_argument('--p', help='prefix search pattern for input FITS file name',
            type=str, dest='pattern')
    args = parser.parse_args()
    
    #Check for optional arguments
    pattern = ""
    if args.pattern is not None:
        pattern = args.pattern

    #Load the list of parameters 
    par = params.get_params()

    #Set the output dir if blank
    if par.out_dir == "": par.out_dir = args.dir_in

    if args.mode in ('both', 'reduction'):

        #Run the file detection and sorting code
        files = ps.fits_sort(par, args.dir_in, pattern, verbose=True)
        files.summary_ra_dec()

        #Create the calibration master files (returns dict of frames)
        calframes = red.create_calframes(files, par, verbose=True)

        #Unpack + reduce the files
        up.unpack_reduce(files, calframes, par, verbose=True)

    if args.mode in ('both', 'photometry'):
 
        #run photometry
        dir_ = join(args.dir_in, par.red_dir)
        
        for root, dirs, files in walk(dir_):
        
            for item in dirs:

                print("Processing frames for photometry on %s" % item) 
                ph.run_phot(args.dir_in, pattern, par, item)

    if args.mode not in ('both', 'reduction', 'photometry'):

        print('Please specify SAFPhot run mode: [reduction, photometry, both]')
