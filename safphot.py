###############################################################################
#                                                                             #
# ===============> SAFPHOT - SAAO 1M PHOTOMETRY PIPELINE <=================== #
#                                                                             #
###############################################################################

'''
NAME
    SAFPHOT - a simple pipeline for processing data from the SAAO 1m using SHOC
SYNOPSIS
    Find files to process in a local directory:
        python safphot.py -t -c SHD|SHA|SHH
DESCRIPTION
'''

import os
import argparse
import photsort as ps
import reduction as red
import unpack as up
import phot as ph

if __name__ == '__main__':

    #Collect arguments from command line
    parser = argparse.ArgumentParser(
        description='Photometry pipeline for SHOC data',
        epilog='''Run using ... ''')
    parser.add_argument('-c', metavar='camera', help='Specify the SHOC camera used.',
                        type=str, action='append')
    parser.add_argument('-d', metavar='input_dir', help='Input directory with raw files.',
                        type=str, action='append')

    args = parser.parse_args()
    print args
    
    
    #Run the file detection and sorting code
    files = ps.fits_sort(args.d[0], args.c[0], verbose=True)

    files.summary_ra_dec()

    #Create the calibration master files (returns dict of frames)
    calframes = red.create_calframes(files, verbose=True)

    #Unpack + reduce the files
    up.unpack_reduce(files, calframes, verbose=True)
    
    #run photometry
    dir_ = args.d[0] + 'reduction/'
    for item in os.listdir(dir_):
        
        print "Processing photometry on %s" % item
        ph.run_phot(dir_, item)




