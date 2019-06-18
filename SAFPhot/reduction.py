import numpy as np
import sys 
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

def create_calframes(files, params, verbose=False):
    '''Main function creating calibration frames'''

    print("Creating calibration frames for data.")

    #Variable for results
    calframes = {}

    #Try creating directory to hold calibration files
    outdir = join(params.out_dir, params.cal_dir) 
    if not exists(outdir): makedirs(outdir)

    #if verbose: print "Default output dir is %s" % outdir

    bias_ = join(outdir, "bias.fits") #bias file name 

    if exists(bias_):
        print("Master bias already exists, skipping creation.")
        calframes["bias"] = fitsio.read(bias_)
    else:
        #MAKE MASTER BIAS
        bias_frames = stack_fits(files.bias)
        calframes["bias"] = np.mean(bias_frames, axis=0)
        
        fitsio.write(join(outdir, "bias.fits"), calframes["bias"])
        del bias_frames
        

    if verbose: print("Bias calibration frame is %s." % bias_)
   
    #MAKE MASTER FLATS
    #prepare arrays for indexing 
    flts = set(files.flat_filter)
    filter_list = np.array(files.flat_filter, dtype=str)
    flat_list = np.array(files.flat, dtype=str)

    #FOR FLATS OF A SPECIFIC FILTER
    for flt in flts:
    
        #output directory
        flat_ = join(outdir, "flat_%s.fits" % flt).replace(' ', '_')

        if exists(flat_):
            print("Flat %s already exists, skipping creation." % flt)
            calframes[flt] = fitsio.read(flat_)

        else: 
            
            #create normalised master_flat
            flat_stack = stack_fits(flat_list[filter_list == flt])
            master_flat = np.mean(flat_stack, axis=0) - calframes["bias"]
            master_flat /= np.median(master_flat)

            fitsio.write(flat_, master_flat)
            calframes[flt] = master_flat

        if verbose: print("Flat calibration frame is %s" % flat_)

    return calframes

