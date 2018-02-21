import argparse
import numpy as np

from astropy.io import fits
from fnmatch import fnmatch
from os import path, walk
from glob import glob
from astropy.time import Time, TimeDelta
from copy import copy

def get_files(folder, extension="*.fits"):

    filestore = []

    for root, dirs, files in walk(folder):
        for file_ in files:
            if fnmatch(file_, extension):
                filestore.append(path.join(root, file_))
    return sorted(filestore)

def correct_time(header, num):
    '''Function to fix the UTC time for each frame.'''

    #Load time from header
    t = Time([header['GPSSTART']], format='isot', scale='utc')
    if num % 2 == 0:
        dt = TimeDelta(val=num/2*header['EXPOSURE'], format='sec')
    else:
        dt = TimeDelta(val=(((num-1)/2)+1)*header['EXPOSURE'], format='sec')
    return t + dt


if __name__ == '__main__':

    #Collect arguments from command line
    parser = argparse.ArgumentParser(
        description='Code for stacking images',
        epilog='''Run using ... ''')
    parser.add_argument('-i', metavar='input', help='Input directory',
                        type=str, action='append')
    parser.add_argument('-n', metavar='num', help='Number of images to stack.',
                        type=str, action='append')
    args = parser.parse_args()
    
    #Get file list
    file_list = get_files(args.i[0])

    #Clip excess frames from end of list where there are not enough to form a stack
    num = int(args.n[0])
    max_num = (len(file_list) / num) * num
    file_list = file_list[0:max_num]
    
    stack_count = 0
    for i in range(0, max_num-num, num):
        
        up_index = i + num
        data = 0.        
        prihdr = fits.open(file_list[0])[0].header
        print stack_count

        for count, file_ in enumerate(file_list[i:up_index]):
        
            #Open file, get data
            f = fits.open(file_)
            data += f[0].data[:,:]
            if count == 1:
                #Correct time for stacked image using time of middle frame
                prihdr = copy(f[0].header)
                prihdr['GPSSTART'] = correct_time(prihdr, max_num).isot[0]
            f.close()
            
        #Write new stacked file
        fname = path.basename(file_list[i]).replace('.fits', '_stacked_%d.fits' % stack_count)
        hdu = fits.PrimaryHDU(data, header=prihdr)
        hdu.writeto(path.join(args.i[0], fname), clobber=True)
        stack_count += 1
