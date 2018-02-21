import numpy as np
import sys; 
#sys.path.append("/home/a/apc34/")
import fitsio

from astropy.io import fits
from os.path import join, exists
from os import makedirs

def combine_calframes(data, chunk_size=150): 
    '''Function is here just in case we start using too many files to fit into
    memory. Currently is serves no major purpose...'''

    if data.shape[0] < chunk_size:
        cal_mean = np.mean(data, axis=0) 
    else:
        #the mean of the mean is a good estimate for the mean
        chunk = []
        for count in range(0, data.shape[0], chunk_size):
            chunk.append(np.mean(data[count:count+chunk_size, :, :], axis=0))
            
        chunks = np.dstack(chunk)
        cal_mean = np.mean(chunks, axis=2)

    return cal_mean

def stack_fits(flat_list):
    '''Create a 3D numpy array of flats for a particular filter or bias frames'''
    stack = []

    for file_ in flat_list:
        calframe = fitsio.read(file_)
        stack.append(calframe) 

    return np.concatenate(stack, axis=0) 


def reduce_sci(files, bias, flat, verbose=False):
    '''Function with which to reduce the science images'''

    bias = fitsio.read(biasl)
    flat = fitsio.read(flatl) 

    for file_ in files:
        f = fits.open(file_)
        f[0].data = (f[0].data - bias)/flat
        f.writeto(file_.replace('SH', 'rSH')) 
        if verbose: print file_ + " done." 

def create_calframes(files, verbose=False):
    '''Main function creating calibration frames'''

    print "Creating calibration frames for data." 

    #Variable for results
    calframes = {}

    #Try creating directory to hold calibration files
    outdir = join(files.dir_, "calframes/") 
    if not exists(outdir): makedirs(outdir)

    if verbose: print "Default output dir is %s" % outdir

    #MAKE MASTER BIAS
    bias_frames = stack_fits(files.bias)
    bias_mean = np.mean(bias_frames, axis=0)
    fitsio.write(join(outdir, "bias.fits"), bias_mean)

    #print bias_frames.shape
    print bias_mean.shape

    if verbose: print "Bias calibration frame saved to %s (%i exposures)." % (join(outdir,
    "bias.fits"), bias_frames.shape[0] )  

    #delete the bias_frames variable to free up space in case
    del bias_frames
    calframes["bias"] = bias_mean

    
    #MAKE MASTER FLATS
    #prepare arrays for indexing 
    flts = set(files.flat_filter)
    filter_list = np.array(files.flat_filter, dtype=str)
    flat_list = np.array(files.flat, dtype=str)

    #FOR FLATS OF A SPECIFIC FILTER
    for flt in flts:
    
        #output directory
        flat_out = join(outdir, "flat_%s.fits" % flt).replace(' ', '_')

        #create normalised master_flat
        flat_stack = stack_fits(flat_list[filter_list == flt])
        master_flat = np.mean(flat_stack, axis=0) - bias_mean 
        master_flat /= np.median(master_flat)

        fitsio.write(flat_out, master_flat)
        calframes[flt] = master_flat

        if verbose: print "Normalised flat calibration frame saved to %s (%i \
        exposures)" % (flat_out, flat_stack.shape[0])

    return calframes

