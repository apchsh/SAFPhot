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

    #Parse arguments from command line
    parser = argparse.ArgumentParser(
        description='Reduction and photometry pipeline for SHOC data')
    parser.add_argument('camera', metavar='camera', help='Specify the SHOC camera used',
            type=str, action='store')
    parser.add_argument('telescope', metavar='telescope', 
            help='Specify the telescope used (m): [1.0, 1.9]',
            type=str, action='store')
    parser.add_argument('dir_in', metavar='dir_in', help='Input directory',
            type=str, action='store')
    parser.add_argument('mode', metavar='mode', 
            help='Mode: [reduction, photometry, both]',type=str, action='store')
    
    parser.add_argument('--ra', 
            help='Explicit RA of object, to superseed header value',
            type=str, dest='ra')
    parser.add_argument('--dec', 
            help='Explicit DEC of object, to superseed header value',
            type=str, dest='dec')
    args = parser.parse_args()

    #Check correct telescope input parameter
    if args.telescope not in ('1.0', '1', '1.', '1.9'):
        raise ValueError('Input telescope parameter value not recognised'.format(
                        args.telescope))

    if args.mode in ('both', 'all', 'b', 'a', 'reduction', 'r'):
        #Run the file detection and sorting code
        files = ps.fits_sort(args.dir_in, args.camera, verbose=True)

        files.summary_ra_dec()

        #Create the calibration master files (returns dict of frames)
        calframes = red.create_calframes(files, verbose=True)

        #Unpack + reduce the files
        if (args.ra is not None) and (args.dec is not None):
            print "Superseeding header RA and DEC with runtime params..."
            up.unpack_reduce(files, calframes, verbose=True, ra=args.ra,
                    dec=args.dec)
        else:
            up.unpack_reduce(files, calframes, verbose=True)

    if args.mode in ('both', 'all', 'b', 'a', 'photometry', 'phot', 'p'):
        #run photometry
        dir_ = join(args.dir_in, 'reduction/')
        for root, dirs, files in os.walk(dir_):
            for item in dirs:
                print "Processing frames for photometry on %s" % item
                
                #Load the correct version of phot depending on the telescope
                if args.telescope in ('1.9'):
                    import phot_1_point_9m as ph
                    ph.run_phot(dir_, item)

                elif args.telescope in ('1.0', '1', '1.'):
                    import phot as ph
                    ph.run_phot(dir_, item)

                else:
                    raise ValueError('Input telescope parameter value '\
                            'not recognised'.format(args.telescope))

    if args.mode not in ('both', 'all', 'b', 'a', 'reduction', 'r',
            'photometry', 'p'):
        print 'Please specify Safphot run mode: [reduction, photometry, both]'
