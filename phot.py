###############################################################################
# ======== PHOTOMETRY SCRIPT FOR SAAO DATA BASED ON THE SEP LIBRARY ========= #
###############################################################################

import sys; sys.path.append("/home/a/apc34/")
import fitsio
import sep
import numpy as np
import matplotlib.pyplot as plt 

from os import path
from scipy.signal import correlate2d, correlate, fftconvolve
from glob import glob 

def cross_correlation_filter(fits):
    '''Use a cross correlation with the initial image, find the peaks of the
    cross correlation function and then sigma-clip out any outlying images.
    This is a simple test to remove images with clouds, or where auto-guiding
    has failed which happens occasionally on the 1m at SAAO.'''
    #!FUNCTION IS STILL NOT WORKING. SCIPY.CORRELATE2D IS TOO SLOW TO USE 

    #Check cross-correlation for outliers
    for count, file_ in enumerate(fits): 

        #Load in reference file 
        if count == 0: ref = fitsio.read(file_)

        #Load data from image
        data = fitsio.read(file_)

        #cross-correlate them data
        cross = correlate2d(data, ref, boundary='symm', mode='same')

        from scipy.ndimage import correlate, convolve
        nd = fftconvolve(data, ref[::-1], mode='full')

        #plots
        plt.figure();plt.imshow(cross); plt.colorbar();
        plt.figure();plt.imshow(nd); plt.colorbar(); plt.show()

        #print argmax
        print np.where(cross == cross.max())
        print np.where(nd == nd.max())
        print data.shape 

        raw_input()

def init_store(flux, x, y):
    phot = {'x':x, 'y':y, 'flux':flux}
    return phot

def match_stars(x_old, y_old, x, y):
    
    #Variable to store the index of the match and corresponding distances
    star_match = np.ones(x.shape[0])*-1
    dist_match = np.zeros(x.shape[0])

    #iterate through for each new star found
    for count in range(0, x.shape[0]):
    
        #find the distance on the chip from other stars
        dist = np.sqrt((x_old - x[count])**2 + (y_old - y[count])**2)
       
        #arbitrary max pixel shift
        dist[dist > 5.0] = 10000 #set to some arbitrary high number
        ind = np.where(dist == min(dist))[0]

        #horrific logic!
        #if there is a clear match then len(ind) == 1
        if len(ind) == 1:

            #if star has two matches, pick the closest one in distance
            if ind in star_match:

                if min(dist) < dist_match[star_match == ind]:
                    star_match[star_match == ind] = np.nan
                    star_match[count] = ind
                else:
                    star_match[count] = np.nan
            else: 
                star_match[count] = ind
            
        else:
            star_match[count] = np.nan

    return star_match


def workout_offset(phot, flux, x, y):
    
    x_old = phot['x']
    y_old = phot['y']
    f_old = phot['flux']

    star_match = match_stars(x_old, y_old, x, y)

    print star_match

    #delta_x = np.array(delta_x) 
    #delta_y = np.array(delta_y) 

    #delta_x.append(x_old[ind] - x[count])
    #delta_y.append(y_old[ind] - y[count])
    #flux_weight.append(flux[count]) 
    
    #flux_weight = np.array(flux_weight) 
    #flux_weight = np.sqrt(flux_weight)
    #flux_weight /= max(flux_weight) 

    #print np.mean(delta_x), np.mean(delta_y) 
    #print np.mean(flux_weight*delta_x), np.mean(flux_weight*delta_y)

    return 0, 0

def star_loc_plot(data, count, x, y, ind):

    dmean = np.mean(data)
    dstd = np.std(data)

    fig = plt.figure()
    plt.imshow(data, vmin=dmean-1*dstd, vmax=dmean+2*dstd, cmap=plt.get_cmap('gray'))
    color_range=plt.cm.hsv(np.linspace(0,1,10))

    for i in range(0, len(x)):

        if not(np.isnan(ind[i])):
            plt.text(x[i], y[i], "%i" % ind[i], fontsize=16)#, color=color_range[int(ind[i])])
            
    plt.savefig("image%i.png" % count, bbox_inches="tight")
    plt.close('all')

def run_phot(dir_, name):

    #Final variable to store flux
    flux_store = []

    #Code for running tests on the images 
    file_dir_ = dir_ + name + '/'
    fits = sorted(glob(file_dir_ + "*.fits")) 

    print "Starting photometry for %s." % name

    #Determine the number of sources 
    for count, file_  in enumerate(fits): 
        
        #Load data from image
        data = fitsio.read(file_)     

        #Background image  
        bkg = sep.Background(data)

        #Save background image
        bkg_image = bkg.back()
        #fitsio.write(file_.replace('.fits','.fits.bkg'), bkg_image)

        #Subtract the background from data
        data_sub = data - bkg_image 

        #Extract objects    
        objects = sep.extract(data_sub, 3.0, err=bkg.globalrms)

        #Calculate flux
        flux, fluxerr, flag = sep.sum_circle(data_sub, objects['x'], objects['y'],
                                                     5.0, err=bkg.globalrms, gain=1.0)
        #store results
        if count == 0:
            phot = init_store(flux, objects['x'], objects['y']) 
            flux_store.append(flux)
        else:
            index = match_stars(phot['x'], phot['y'], objects['x'], objects['y'])
            nflux = np.zeros(phot['flux'].shape)

            #if it's not in the original image it will get ignored!!!
            for j in range(0, len(flux)): 
                if not(np.isnan(index[j])):
                    nflux[int(index[j])] = flux[j]

            
            flux_store.append(nflux)

    flux_store = np.vstack(flux_store)
    print "Completed photometry for %s." % name
    np.savetxt(path.join(dir_, name + '.dat'), flux_store)
   
'''
 
        #SOURCE DETECTION
        threshold = photutils.detect_threshold(data, snr=3.0)
        print threshold.shape

        from astropy.convolution import Gaussian2DKernel
        from astropy.stats import gaussian_fwhm_to_sigma
        from photutils import detect_sources
        
        sigma = 2.0 * gaussian_fwhm_to_sigma    # FWHM = 2.
        kernel = Gaussian2DKernel(sigma, x_size=5, y_size=5)
        kernel.normalize()

        print kernel.shape 

        segm = detect_sources(data, threshold, npixels=20, filter_kernel=kernel)

        from photutils import deblend_sources
        segm_deblend = deblend_sources(data, segm, npixels=5, filter_kernel=kernel)

        from astropy.visualization import SqrtStretch
        from astropy.visualization.mpl_normalize import ImageNormalize
        from photutils.utils import random_cmap
        
        #rand_cmap = random_cmap(segm_deblend.max + 1, random_state=12345)
        #norm = ImageNormalize(stretch=SqrtStretch())
        #fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
        #ax1.imshow(data, origin='lower', cmap='Greys_r', norm=norm)
        #ax2.imshow(segm_deblend, origin='lower', cmap=rand_cmap)

        #plt.show()
        print segm_deblend
        from photutils import source_properties, properties_table    

        props = source_properties(data, segm_deblend)
        tbl = properties_table(props)
        print(tbl)
'''

