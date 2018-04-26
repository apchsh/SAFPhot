###############################################################################
# ======== PHOTOMETRY SCRIPT FOR SAAO DATA BASED ON THE SEP LIBRARY ========= #
###############################################################################

import sys
import fitsio
import sep
import numpy as np
import matplotlib.pyplot as plt 

from astropy.io import fits
from astropy.table import Table
from os import path
from glob import glob
from random import uniform
from donuts import Donuts
from time import time as time_
from scipy import ndimage

def rot(image, xy, angle):
    #Rotate an imput image and set of coordinates by an angle
    im_rot = ndimage.rotate(image,angle) 
    org_center = (np.array(image.shape[:2][::-1])-1)/2.
    rot_center = (np.array(im_rot.shape[:2][::-1])-1)/2.
    xy_rot = np.empty([2, xy.shape[1]])
    for i in range(xy.shape[1]):
        org = xy[:,i]-org_center
        a = np.deg2rad(angle)
        xy_rot[:,i] = np.array([org[0]*np.cos(a) + org[1]*np.sin(a),
            -org[0]*np.sin(a) + org[1]*np.cos(a) ] + rot_center)
    return im_rot, xy_rot

def star_loc_plot(name, data, x, y, angle):

    dmean = np.mean(data)
    dstd = np.std(data)
    
    fig = plt.figure()
    data_rot, (x,y) = rot(data, np.vstack([x,y]), angle)
    plt.imshow(data_rot, vmin=dmean-1*dstd, vmax=dmean+2*dstd,
           cmap=plt.get_cmap('gray'))
    color_range=plt.cm.hsv(np.linspace(0,1,10))
   
    ind = x.shape[0]
    for i in range(0, int(ind)):
        plt.text(x[i], y[i], "%i" % i, fontsize=16)
        #, color=color_range[int(ind[i])])
            
    plt.savefig(name, bbox_inches="tight")
    plt.close('all')

