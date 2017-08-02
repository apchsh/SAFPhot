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

def star_loc_plot(name, data, x, y, ind):

    dmean = np.mean(data)
    dstd = np.std(data)

    fig = plt.figure()
    plt.imshow(data, vmin=dmean-1*dstd, vmax=dmean+2*dstd, cmap=plt.get_cmap('gray'))
    color_range=plt.cm.hsv(np.linspace(0,1,10))

    for i in range(0, len(x)):

        if not(np.isnan(ind[i])):
            plt.text(x[i], y[i], "%i" % ind[i], fontsize=16)#, color=color_range[int(ind[i])])
            
    plt.savefig(name, bbox_inches="tight")
    plt.close('all')

def run_phot(dir_, name):

    #Final variable to store flux
    flux_store = []
    jd_store = [] 
	pos_store = []
	fwhm_store = [] 

    #Code for running tests on the images 
    file_dir_ = dir_ + name + '/'
    fits = sorted(glob(file_dir_ + "*.fits")) 

    print "Starting photometry for %s." % name

    #Determine the number of sources 
    for count, file_  in enumerate(fits): 
        
        #Load data from image
        f = fitsio.FITS(file_)
        data = f[0][:, :]
        jd = f[0].read_header()["JD"]
        exp = f[0].read_header()["EXPOSURE"]
        f.close() 

        #Background image  
        bkg = sep.Background(data)

        #Save background image
        bkg_image = bkg.back()
        #fitsio.write(file_.replace('.fits','.fits.bkg'), bkg_image)

        #Subtract the background from data
        data_sub = data - bkg_image 

        #Extract objects    
        objects = sep.extract(data_sub, 4.0, err=bkg.globalrms)


		#Get the half width radius 
		fwhm, flags = flux_radius(data_sub, objects['x'], objects['y'], 10.0, 0.5, subpix=0)

		#find the mean fwhm
		mean_fwhm = np.nanmean(fwhm); fwhm_store.append(fwhm)

		#Update the positions using sep winpos algorithm
		x, y = sep.winpos(data_sub, objects['x'], objects['y'], mean_fwhm*0.424, subpix=0)
		pos_store.append((x,y))

        #Calculate flux
        flux, fluxerr, flag = sep.sum_circle(data_sub, x, y,
                                                     mean_fwhm*2, err=bkg.globalrms, gain=1.0)
        #store results
        if count == 0:
            phot = init_store(flux, x, y) 
            flux_store.append(flux/exp) #correct the counts for exposure time           
            jd_store.append(jd)
        else:
            index = match_stars(phot['x'], phot['y'], x, y)
            nflux = np.zeros(phot['flux'].shape)

            #if it's not in the original image it will get ignored!!!
            for j in range(0, len(flux)): 
                if not(np.isnan(index[j])):
                    nflux[int(index[j])] = flux[j]

            
            flux_store.append(nflux/exp) #correct the counts for exposure time
            jd_store.append(jd)

            if count == 1:
                star_loc_plot(path.join(dir_, name +'.png'), data_sub, objects['x'], objects['y'], index)

    flux_store = np.vstack(flux_store)
    jd_store = np.vstack(jd_store)
	fwhm_store = np.vstack(fwhm_store) #haven't tested this works
	pos_store = np.vstack(pos_store) #haven't test this either! 
	
    print "Completed photometry for %s." % name
    np.savetxt(path.join(dir_, name + '.dat'), flux_store)
    np.savetxt(path.join(dir_, name + '_jd.dat'), jd_store)
	np.savetxt(path.join(dir_, name + '_pos.dat'), pos_store)
	np.savetxt(path.join(dir_, name + '_fwhm.dat'), fwhm_store)


