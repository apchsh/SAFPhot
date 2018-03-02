#!/usr/bin/env python
#================================================#
#                                                                             #
# ========> SAFPHOT - SAAO SHOC REDUCTION AND PHOTOMETRY PIPELINE <========== #
#                                                                             #
#=================================================#
import os
import argparse
import photsort as ps
import reduction as red
import unpack as up

from os.path import join

if __name__ == '__main__':

    #Collect arguments from command line
    parser = argparse.ArgumentParser(
        description='Reduction and photometry pipeline for SHOC data',
        epilog='''Run using ... ''')
    parser.add_argument('-c', metavar='camera', help='Specify the SHOC camera used.',
                        type=str, action='append')
    parser.add_argument('-t', metavar='telescope', help='Specify the telescope used.',
                        type=str, action='append')
    parser.add_argument('-d', metavar='input_dir', help='Input directory with raw files.',
                        type=str, action='append')
    parser.add_argument('-m', metavar='mode', 
            help='Mode: [reduction/photometry/both]',type=str, action='append')

    args = parser.parse_args()
    
    #Check correct telescope input parameter
    if args.t[0] not in ('1.0', '1', '1.', '1.9'):
        raise ValueError('Input telescope parameter value -t  {} not recognised'.format(
                        args.t[0]))

    if args.m[0] in ('both', 'all', 'b', 'a', 'reduction', 'r'):
        #Run the file detection and sorting code
        files = ps.fits_sort(args.d[0], args.c[0], verbose=True)

        files.summary_ra_dec()

        #Create the calibration master files (returns dict of frames)
        calframes = red.create_calframes(files, verbose=True)

        #print files

        #Unpack + reduce the files
        up.unpack_reduce(files, calframes, verbose=True)

    if args.m[0] in ('both', 'all', 'b', 'a', 'photometry', 'phot', 'p'):
        #run photometry
        dir_ = join(args.d[0], 'reduction/')
        for root, dirs, files in os.walk(dir_):
            for item in dirs:
                print "Processing frames for photometry on %s" % item
                
                #Load the correct version of phot depending on the telescope
                if args.t[0] in ('1.9'):
                    import phot_1_point_9m as ph
                    ph.run_phot(dir_, item)

                elif args.t[0] in ('1.0', '1', '1.'):
                    import phot_1_point_0m as ph
                    ph.run_phot(dir_, item)

                else:
                    raise ValueError('Input telescope parameter value -t  {} '\
                            'not recognised'.format(args.t[0]))

    if args.m[0] not in ('both', 'all', 'b', 'a', 'reduction', 'r',
            'photometry', 'p'):
        print 'Please specify Safphot run mode: [reduction/photometry/both]'