def build_obj_cat(dir_, name, first, thresh, bw, fw):
    
    #Get background image  
    bkg = sep.Background(first, bw=bw, bh=bw, fw=fw, fh=fw)

    #Subtract the background
    first_sub = first - bkg.back() 

    #Extract sources to use as object catalogue
    objects = sep.extract(first_sub, thresh=thresh, err=bkg.globalrms)

    #Get the half-width radius 
    fwhm_ref, flags = sep.flux_radius(first_sub, objects['x'],
            objects['y'], np.ones(len(objects['x']))*10.0, 0.5, subpix=10)
   
    #Update the object centroid positions using sep winpos algorithm
    x_ref, y_ref, f_ref = sep.winpos(first_sub, objects['x'], 
            objects['y'], fwhm_ref*0.424, subpix=10)
    '''
    #Or alternatively just use Donuts positions without winpos refinement
    x_ref = objects['x']
    y_ref = objects['y']
    '''
    
    #Save example field image with objects numbered
    star_loc_plot(path.join(dir_, "SAAO_"+ name +'_field.png'),
            first_sub, x_ref, y_ref, 180)
    
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
   
    #Define output file name 
    output_name = path.join(dir_, "SAAO_"+ name +'_phot.fits')

    #Get science images
    file_dir_ = dir_ + name + '/'
    f_list = sorted(glob(file_dir_ + "*.fits")) 
    print ("%d frames" %len(f_list))

    #Load first image
    with fitsio.FITS(f_list[0]) as fi:
        first = fi[0][:, :]

    #Get object catalogue x and y positions
    x_ref, y_ref = build_obj_cat(dir_, name, first, thresh, 32, 3)

    
    #Define aperture positions for background flux measurement
    lim_x = first.shape[0]
    lim_y = first.shape[1]
    bapp_x = [uniform(0.05*lim_x, 0.95*lim_x) for n in range(100)]
    bapp_y = [uniform(0.05*lim_y, 0.95*lim_y) for n in range(100)]
    
    #Initialise variables to store data
    '''4D array structure: [apertures, objects, bkg_params, frames]'''
    flux_store = np.empty([radii.shape[0], len(x_ref),
        len(bsizes)*len(fsizes), len(f_list)])
    fluxerr_store = np.empty([radii.shape[0], len(x_ref),
        len(bsizes)*len(fsizes), len(f_list)])
    flag_store = np.empty([radii.shape[0], len(x_ref),
        len(bsizes)*len(fsizes), len(f_list)])
    
    '''3D array structure: [bkg_apertures, bkg_params, frames]'''
    bkg_flux_store = np.empty([len(bapp_x), len(bsizes)*len(fsizes), len(f_list)])
    
    '''2D array structure: [objects, frames]'''
    pos_store_x = np.empty([len(x_ref), len(f_list)])
    pos_store_y = np.empty([len(y_ref), len(f_list)])
    pos_store_donuts_x = np.empty([len(x_ref), len(f_list)])
    pos_store_donuts_y = np.empty([len(y_ref), len(f_list)])
    
    '''2D array structure: [bkg_params, frames]'''
    fwhm_store = np.empty([len(bsizes)*len(fsizes), len(f_list)])
    
    '''1D array structure: [frames]'''
    jd_store = np.empty([len(f_list)])
    hjd_store = np.empty([len(f_list)])
    bjd_store = np.empty([len(f_list)])
    frame_shift_x_store = np.empty([len(f_list)])
    frame_shift_y_store = np.empty([len(f_list)])
    exp_store = np.empty([len(f_list)])

    #Create Donuts object using first image as reference
    d = Donuts(
        refimage=f_list[0], image_ext=0,
        overscan_width=0, prescan_width=0,
        border=0, normalise=False,
        subtract_bkg=False)
    
    print "Starting photometry for %s." % name

    #Initialise start time for progress meter 
    meter_width=48
    start_time = time_()

    #Iterate through each reduced science image
    for count, file_  in enumerate(f_list): 
               
        #Store frame offset wrt reference image
        if count != 1:
            #Calculate offset from reference image
            shift_result = d.measure_shift(file_)
            frame_shift_x_store[count-1] = (shift_result.x).value
            frame_shift_y_store[count-1] = (shift_result.y).value
        else:
            #Frame is the reference image so now offset by definition
            frame_shift_x_store[count-1] = 0
            frame_shift_y_store[count-1] = 0

        #Create image handle
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
    
        # Store frame-only dependent times
        jd_store[count-1] = jd
        hjd_store[count-1] = hjd
        bjd_store[count-1] = bjd
        exp_store[count-1] = exp

        #Initialise count of number of bkg params gone through
        bkg_count = 0

        #Iterate through background box sizes
        for ii in bsizes:
            #iterate through filter widths
            for jj in fsizes:

                #Get background image  
                bkg = sep.Background(data, bw=ii, bh=ii, fw=jj, fh=jj)

                #Subtract the background from data
                data_sub = data - bkg.back()

                '''Extract objects at minimal detection threshold to properly
                mask stars for bkg residual measurement'''
                objects_bkg, segmap_bkg = sep.extract(data_sub, thresh=1.0, 
                        err=bkg.globalrms, segmentation_map=True)
                
                #Measure background flux residuals
                bflux, bfluxerr, bflag = sep.sum_circle(data_sub, bapp_x, bapp_y,
                            4.0, err=bkg.globalrms, mask=segmap_bkg, gain=gain)
                
                #Store background flux residuals
                bkg_flux_store[:, bkg_count, count-1] = bflux/exp
                
                '''Adjust target aperture centroid positions using Donuts output to
                allow for drift of frame compared to reference image'''
                x = x_ref - frame_shift_x_store[count-1]
                y = y_ref - frame_shift_y_store[count-1]
                    
                #Get object half width radii
                fwhm, flags = sep.flux_radius(data_sub, x, y,
                        np.ones(len(x))*10.0, 0.5, subpix=10)

                #Store the fwhm result in arcsec, taking mean over all objects
                fwhm_store[bkg_count, count-1] = (
                        np.nanmean(fwhm) * binfactor * platescale)
                
                #Update target aperture positions using winpos algorithm
                x_pos,y_pos,f = sep.winpos(data_sub, x, y,
                        fwhm*0.424, subpix=10)
                '''
                #Or alternatively trust Donuts positions without winpos
                #refinement
                x_pos = x
                y_pos = y
                '''
                
                #Store the object centroid positions 
                pos_store_x[:, count-1] = x_pos
                pos_store_y[:, count-1] = y_pos
                pos_store_donuts_x[:, count-1] = x
                pos_store_donuts_y[:, count-1] = y

                #Tile centroid x/y positions per aperture radii used
                x_rad = np.tile(x_pos, len(radii))
                y_rad = np.tile(y_pos, len(radii))
                x_rad = x_rad.reshape((len(radii), len(x_pos)))
                y_rad = y_rad.reshape((len(radii), len(y_pos)))

                #Tile list of aperture radii per object in catalogue and transpose
                rad = [] 
                for z  in range(0, len(x_ref)):
                    rad.append(radii)
                rad = np.asarray(rad).transpose()
                
                #Measure number of counts
                flux, fluxerr, flag = sep.sum_circle(data_sub, x_rad, y_rad,
                    rad, err=bkg.globalrms, gain=gain)
                
                #Store flux, flux err and flags
                flux_store[:, :, bkg_count, count-1] = flux/exp
                fluxerr_store[:, :, bkg_count, count-1] = fluxerr/exp
                flag_store[:, :, bkg_count, count-1] = flag

                #Increment count of bkg_params gone through
                bkg_count += 1
    
        #Show progress meter for number of frames processed
        n_steps = len(f_list)
        nn = int((meter_width+1) * float(count) / n_steps)
        delta_t = time_()-start_time # time to do float(count) / n_steps % of caluculation
        time_incr = delta_t/(float(count+1) / n_steps) # seconds per increment
        time_left = time_incr*(1- float(count) / n_steps)
        m, s = divmod(time_left, 60)
        h, m = divmod(m, 60)
        sys.stdout.write("\r[{0}{1}] {2:5.1f}% - {3:02}h:{4:02}m:{05:.2f}s".
             format('#' * nn, ' ' * (meter_width - nn), 100*float(count)/n_steps,h,m,s))
   
    #Save data to file
    #Need to think abour using headers to define the dimensions
    #TableHDU might not be what we want
    pri = fits.PrimaryHDU(n)
    flux = fits.TableHDU(flux_store, header=None, name="flux")
    fluxerr = fits.TableHDU(fluxerr_store, header=None, name="fluxerr")
    flags = fits.TableHDU(flag_store, header=None, name="flags")
    bkgflux = fits.TableHDU(bkg_flux_store, header=None, name="bkgflux")
    hdulist = fits.fits.HDUList([pri, flux, fluxerr, flags, bkgflux])
    hdulist.writeto('output_name')

    print "\nCompleted photometry for %s." % name
