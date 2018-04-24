###############################################################################
# ======== PHOTOMETRY SCRIPT FOR SAAO DATA BASED ON THE SEP LIBRARY ========= #
###############################################################################

import sys
import fitsio
import sep
import numpy as np
import matplotlib.pyplot as plt 

from scipy.io import savemat, loadmat
from os import path
from scipy.signal import correlate2d, correlate, fftconvolve
from glob import glob
from random import uniform
from donuts import Donuts
from time import time as time_

def star_loc_plot(name, data, x, y):

    dmean = np.mean(data)
    dstd = np.std(data)

    fig = plt.figure()
    plt.imshow(data, vmin=dmean-1*dstd, vmax=dmean+2*dstd, cmap=plt.get_cmap('gray'))
    color_range=plt.cm.hsv(np.linspace(0,1,10))
    
    ind = x.shape[1]

    for i in range(0, int(ind)):
        plt.text(x[0,i], y[0,i], "%i" % i, fontsize=16)#, color=color_range[int(ind[i])])
            
    plt.savefig(name, bbox_inches="tight")
    plt.close('all')

def build_obj_cat(first, thresh, bw, fw):
    
    #Get background image  
    bkg = sep.Background(first, bw=bw, bh=bw, fw=fw, fh=fw)

    #Subtract the background
    first_sub = first - bkg.back() 

    #Extract sources to use as object catalogue
    objects = sep.extract(first_sub, thresh=thresh, 
            err=bkg.globalrms)

    #Get the half-width radius 
    fwhm_ref, flags = sep.flux_radius(first_sub, objects['x'],
            objects['y'], np.ones(len(objects['x']))*10.0, 0.5,
            subpix=10)
   
    #Update the object centroid positions using sep winpos algorithm
    x_ref, y_ref, f_ref = sep.winpos(first_sub, objects['x'], 
            objects['y'], fwhm_ref*0.424, subpix=10)
    '''
    #Or alternatively just use Donuts positions without winpos refinement
    x_ref = objects['x']
    y_ref = objects['y']
    '''
    
    return x_ref, y_ref

