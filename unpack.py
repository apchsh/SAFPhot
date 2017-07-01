import pyfits

from os.path import join, exists, basename
from os import makedirs
from astropy.time import Time, TimeDelta
from copy import copy
from glob import glob

def difheader(head1, head2): 
    '''Function for checking the difference between two headers. Not used for
    correction. Just for comparison'''

    #get a list of keys 
    key1 = []
    for key in head1: key1.append(key)
    key2 = [] 
    for key in head2: key2.append(key) 

    #make a copy of key1 to iterate through
    temp = copy(key1)
    for key in temp:
        if (key in key1) and (key in key2):
            key1.remove(key); key2.remove(key)

    return key1, key2 

def correct_time(header, frame_num):
    '''Function to fix the UTC time for each frame.'''

    #Load time from header
    t = Time([header['GPSSTART']], format='isot', scale='utc')
    #Create the time delta object which corrects the exposure time
    dt = TimeDelta(val=frame_num*(header['EXPOSURE']+ 0.00676) +
    header['EXPOSURE'] * 0.5, format='sec')
    return t + dt

def unpack_reduce(files, calframes, verbose=True):

    #prepare for unpacking process
    master_outdir = join(files.dir_ , 'reduction') 

    for file_, target, filt in zip(files.target, files.target_name,
            files.target_filter):    

        if verbose: print "Processing %s: %s " % (target, file_)

        #Create directory within reduction subfolder
        outdir = join(master_outdir, target).replace(' ', '_')
        if not exists(outdir): 
            makedirs(outdir)
            if verbose: print "%s folder created." % outdir
            
        #Open master files
        f = pyfits.open(file_) 
        prihdr = f[0].header    

        for count in range(0, f[0].data.shape[0]):

            temp_header = copy(prihdr)
            red_data = ( f[0].data[count, :, :] - calframes['bias'] ) / calframes[filt]

            newtime = correct_time(temp_header, count)        
            temp_header['JD'] = newtime.jd[0]

            fname = basename(file_).replace('.fits', '.%04d.fits' % count)
            hdu = pyfits.PrimaryHDU(red_data, header=temp_header)
            hdu.writeto(join(outdir, fname), clobber=True)

        f.close()

    print "Reduction and unpacking complete." 
