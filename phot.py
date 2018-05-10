import sys
import fitsio
import sep
import numpy as np
import matplotlib.pyplot as plt 

from astropy.table import Table
from astropy import coordinates as coord
from os.path import join, exists
from os import makedirs
from glob import glob
from random import uniform
from donuts import Donuts
from time import time as time_
from scipy import ndimage
from copy import copy
from unpack import convert_jd_hjd, convert_jd_bjd, Mapper # SAFPhot script
from photsort import get_all_files # SAFPhot script

def makeheader(m):
    #Make general header for each HDU
    (dateobs_com, observer_com, analyser_com, observatory_com, telescope_com,
    instrument_com, filtera_com, filterb_com, platescale_com, target_com, ra_com,
    dec_com, epoch_com, equinox_com) = (None, None, None, None, None, None, None,
    None, None, None, None, None, None, None)
    
    if hasattr(m, 'dateobs_com'): datecoms_com = m.dateobs_com
    else: dateobs_com = 'Start date and local start time of observations'
    if hasattr(m, 'observer_com'): observer_com = m.observer
    else: observer_com = 'Observer who acquired the data'
    if hasattr(m, 'analyser_com'): analyser_com = m.analyser_com
    else: analyser_com = 'Person who analysed the data'
    if hasattr(m, 'observatory_com'): observatory_com = m.observatory_com
    else: observatory_com = 'Observatory'
    if hasattr(m, 'telescope_com'): telescope_com = m.telescope_com
    else: telescope_com = 'Telescope'
    if hasattr(m, 'instrument_com'): instrument_com = m.instrument_com
    else: instrument_com = 'Instrument'
    if hasattr(m, 'filtera_com'): filtera_com = m.filtera_com
    else: filtera_com = 'The active filter in wheel A'
    if hasattr(m, 'filterb_com'): filterb_com = m.filterb_com
    else: filterb_com = 'The active filter in wheel B'
    if hasattr(m, 'platescale_com'): platescale_com = m.platescale_com
    else: platescale_com = 'Platescale [arcsec/pixel]'
    if hasattr(m, 'target_com'): target_com = m.target_com
    else: target_com = 'Target object'
    if hasattr(m, 'ra_com'): ra_com = m.ra_com
    else: ra_com = 'RA of target object'
    if hasattr(m, 'dec_com'): dec_com = m.dec_com
    else: dec_com = 'DEC of target object'
    if hasattr(m, 'epoch_com'): epoch_com = m.epoch_com
    else: epoch_com = 'Target object coordinate epoch'
    if hasattr(m, 'hequinox_com'): equinox_com = m.equinox_com
    else: equinox_com = 'Target object coordinate equinox'

    hlist = [{'name':'DATE-OBS', 'value':m.dateobs,
                    'comment':dateobs_com},
            {'name':'OBSERVER', 'value':m.observer,
                    'comment':observer_com},
            {'name':'ANALYSER', 'value':m.analyser,
                    'comment':analyser_com},
            {'name':'OBSERVAT', 'value':m.observatory,
                    'comment':observatory_com},
            {'name':'TELESCOP', 'value':m.telescope,
                    'comment':telescope_com},
            {'name':'INSTRUMT', 'value':m.instrument,
                    'comment':instrument_com},
            {'name':'FILTERA', 'value':m.filtera,
                    'comment':filtera_com},
            {'name':'FILTERB', 'value':m.filterb,
                    'comment':filterb_com},
            {'name':'PLATESCL', 'value':m.platescale,
                    'comment':platescale_com},
            {'name':'TARGET', 'value':m.target, 'comment':target_com},
            {'name':'RA', 'value':m.ra, 'comment':ra_com},
            {'name':'DEC', 'value':m.dec, 'comment':dec_com},
            {'name':'EPOCH', 'value':m.epoch,
                    'comment':epoch_com},
            {'name':'EQUINOX', 'value':m.equinox,
                    'comment':equinox_com}
            ]
    return hlist