def run_phot(dir_, name):

    #Define background box sizes to use
    bsizes = [16, 32, 64]

    #Define background filter widths to use
    fsizes = range(5)

    #Define aperture radii to use
    radii = np.arange(2.0, 6.0, 0.1)

    #Define platescale for seeing calculation
    platescale = 0.167 #arcsec / pix
    
    #Define source detection threshold
    thresh = 7.0
    
    #Get science images
    file_dir_ = dir_ + name + '/'
    fits = sorted(glob(file_dir_ + "*.fits")) 
    print ("%d frames" %len(fits))

    #Load first image
    with fitsio.FITS(fits[0]) as fi:
        first = fi[0][:, :]

    #Get object catalogue x and y positions
    x_ref, y_ref = build_obj_cat(first, thresh, 32, 3)

    #Tile list of aperture radii per object in catalogue
    rad = [] 
    for z  in range(0, len(x_ref)):
        rad.append(radii)
    
    #Define aperture positions for background flux measurement
    lim_x = first.shape[0]
    lim_y = first.shape[1]
    bapp_x = [uniform(0.05*lim_x, 0.95*lim_x) for n in range(100)]
    bapp_y = [uniform(0.05*lim_y, 0.95*lim_y) for n in range(100)]
    
    #Initialise variables to store data
    '''4D array structure: [apertures, objects, bkg_params, frames]'''
    flux_store = np.empty([radii.shape[0], len(x_ref), bsizes*fsizes, len(fits)])
    fluxerr_store = np.empty([radii.shape[0], len(x_ref), bsizes*fsizes, len(fits)])
    
    '''3D array structure: [bkg_apertures, bkg_params, frames]'''
    bkg_flux_store = np.empty([len(bapp_x), bsizes*fsizes, len(fits)])
    
    '''2D array structure: [objects, frames]'''
    pos_store = np.empty([len(x_ref), len(fits)])
    
    '''1D array structure: [frames]'''
    jd_store = np.empty([len(fits)])
    hjd_store = np.empty([len(fits)])
    bjd_store = np.empty([len(fits)])
    fwhm_store = np.empty([len(fits)])
    frame_shift_store = np.empty([len(fits)])

    #Create Donuts object using first image as reference
    d = Donuts(
        refimage=fits[0], image_ext=0,
        overscan_width=0, prescan_width=0,
        border=0, normalise=False,
        subtract_bkg=False)
    
    print "Starting photometry for %s." % name

    '''Initialise count of number of images processed, incremented for each bkg
    parameter combination'''
    count2 = 0

    #Initialise start time for progress meter 
    meter_width=48
    start_time = time_()

    #Iterate through each reduced science image
    for count, file_  in enumerate(fits): 
               
        #Store frame offset wrt ref image
        if count != 1:
            #Calculate offset from reference image
            shift_result = d.measure_shift(file_)
            frame_shift_store[count-1] = [(shift_result.x).value, (shift_result.y).value]
        else:
            frame_shift_store[count-1] = [0,0]

        #Load image
        with fitsio.FITS(file_) as f:
            
            #Load tabular data from image
            data = f[0][:, :]
            
            #Load header data from image
            jd = f[0].read_header()["JD"]
            try:
                hjd = f[0].read_header()["HJD"]
            except:
                hjd = np.nan
            try:
                bjd = f[0].read_header()["BJD"]
            except:
                bjd = np.nan
            exp = f[0].read_header()["EXPOSURE"]
            gain = f[0].read_header()['PREAMP']
            binfactor = f[0].read_header()['VBIN']
    
        #Iterate through background box sizes
        for ii in bsizes:
            #iterate through filter widths
            for jj in fsizes:

                #Background image  
                bkg = sep.Background(data, bw=ii, bh=ii, fw=jj, fh=jj)

                #Save background image
                bkg_image = bkg.back()

                #Subtract the background from data
                data_sub = data - bkg_image 

                '''Extract objects at minimal threshold to properly mask stars
                for bkg residual measurement'''
                objects_bkg, segmap_bkg = sep.extract(data_sub, thresh=1.0, 
                        err=bkg.globalrms, segmentation_map=True)
                
                #Measure background flux
                bflux, bfluxerr, bflag = sep.sum_circle(data_sub, bapp_x, bapp_y,
                            4.0, err=bkg.globalrms, mask=segmap_bkg, gain=gain)
                
                ####### UP TO HERE ##########
                #############################
                #############################

                #Store background flux
                bkg_flux_store.append(bflux/exp)
                
                if count2 == 0:
                    #Extract objects to use as catalogue, normal thresh=9.0
                    objects, segmap = sep.extract(data_sub, thresh=thresh,
                            err=bkg.globalrms, segmentation_map=True)


                    #Accurate x and y already know so no kneed to refine as is
                    #done for subsequent frames
                    x_pos = x_ref
                    y_pos = y_ref
    
                    #Store the fwhm result 
                    fwhm_store.append(np.nanmean(fwhm_ref))
                
                else:
                    #Adjust centroid positions using Donuts output to allow for
                    # drift of frame compared to reference image
                    x = x_ref - (shift_result.x).value
                    y = y_ref - (shift_result.y).value
                    
                    #Get the half width radius 
                    fwhm, flags = sep.flux_radius(data_sub, x, y,
                            np.ones(len(x))*10.0, 0.5, subpix=10)

                    #Store the fwhm result 
                    fwhm_store.append(np.nanmean(fwhm))
                    
                    #Update the object centroid positions using sep winpos algorithm
                    x_pos,y_pos,f = sep.winpos(data_sub, x, y,
                            fwhm*0.424, subpix=10)
                    
                    '''
                    #Or alternatively trust the Donuts positions
                    x_pos = x
                    y_pos = y
                    '''
                
                #Store the centroid positions 
                pos_store.append((x_ref,y_ref))

                #Tile centroid x/y positions to match num radii
                x_rad = np.tile(x_pos, len(radii))
                y_rad = np.tile(y_pos, len(radii))
                x_rad = x_rad.reshape((len(radii), len(x_pos)))
                y_rad = y_rad.reshape((len(radii), len(y_pos)))

                #Create array of radii and transpose
                radii = np.array(rad)
                radii = radii.transpose()
                
                #Measure number of counts
                flux, fluxerr, flag = sep.sum_circle(data_sub, x_rad, y_rad,
                    radii, err=bkg.globalrms, gain=gain)

                #store results
                flux_store.append(flux/exp) #correct the counts for exposure time
                fluxerr_store.append(fluxerr/exp)
                jd_store.append(jd)
                hjd_store.append(hjd)
                bjd_store.append(bjd)
                if (ii == 32 and jj == 3 and count == 1) :
                    star_loc_plot(path.join(dir_, "SAAO_"+ name +'_field.png'),
                            data_sub, x_rad, y_rad)

                count2 += 1
    
        #Progress meter
        nn = int((meter_width+1) * float(count) / n_steps)
        delta_t = time_()-start_time # time to do float(count) / n_steps % of caluculation
        time_incr = delta_t/(float(count+1) / n_steps) # seconds per increment
        time_left = time_incr*(1- float(count) / n_steps)
        m, s = divmod(time_left, 60)
        h, m = divmod(m, 60)
        sys.stdout.write("\r[{0}{1}] {2:5.1f}% - {3:02}h:{4:02}m:{05:.2f}s".
             format('#' * nn, ' ' * (meter_width - nn), 100*float(count)/n_steps,h,m,s))
    
    #Stack flux frames and store
    flux_store = np.dstack(flux_store)
    fluxerr_store = np.dstack(fluxerr_store)
    
    #Reshape flux so bkg params is a new axis
    flux_store = flux_store.reshape(flux_store.shape[0], flux_store.shape[1],
            flux_store.shape[2]/(len(bsizes)*len(fsizes)), len(bsizes)*len(fsizes))
    fluxerr_store = fluxerr_store.reshape(fluxerr_store.shape[0], fluxerr_store.shape[1],
            fluxerr_store.shape[2]/(len(bsizes)*len(fsizes)), len(bsizes)*len(fsizes))

    #Swap axes for bkg params and frame number
    flux_store = np.swapaxes(flux_store, 2, 3)
    fluxerr_store = np.swapaxes(fluxerr_store, 2, 3)

    print flux_store.shape
    
    #Stack lists to form arrays
    bkg_flux_store = np.vstack(bkg_flux_store)
    jd_store = np.vstack(jd_store)
    hjd_store = np.vstack(hjd_store)
    bjd_store = np.vstack(bjd_store)
    fwhm_store = np.hstack(fwhm_store)
    pos_store = np.hstack(pos_store)
    frame_shift_store = np.vstack(frame_shift_store)
    
    #Save flux and fluxerr to Matlab file in 4D format
    savemat(path.join(dir_, "SAAO_"+ name + '_obj_flux'), 
            mdict={'flux': flux_store}, oned_as='row')
    load_back = loadmat(path.join(dir_, "SAAO_"+ name + '_obj_flux'))
    assert np.all(flux_store == load_back['flux'])
    savemat(path.join(dir_, "SAAO_"+ name + '_obj_flux_err'), 
            mdict={'fluxerr': fluxerr_store}, oned_as='row')

    #Remove duplicate jd entries due to background parameter sampling loops
    jd_store = jd_store.reshape((jd_store.shape[0]/flux_store.shape[2], 
        flux_store.shape[2]))
    jd_store = jd_store[:, 0]
    hjd_store = hjd_store.reshape((hjd_store.shape[0]/flux_store.shape[2], 
        flux_store.shape[2]))
    hjd_store = hjd_store[:, 0]
    bjd_store = bjd_store.reshape((bjd_store.shape[0]/flux_store.shape[2], 
        flux_store.shape[2]))
    bjd_store = bjd_store[:, 0]

    #Reshape fwhm_store so format is [bkg params, frames]
    fwhm_store = fwhm_store.reshape(fwhm_store.shape[0]/len(bsizes)/len(fsizes),
            len(bsizes)*len(fsizes))
    fwhm_store = np.swapaxes(fwhm_store, 0, 1)

    #Multiple fwhm by binning factor and plate scale to get seeing in arcsec
    fwhm_store *= binfactor * platescale

    #Reshape pos_store so format is [x/y, obj, bkg, frames]
    numobjs = len(objects['x'])
    pos_store = pos_store.reshape(pos_store.shape[0],
            pos_store.shape[1]/numobjs/len(bsizes)/len(fsizes), 
            len(bsizes)*len(fsizes), numobjs)
    # format currently [x/y, frames, bkg, objs], swap 2 axes for desired format
    pos_store = np.swapaxes(pos_store, 1, 3)
    #Save centroid positions as matlab file to preserve ndim format
    savemat(path.join(dir_, "SAAO_"+name + '_centroid_pos'),
            mdict={'centroid_pos': pos_store}, oned_as='row')

    # Swap axes for frame_shift_store so format is [x/y, frames]
    frame_shift_store = np.swapaxes(frame_shift_store, 0, 1)

    #Save other 1D and 2D arrays to files
    np.savetxt(path.join(dir_, "SAAO_"+name + '_jd.dat'), jd_store)
    np.savetxt(path.join(dir_, "SAAO_"+name + '_hjd.dat'), hjd_store)
    np.savetxt(path.join(dir_, "SAAO_"+name + '_bjd.dat'), bjd_store)
    np.savetxt(path.join(dir_, "SAAO_"+name + '_bkg_flux.dat'), bkg_flux_store)
    np.savetxt(path.join(dir_, "SAAO_"+name + '_fwhm.dat'), fwhm_store)
    np.savetxt(path.join(dir_, "SAAO_"+name + '_frame_shift.dat'), frame_shift_store)
    
    print "Completed photometry for %s." % name
