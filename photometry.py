###############################################################################
# ======== PHOTOMETRY SCRIPT FOR SAAO DATA BASED ON THE SEP LIBRARY ========= #
###############################################################################
import fitsio
import sep
import numpy as np
import matplotlib.pyplot as plt 

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
    

if __name__ == "__main__":
    
    #Code for running tests on the images 
    fits = sorted(glob("test/*.fits")) 
       
    #Determine the number of sources 
    for count, file_  in enumerate(fits): 
        
        #Load data from image
        data = fitsio.read(file_)
                
        #Background image  
        bkg = sep.Background(data)

        #Save background image
        print bkg
        bkg_image = bkg.back()
        #fitsio.write(file_.replace('.fits','.fits.bkg'), bkg_image)

        #Subtract the background from data
        data_sub = data - bkg_image 

        #Extract objects    
        objects = sep.extract(data_sub, 3.0, err=bkg.globalrms)

        #print objects
        print objects.shape

        flux, fluxerr, flag = sep.sum_circle(data_sub, objects['x'], objects['y'],
                                                     3.0, err=bkg.globalrms, gain=1.0)

        print flux
        raw_input()
        
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