def append_header(h, vars_):
    #Reverse dimension order to be consistent with FITS format
    h_ = copy(h)
    vars_.reverse()
    #Add keyword for each dimension
    for i in range(len(vars_)):
        h_.append({'name':'VARAXIS' + str(i+1), 'value':vars_[i],
                'comment':'variable of data axis %s' %(i+1)})
    return h_

def rot(image, xy, angle):
    #Rotate an input image and set of coordinates by an angle
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

def build_obj_cat(dir_, prefix, name, first, thresh, bw, fw, angle):
    
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
    star_loc_plot(join(dir_, prefix + name +'_field.png'),
            first_sub, x_ref, y_ref, angle)
    
    return x_ref, y_ref
               
def run_phot(dir_, pattern, p, name):

    #Define background box sizes to use
    bsizes = np.array(p.box_size)

    #Define background filter widths to use
    fsizes = np.array(p.filter_size)

    #Define aperture radii to use for flux measurements
    radii = np.array(p.radii)

    #Define num apertures and radius to use for bkg residuals
    bkg_rad = p.bkg_app_rad
    nbapps = p.num_bkg_apps

    #Define source detection threshold
    thresh = p.source_thresh
   
    #Define rotation angle for field image
    field_angle = p.field_angle

    #Define output directory and file name 
    if p.out_dir is "":
        p.out_dir = dir_
    out_dir = join(p.out_dir, p.phot_dir)
    output_name = join(out_dir, p.phot_prefix + name +'_phot.fits')

    '''END OF DEFINITIONS'''

    #Try creating directory to hold photometry files
    if not exists(out_dir): makedirs(out_dir)

    #Get science images
    file_dir_ = join(dir_, p.red_dir, name, "")
    f_list = get_all_files(file_dir_, extension=pattern+"*.fits")
    assert (len(f_list) > 0), "No photometry files found!"
    print ("%d frames" %len(f_list))

    #Load first image
    with fitsio.FITS(f_list[0]) as fi:
        first = fi[0][:, :]
        firsthdr = fi[0].read_header()

    #Try and map parameters to header keywords otherwise set the keyword
    keylist = {'dateobs', 'observer', 'analyser', 'observatory', 'telescope',
            'instrument', 'filtera', 'filterb', 'target', 'ra', 'dec', 'epoch',
            'equinox', 'platescale', 'lon', 'lat', 'alt', 'hbin', 'vbin',
            'preamp'}
    m = Mapper(firsthdr, p, keylist)

    #Get output file general header
    hdr = makeheader(m)

    #Get object catalogue x and y positions
    x_ref, y_ref = build_obj_cat(out_dir, p.phot_prefix, name, first, 
            thresh, 32, 3, field_angle)

    #Define aperture positions for background flux measurement
    lim_x = first.shape[0]
    lim_y = first.shape[1]
    bapp_x = [uniform(0.05*lim_x, 0.95*lim_x) for n in range(nbapps)]
    bapp_y = [uniform(0.05*lim_y, 0.95*lim_y) for n in range(nbapps)]
    
    #Initialise variables to store data
    struct_4D_flux = ['apertures', 'objects', 'bkgrnd params', 'frames']
    header_4D_flux = append_header(hdr, struct_4D_flux)
    flux_store = np.empty([radii.shape[0], len(x_ref),
        len(bsizes)*len(fsizes), len(f_list)])
    fluxerr_store = np.empty([radii.shape[0], len(x_ref),
        len(bsizes)*len(fsizes), len(f_list)])
    flag_store = np.empty([radii.shape[0], len(x_ref),
        len(bsizes)*len(fsizes), len(f_list)])
    bkg_app_flux_store = np.empty([radii.shape[0], len(x_ref),
        len(bsizes)*len(fsizes), len(f_list)])
    bkg_app_fluxerr_store = np.empty([radii.shape[0], len(x_ref),
        len(bsizes)*len(fsizes), len(f_list)])
    
    struct_3D_flux = ['bkgrnd apertures', 'bkgrnd params', 'frames']
    header_3D_flux = append_header(hdr, struct_3D_flux)
    bkg_flux_store = np.empty([len(bapp_x), len(bsizes)*len(fsizes),
        len(f_list)])
    
    struct_2D_pos = ['objects', 'frames']
    header_2D_pos = append_header(hdr, struct_2D_pos)
    pos_store_x = np.empty([len(x_ref), len(f_list)])
    pos_store_y = np.empty([len(y_ref), len(f_list)])
    pos_store_donuts_x = np.empty([len(x_ref), len(f_list)])
    pos_store_donuts_y = np.empty([len(y_ref), len(f_list)])
    
    struct_2D_fwhm = ['bkgrnd params', 'frames']
    header_2D_fwhm = append_header(hdr, struct_2D_fwhm)
    fwhm_store = np.empty([len(bsizes)*len(fsizes), len(f_list)])
    
    struct_1D_frames = ['frames']
    header_1D_frames = append_header(hdr, struct_1D_frames)
    jd_store = np.empty([len(f_list)])
    hjd_store = np.empty([len(f_list)])
    bjd_store = np.empty([len(f_list)])
    frame_shift_x_store = np.empty([len(f_list)])
    frame_shift_y_store = np.empty([len(f_list)])
    exp_store = np.empty([len(f_list)])
    airmass_store = np.empty([len(f_list)])

    #Create variable to log bkg param combinations iterating through 
    dt = np.dtype([('bkg_parameter_combo', 'S10')])
    bkg_params = np.empty(bsizes.shape[0]*fsizes.shape[0], dtype=dt)
    struct_bkg_params = ['box size (pix), filter width (box)']
    header_bkg_params = append_header(hdr, struct_bkg_params)
    counter = 0
    for i in bsizes:
        for j in fsizes:
            bkg_params[counter] = str(i)+','+str(j)
            counter += 1

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
            #Frame is the reference image so no offset by definition
            frame_shift_x_store[count-1] = 0
            frame_shift_y_store[count-1] = 0

        #Create image handle
        with fitsio.FITS(file_) as f:
            
            #Load tabular data from image
            data = f[0][:, :]
            header = f[0].read_header()

            #Set frame dependent variables
            exp = header[p.exposure] # existence compulsory
            jd = header[p.jd] # existence compulsory
            binfactor = 1.0

            try:
                binfactor = float(m.hbin)
            except:
                try:
                    binfactor = float(m.vbin)
                except:
                    pass
            #Store frame dependent variables
            exp_store[count-1] = exp
            jd_store[count-1] = jd
            try:
                hjd_store[count-1] = header[p.hjd]
            except:
                if all(v is not None for v in [m.lon, m.lat, m.alt]):
                    hjd_store[count-1] = convert_jd_hjd(
                            jd, m.ra, m.dec, coord.EarthLocation.from_geodetic(
                                m.lon, m.lat, m.alt)) 
                else:
                    hjd_store[count-1] = np.nan
            try:
                bjd_store[count-1] = header[p.bjd]
            except:
                if all(v is not None for v in [m.lon, m.lat, m.alt]):
                    bjd_store[count-1] = convert_jd_bjd(
                            jd, m.ra, m.dec, coord.EarthLocation.from_geodetic(
                                m.lon, m.lat, m.alt)) 
                else:
                    bjd_store[count-1] = np.nan
            try:
                airmass_store[count-1] = header[p.airmass]
            except:
                airmass_store[count-1] = np.nan

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
                            bkg_rad, err=bkg.globalrms, mask=segmap_bkg,
                            gain=m.preamp)
                
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
                        np.nanmean(fwhm) * binfactor * m.platescale)
                
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
                
                #Measure number of counts in target aperture
                flux, fluxerr, flag = sep.sum_circle(data_sub, x_rad, y_rad,
                    rad, err=bkg.globalrms, gain=m.preamp)
                
                #Measure num counts subtracted as bkg in same aperture
                bflux_app, bfluxerr_app, bflag_app = sep.sum_circle(
                        bkg.back(), x_rad, y_rad, rad, err=bkg.globalrms,
                        gain=m.preamp)

                #Store flux, flux err and flags for target apertures
                flux_store[:, :, bkg_count, count-1] = flux/exp
                fluxerr_store[:, :, bkg_count, count-1] = fluxerr/exp
                flag_store[:, :, bkg_count, count-1] = flag

                #Store flux, flux err and flags for bkg in same apertures
                bkg_app_flux_store[:, :, bkg_count, count-1] = bflux_app/exp
                bkg_app_fluxerr_store[:, :, bkg_count, count-1] = bfluxerr_app/exp
                
                #Increment count of bkg_params gone through
                bkg_count += 1
    
        #Show progress meter for number of frames processed
        n_steps = len(f_list)
        nn = int((meter_width+1) * float(count) / n_steps)
        delta_t = time_()-start_time # time to do float(count) / n_steps % of caluculation
        time_incr = delta_t/(float(count+1) / n_steps) # seconds per increment
        time_left = time_incr*(1- float(count) / n_steps)
        mins, s = divmod(time_left, 60)
        h, mins = divmod(mins, 60)
        sys.stdout.write("\r[{0}{1}] {2:5.1f}% - {3:02}h:{4:02}m:{05:.2f}s".
             format('#' * nn, ' ' * (meter_width - nn),
                 100*float(count)/n_steps,h,mins,s))
  
    #Save each data array as a HDU in FITS file
    with fitsio.FITS(output_name, "rw", clobber=True) as g:
        g.write(flux_store, header=header_4D_flux, extname="OBJ_FLUX")
        g.write(fluxerr_store, header=header_4D_flux, extname="OBJ_FLUX_ERR")
        g.write(flag_store, header=header_4D_flux, extname="OBJ_FLUX_FLAGS")
        g.write(bkg_app_flux_store, header=header_4D_flux, extname="OBJ_BKG_APP_FLUX")
        g.write(bkg_app_fluxerr_store, header=header_4D_flux,
                extname="OBJ_BKG_APP_FLUX_ERR")
        g.write(bkg_flux_store, header=header_3D_flux, extname="RESIDUAL_BKG_FLUX")
        g.write(pos_store_x, header=header_2D_pos, extname="OBJ_CCD_X")
        g.write(pos_store_y, header=header_2D_pos, extname="OBJ_CCD_Y")
        g.write(pos_store_donuts_x, header=header_2D_pos, extname="OBJ_CCD_X_UNREFINED")
        g.write(pos_store_donuts_y, header=header_2D_pos, extname="OBJ_CCD_Y_UNREFINED")
        g.write(fwhm_store, header=header_2D_fwhm, extname="MEAN_OBJ_FWHM")
        g.write(jd_store, header=header_1D_frames, extname="JD")
        g.write(hjd_store, header=header_1D_frames, extname="HJD_utc")
        g.write(bjd_store, header=header_1D_frames, extname="BJD_tdb")
        g.write(frame_shift_x_store, header=header_1D_frames, extname="FRAME_SHIFT_X")
        g.write(frame_shift_y_store, header=header_1D_frames, extname="FRAME_SHIFT_Y")
        g.write(exp_store, header=header_1D_frames, extname="EXPOSURE_TIME")
        g.write(airmass_store, header=header_1D_frames, extname="AIRMASS")
        g.write(radii, header=hdr, extname="VARIABLES_APERTURE_RADII")
        g.write(bkg_params, header=header_bkg_params, extname="VARIABLES_BKG_PARAMS")

    print "\nCompleted photometry for %s." % name
