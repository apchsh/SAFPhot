#!/usr/bin/env python

'''
Script to perform differential photometry on SAFPhot output data. Utilises
parameters define in params.py

Mandatory: 
        - Input directory: path to photometry folder containing photometry FITS
        and field image PNG
'''

import numpy as np
import matplotlib.pyplot as plt
import warnings; warnings.simplefilter('ignore') 
import sys
import argparse
import params # SAFPhot script

from os.path import join, dirname
from astropy.table import Table
from astropy.time import Time
from fitsio import FITS
from glob import glob
from matplotlib.backends.backend_pdf import PdfPages
from copy import copy
from matplotlib.image import imread
from shutil import copyfile
#from scipy.stats import pearsonr

warnings.simplefilter('ignore')

def get_sn_max(sn_max):
    sn_max_a = sn_max[0][0]
    sn_max_b = sn_max[1][0]
    return sn_max_a, sn_max_b

def bin_to_size(data, num_points_bin, block_exposure_times, 
        block_index_boundaries, mask):
    '''Convenience function to bin everything to a fixed num of points per
    bin. Data is clipped to the nearest bin (i.e. data % num_points_bin are
    discarded from the end of the time series).'''
    
    #Initialise storeage for blocks
    data_rack = []

    #Iterate over blocks
    for j, value in enumerate(block_index_boundaries):
        if j < len(block_index_boundaries) -1:
            #Get block
            data_block = data[value:block_index_boundaries[j+1]]
            mask_block = mask[value:block_index_boundaries[j+1]]
            
            #Clean out nans from block
            data_block = data_block[mask_block]

            #Calculate number of points per bin for block
            npb = int(num_points_bin / block_exposure_times[j])

            #bin block
            num_bins = int(len(data_block) / npb)
            data_block = rebin(data_block[0:num_bins*npb], num_bins)

            #Store block in rack
            data_rack.append(data_block)

    #Flatten rack
    rebinned_data = np.hstack(data_rack)
    return rebinned_data

def rebin(a, *args):
    '''From the scipy cookbook on rebinning arrays
    rebin ndarray data into a smaller ndarray of the same rank whose dimensions
    are factors of the original dimensions. eg. An array with 6 columns and 4 
    rows can be reduced to have 6,3,2 or 1 columns and 4,2 or 1 rows.
    example usages:
    a=rand(6,4); b=rebin(a,3,2)
    a=rand(6); b=rebin(a,2)'''
    shape = a.shape
    lenShape = len(shape)
    factor = np.asarray(shape)/np.asarray(args)
    evList = ['a.reshape('] + \
             ['args[%d],factor[%d],'%(i,i) for i in range(lenShape)] + \
             [')'] + ['.sum(%d)'%(i+1) for i in range(lenShape)] + \
             ['/factor[%d]'%i for i in range(lenShape)]
    return eval(''.join(evList))

def air_corr(flux, xjd, xjd_oot_l=99, xjd_oot_u=99):
    '''Function to remove a 2-D polynomial fit using the out of transit
    region.'''
    
    #Copy data to prevent overwriting input arrays
    flux_r = np.copy(flux)
    xjd_r = np.copy(xjd)

    #Divide out residual airmass using out of transit region
    oot = (((xjd_r < xjd_oot_l) | (xjd_r > xjd_oot_u)) & (np.isfinite(flux_r)) &
        (np.isfinite(xjd_r)))
    poly1 = np.poly1d(np.polyfit(xjd_r[oot], flux_r[oot], 2))
    p1 = poly1(xjd_r)
    flux_r /= p1
    return flux_r

def add_plot(x_in, y_in, ylabel=None, xoffset=0, s=10, c='b', alpha=1.0,
        xlim=[None, None], ylim=[None, None],
        xlabel=None, plot_oot_l_p=False, plot_oot_u_p=False,
        plot_rms=False, rms_mask=None, inc=False, hold=False):
   
    #Retrieve global variables
    global npp; global n_plotted; global n_plot_tot
    global fig; global figs; global ax; global axf; global used_axes
    
    #Check whether new plot page is required
    if (npp == 0) and (hold is False):

        #Initialise variables
        used_axes = []
        
        #Define figure and axes
        fig, ax = plt.subplots(
                nrows, ncols, figsize=figsize, dpi=dpi, sharex=True)
        axf = ax.flat
        fig.suptitle(target_name+', '+observat+' '
                +telescop+', '+filtera+', '+filterb+', '+str(dateobs))

    #Copy data
    x = np.copy(x_in) - xoffset
    y = np.copy(y_in)

    #Clip outliers
    if xlim[0] is not None:
        x[x < xlim[0]] = np.nan
    if xlim[1] is not None:
        x[x > xlim[1]] = np.nan
    if ylim[0] is not None:
        y[y < ylim[0]] = np.nan
    if ylim[1] is not None:
        y[y > ylim[1]] = np.nan
    
    #RMS
    if rms_mask is not None:
        mask = rms_mask
    else:
        mask = np.ones(x.shape[0], dtype=bool)
    rms = (np.nanstd(y[mask], ddof=1) / np.nanmedian(y[mask]))
    
    #Data label
    datalabel = 'RMS: %7.5f' % rms

    #Plot
    axf[npp].scatter(x, y, label=datalabel, s=s, c=c, alpha=alpha)

    #Axes labels
    cond_1 = (xlabel is not None) and (npp >= (nrows*ncols)-ncols)
    cond_2 = (xlabel is not None) and (n_plot_tot-n_plotted <= ncols)
    if any([cond_1, cond_2]) :
        plt.setp(axf[npp].get_xticklabels(), visible=True)
        axf[npp].set_xlabel(xlabel + " (-%d)" %xoffset)
    if ylabel is not None:
        axf[npp].set_ylabel(ylabel)

    #Legend
    if plot_rms is True:
        axf[npp].legend()

    #X lines
    if (xjd_oot_l_p is not None) and (plot_oot_l_p is True):
        axf[npp].axvline(x=xjd_oot_l_p - xoffset, c='g')
    if (xjd_oot_u_p is not None) and (plot_oot_u_p is True):
        axf[npp].axvline(x=xjd_oot_u_p - xoffset, c='g')
    
    #Increment plot counter
    if inc is True:
        used_axes.append(axf[npp])
        npp += 1
        n_plotted += 1

    #If page finished
    if (n_plot_tot - n_plotted == 0) or (npp >= (nrows*ncols)):
   
        #Remove empty axes:
        for ii in axf:
            if ii not in used_axes:
                ii.remove()

        #Save figure
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        figs.append(fig)
    
        #Reset plot counter
        if npp >= (nrows*ncols):
            npp = 0

def write_table_header(table, dic):
    for key in dic.keys():
        table.meta[key] = dic[key]
    return table

def update_table(table_in, dic):
    table_out = copy(table_in)
    for key in dic.keys():
        table_in[key] = dic[key]
    return table_out

def save_data_fits(table, file_name, comp_name):

    #Save data as FITS
    fits_name = join(dir_, file_name + '_%s.fits' % comp_name) 
    table.write(fits_name, overwrite=True)

def differential_photometry(i_flux, i_err, obj_index, comp_index,
        norm_mask=None):

    #Copy data to prevent overwriting of input arrays
    in_flux = np.copy(i_flux)
    in_err = np.copy(i_err)

    #If no norm_mask, set to array of ones
    if norm_mask is None:
        norm_mask = np.ones(in_flux.shape[-1], dtype=bool)

    #create variables to store the comparison star flux and flux err
    comp_flux = np.zeros((in_flux.shape[0], in_flux.shape[2], in_flux.shape[3]))
    comp_flux_err = np.zeros((in_err.shape[0], in_err.shape[2], in_err.shape[3]))

    #Make 0s nans so as not to bias calculations
    in_flux[in_flux == 0] = np.nan
    in_err[in_err == 0] = np.nan
   
    #Get object flux and error
    obj_flux = in_flux[:, obj_index, :, :]
    obj_flux_err = in_err[:, obj_index, :, :]
    '''obj_norm = (np.nanmedian((obj_flux[:, :, norm_mask]), 
                axis=2).reshape((in_flux.shape[0], in_flux.shape[2], 1)))'''
    
    #Get comparison flux and error
    comp_flux_raw = in_flux[:, comp_index, :, :]
    comp_flux_err_raw = in_err[:, comp_index, :, :]
    weight_vals = np.nanmean(1.0 / (comp_flux_err_raw / comp_flux_raw)**2,
        axis=-1).reshape((comp_flux_raw.shape[0],
        comp_flux_raw.shape[1], comp_flux_raw.shape[2], 1))
    weights = np.concatenate([weight_vals] * comp_flux_raw.shape[-1],
            axis=-1)
    nan_mask = np.logical_or(np.isnan(comp_flux_raw),
        np.isnan(comp_flux_err_raw))
    comp_flux = np.ma.masked_array(comp_flux_raw, mask=nan_mask)
    comp_flux_err = np.ma.masked_array(comp_flux_err_raw, mask=nan_mask)
    comp_flux = np.ma.average(comp_flux, weights=weights, axis=1)
    comp_flux_err = np.sqrt(1.0/np.sum(1.0/(comp_flux_err**2.0), axis=1))
    '''comp_norm = (np.nanmedian(comp_flux[:, :, norm_mask], 
            axis=2).reshape((comp_flux.shape[0], comp_flux.shape[1], 1)))'''

    #Get differential flux and error, normalised by median OOT region
    diff_flux = obj_flux / comp_flux
    diff_flux_err = diff_flux * np.sqrt((obj_flux_err/obj_flux)**2.0 +
                (comp_flux_err/comp_flux)**2.0)
    diff_norm = (np.nanmedian(diff_flux[:, :, norm_mask], 
            axis=2).reshape((diff_flux.shape[0], diff_flux.shape[1], 1)))
    diff_flux /= diff_norm
    diff_flux_err /= diff_norm 

    return diff_flux, diff_flux_err, obj_flux, comp_flux 
    
def plot_field_image(dir_, field_file, o_num, c_num):
    field_image = plt.imread(join(dir_,field_file))[:,:,:]
    fig = plt.figure(figsize=figsize, dpi=dpi)
    dmean = np.mean(field_image)
    dstd = np.std(field_image)
    plt.imshow(field_image, vmin=dmean-1*dstd, vmax=dmean+2*dstd,
        cmap=plt.get_cmap('gray'))
    plt.axis('off')
    fig.suptitle(target_name+', '+observat+' '
            +telescop+', '+filtera+', '+str(dateobs) + '\n\ntarget: %d;  '
            %o_num +'comparisons: %s' %[x for x in c_num])
    figs.append(fig)


if __name__ == "__main__":

    #Parse arguments from command line
    parser = argparse.ArgumentParser(
        description='Plotting script for photometry produced by SAFPhot')
    parser.add_argument('dir_in', metavar='dir_in', help='Input directory',
            type=str, action='store')
    args = parser.parse_args()

    #Load the list of parameters 
    p = params.get_params()

    '''===== START OF INPUT PARAMETERS ======'''
    
    #Specify input-output directory
    dir_ = args.dir_in
    
    #Specify input photometry file name
    infile_list = glob(join(dir_, p.phot_file_in))
    assert len(infile_list) != 0, "No photometry input file detected"
    assert len(infile_list) < 2, "Too many photometry input files detected: %d" \
            %(len(infile_list))
    infile_ = infile_list[0]
    
    #Specify input field image file name
    field_image_list = glob(join(dir_, p.field_image_in))
    assert len(field_image_list) != 0, "No field image input file detected"
    assert len(field_image_list) < 2, "Too many field image input files detected: %d" \
            %(len(field_image_list))
    field_file = field_image_list[0]
   
    #Define output FITS and PDF names
    outfile_pdf = infile_.replace(".fits", "_plot.pdf")
    outfile_fits = infile_.replace("_phot.fits", "_comp")

    #Define target and comparison object numbers (indicies) from field plot
    o_num = p.target_object_num           # As integer
    c_num = p.comparison_object_nums      # As list

    #Define normalised flux and time axis limits for plotting
    norm_flux_limits = p.norm_flux_limits
    time_axis_limits = p.time_axis_limits

    #Define plot time format to use [JD, HJD, BJD]
    plot_time_format = p.plot_time_format
    
    #Define time to bin up light curve (seconds)
    binning = p.binning
   
    #Ingress and egress times [None, value]
    global xjd_oot_l_p; xjd_oot_l_p = p.predicted_ingress   # predicted ingress
    global xjd_oot_u_p; xjd_oot_u_p = p.predicted_egress    # predicted egress
    global xjd_oot_l; xjd_oot_l = p.actual_ingress          # actual ingress
    global xjd_oot_u; xjd_oot_u = p.actual_egress           # actual egress
    
    #Define max number of plot panel rows and columns per page and other vars
    global ncols; ncols = p.ncols
    global nrows; nrows = p.nrows
    global figsize; figsize = p.figsize
    global dpi; dpi = p.dpi

    '''===== END OF INPUT PARAMETERS ====='''

    
    #Load data from photometry file
    with FITS(glob(join(dir_, infile_))[0]) as f:
        hdr = copy(f[0].read_header())
        flux = f['OBJ_FLUX'][:,:,:,:]
        fluxerr = f['OBJ_FLUX_ERR'][:,:,:,:]
        obj_bkg_app_flux = f['OBJ_BKG_APP_FLUX'][:,:,:,:]
        bkg_flux = f['RESIDUAL_BKG_FLUX'][:,:,:]
        ccdx = f['OBJ_CCD_X'][:,:]
        ccdy = f['OBJ_CCD_Y'][:,:]
        fwhm = f['MEAN_OBJ_FWHM'][:,:]
        jd = f['JD'][:]
        hjd = f['HJD_utc'][:]
        bjd = f['BJD_tdb'][:]
        exp = f['EXPOSURE_TIME'][:]
        airmass = f['AIRMASS'][:]
        apps = f['VARIABLES_APERTURE_RADII'][:]
        bkgs = np.char.strip(np.asarray(f['VARIABLES_BKG_PARAMS'][:],
            dtype='S10'))

    #Get key header information
    global target_name; target_name = hdr['TARGET']
    global dateobs; dateobs = Time(
            hdr['DATE-OBS'].strip(),format='isot',scale='utc',out_subfmt='date_hm')
    global observat; observat = hdr['OBSERVAT'].strip()
    global telescop; telescop = hdr['TELESCOP'].strip()
    global instrumt; instrumt = hdr['INSTRUMT'].strip()
    global observer; observer = hdr['OBSERVER'].strip()
    global analyser; analyser = hdr['ANALYSER'].strip()
    global filtera; filtera, _, _ = hdr['FILTERA'].strip().partition(' - ')
    global filterb; filterb, _, _ = hdr['FILTERB'].strip().partition(' - ')
    
    #Screen print
    print "\nPlotting photometry for: %s %s %s %s %s" %(target_name, observat,
            telescop, instrumt, filtera)

    #Create dictionary for header of output FITS
    header_dic = {'TARGET': target_name,
            'DATE-OBS': str(dateobs),
            'OBSERVAT': observat,
            'TELESCOP': telescop,
            'INSTRUMT': instrumt,
            'OBSERVER': observer,
            'ANALYSER': analyser,
            'FILTERA': filtera,
            'FILTERB': filterb}

    #Get preffered plot time format
    if plot_time_format == "HJD": xjd = hjd
    elif plot_time_format == "BJD": xjd = bjd
    else: xjd = jd
    
    #Get xjd offset time 
    xjd_off = np.floor(np.nanmin(xjd))

    #Get normalisation mask
    if xjd_oot_l is None: xjd_oot_l = np.nanmin(xjd)
    if xjd_oot_u is None: xjd_oot_u = np.nanmax(xjd)
    oot = (xjd < xjd_oot_l) | (xjd > xjd_oot_u)
    if np.any(oot):
        norm_mask = oot
    else:
        norm_mask = np.ones(xjd.shape[0], dtype=bool)

    #Identify blocks of frames with different exposure times
    block_ind_bound = np.array([0])
    block_ind_bound = np.append(block_ind_bound, np.where(exp[:-1] != exp[1:])[0] +1)
    block_exp_t = exp[block_ind_bound]
    block_ind_bound = np.append(block_ind_bound, exp.shape[0]).tolist()

    #Find background subtraction parameters with lowest residuals
    '''
    print ("Bkg subtraction residual flux for each parameter combination "\
        "summed across frames:")
    print np.nansum(bkg_flux, axis=(0,2))
    '''
    lowest_bkg = np.where(np.nansum(bkg_flux, axis=(0,2)) == np.nanmin(
        np.nansum(bkg_flux, axis=(0,2))))[0][0]
 
    #Initialise first page of output pdf
    global npp; npp = 0
    global figs; figs = []
    global n_plot_tot; n_plot_tot = 6 + 2*len(c_num)
    global n_plotted; n_plotted = 0


    '''TARGET VS MEAN/ENSAMBLE COMPARISON'''
    #Perform differential photometry using comparison ensemble
    diff_flux, diff_flux_err, obj_flux, comp_flux = differential_photometry(flux, 
                                                fluxerr, o_num, c_num, norm_mask)

    #Pick the best signal to noise (from oot region if specified)
    signal = np.nanmean(diff_flux[:,:,norm_mask], axis=2)
    noise = np.nanstd(diff_flux[:,:,norm_mask], axis=2, ddof=1)
    sn_max = (np.where(signal/noise == np.nanmax(signal/noise)))
    sn_max_bkg = (np.where(signal/noise == np.nanmax((signal/noise)[:,lowest_bkg])))
    sn_max_a, sn_max_b = get_sn_max(sn_max)
    sn_max_bkg_a, sn_max_bkg_b = get_sn_max(sn_max_bkg)
    
    #Print signal to noise
    '''
    print ("Max S/N overall: {:.2f}; aperture "\
            "rad: {:.1f} pix; bkg params: {}".format(np.nanmax((signal/noise)[:,:]),
            apps[sn_max_a], bkgs[sn_max_b]))
    '''
    print ("Max S/N with lowest bkg residuals: "\
            "{:.2f}; aperture rad: {:.1f} pix; bkg params: {}".format(
                np.nanmax((signal/noise)[:,lowest_bkg]),
                apps[sn_max_bkg_a],bkgs[sn_max_bkg_b]))
    
    #Get base data table for FITS output
    base_table = Table([jd, hjd, bjd, diff_flux[sn_max_bkg_a,sn_max_bkg_b,:], 
        diff_flux_err[sn_max_bkg_a,sn_max_bkg_b,:], 
        obj_bkg_app_flux[sn_max_bkg_a,o_num,sn_max_bkg_b], 
        ccdx[o_num, :], ccdy[o_num, :], 
        fwhm[sn_max_bkg_b,:], exp, airmass], 
        names=('JD_UTC', 'HJD_UTC', 'BJD_TDB', 'RELATIVE_FLUX', 'FLUX_ERROR',
            'BACKGROUND_FLUX', 'CCD_X', 'CCD_Y', 'SEEING_ARCSECONDS',
            'EXPOSURE_TIME_SECONDS', 'AIRMASS'))
    header_dic['APPRADUS'] = apps[sn_max_bkg_a]
    header_dic['BKGPARAM'] = bkgs[sn_max_bkg_b]
    base_table = write_table_header(base_table, header_dic)
    
    #Plot differential photometry using comparison ensemble
    add_plot(xjd, diff_flux[sn_max_bkg_a,sn_max_bkg_b,:],
        'Rel. flux (ensemble)', xoffset=xjd_off, xlabel=plot_time_format,
        plot_oot_l_p=True, plot_oot_u_p=True, plot_rms=True, rms_mask=norm_mask,
        xlim=time_axis_limits, ylim=norm_flux_limits, alpha=0.5, inc=False)
    
    #Bin data
    finite_mask = np.isfinite(diff_flux[sn_max_bkg_a, sn_max_bkg_b, :])
    flux_bin = bin_to_size(diff_flux[sn_max_bkg_a, sn_max_bkg_b, :], binning, 
            block_exp_t, block_ind_bound, finite_mask)
    xjd_bin = bin_to_size(xjd, binning, block_exp_t, block_ind_bound,
            finite_mask)
    fwhm_bin = bin_to_size(fwhm[sn_max_bkg_b,:], binning, block_exp_t, block_ind_bound,
            finite_mask)
    norm_mask_bin = bin_to_size(norm_mask, binning, block_exp_t, block_ind_bound,
            finite_mask)

    #plot Binned differential photometry using comparison ensemble
    add_plot(xjd_bin, flux_bin, xoffset=xjd_off,
        plot_rms=True, rms_mask=norm_mask_bin, xlim=time_axis_limits,
        ylim=norm_flux_limits, c='r', inc=True, hold=True)
    
    #Save data to FITS file
    params_to_update = {
        'RELATIVE_FLUX': diff_flux[sn_max_bkg_a,sn_max_bkg_b,:],
        'FLUX_ERROR': diff_flux_err[sn_max_bkg_a,sn_max_bkg_b,:],
        'BACKGROUND_FLUX': obj_bkg_app_flux[sn_max_bkg_a,o_num,sn_max_bkg_b,:]}
    updated_table = update_table(base_table, params_to_update)
    updated_table.meta['APPRADUS'] = apps[sn_max_bkg_a]
    updated_table.meta['BKGPARAM'] = bkgs[sn_max_bkg_b]
    save_data_fits(updated_table, outfile_fits, 'ensemble')


    ''''PLOT SYSTEMATIC INDICATORS'''
    '''
    corr_store = []
    for i in range(diff_flux[sn_max_bkg_a,sn_max_bkg_b, :].shape[0]):
        yy =pearsonr(np.roll(obj_bkg_app_flux[sn_max_bkg_a,o_num,sn_max_bkg_b],
            i), diff_flux[sn_max_bkg_a,sn_max_bkg_b])[0]
        corr_store.append(yy)
    add_plot(xjd, np.asarray(corr_store),
            ylabel='Background flux', xoffset=xjd_off, xlabel=plot_time_format, inc=True)
    ''' 
    add_plot(xjd, obj_bkg_app_flux[sn_max_bkg_a,o_num,sn_max_bkg_b,:], 
            ylabel='Background flux', xoffset=xjd_off, xlabel=plot_time_format,
            xlim=time_axis_limits, inc=True)
    add_plot(xjd, ccdx[o_num,:], ylabel='CCD_X', xoffset=xjd_off,
            xlabel=plot_time_format, xlim=time_axis_limits, inc=True)
    add_plot(xjd, fwhm[sn_max_bkg_b,:], xoffset=xjd_off,
            xlabel=plot_time_format, xlim=time_axis_limits, inc=False)
    add_plot(xjd_bin, fwhm_bin, ylabel='FWHM (arcsec)', xoffset=xjd_off,
            xlabel=plot_time_format, xlim=time_axis_limits, inc=True, hold=True, c='r')
    add_plot(xjd, ccdy[o_num,:], ylabel='CCD_Y', xoffset=xjd_off,
            xlabel=plot_time_format, xlim=time_axis_limits, inc=True)
    add_plot(xjd, airmass, ylabel='Airmass', xoffset=xjd_off,
            xlabel=plot_time_format, xlim=time_axis_limits, inc=True)
    

    #Work through the individual comparison stars
    for cindex in c_num:
        
        '''TARGET VS INDIVIDUAL COMPARISONS'''
        #Get differential flux of object with comparison star
        diff_flux, diff_flux_err, obj_flux, comp_flux = differential_photometry(
                flux, fluxerr, o_num, [cindex], norm_mask)
        signal = np.nanmean(diff_flux[:,:,norm_mask], axis=2)
        noise = np.nanstd(diff_flux[:,:,norm_mask], axis=2, ddof=1)
        sn_max = np.where(signal/noise == np.nanmax(signal/noise))
        sn_max_a, sn_max_b = get_sn_max(sn_max)
        sn_max_bkg = (np.where(signal/noise == np.nanmax(
            (signal/noise)[:,lowest_bkg])))
        sn_max_bkg_a, sn_max_bkg_b = get_sn_max(sn_max_bkg)
    
        #Plot differential photometry using individual comparisons
        add_plot(xjd, diff_flux[sn_max_bkg_a,sn_max_bkg_b,:],
            'Rel. flux (comp. %d)' %cindex, xoffset=xjd_off,
            xlabel=plot_time_format, plot_oot_l_p=True,
            plot_oot_u_p=True, plot_rms=True, rms_mask=norm_mask,
            xlim=time_axis_limits, ylim=norm_flux_limits, alpha=0.5, inc=False)
        
        #Bin data
        finite_mask = np.isfinite(diff_flux[sn_max_bkg_a, sn_max_bkg_b, :])
        flux_bin = bin_to_size(diff_flux[sn_max_bkg_a, sn_max_bkg_b, :], binning, 
                block_exp_t, block_ind_bound, finite_mask)
        xjd_bin = bin_to_size(xjd, binning, block_exp_t, block_ind_bound,
                finite_mask)
        norm_mask_bin = bin_to_size(norm_mask, binning, block_exp_t, block_ind_bound,
                finite_mask)
        #Plot binned photometry using individual comparisons
        add_plot(xjd_bin, flux_bin, xoffset=xjd_off,
            plot_rms=True, rms_mask=norm_mask_bin, xlim=time_axis_limits, 
            ylim=norm_flux_limits, c='r', inc=True, hold=True)
        
        #Save data to FITS file
        params_to_update = {
            'RELATIVE_FLUX':diff_flux[sn_max_bkg_a,sn_max_bkg_b,:],
            'FLUX_ERROR':diff_flux_err[sn_max_bkg_a,sn_max_bkg_b,:],
            'BACKGROUND_FLUX':obj_bkg_app_flux[sn_max_bkg_a,o_num,sn_max_bkg_b,:]}
        updated_table.meta['APPRADUS'] = apps[sn_max_bkg_a]
        updated_table.meta['BKGPARAM'] = bkgs[sn_max_bkg_b]
        updated_table = update_table(base_table, params_to_update)
        save_data_fits(updated_table, outfile_fits, cindex)
        

        '''EACH COMPARISON VS MEAN OF OTHER COMPARISONS'''
        #Get diff flux of comparison with mean of other comparisons
        if (len(c_num) > 1):
            comp_mask = np.not_equal(c_num, [cindex]*len(c_num))
            other_comps = np.asarray(c_num)[comp_mask]
            (diff_flux_other, diff_flux_other_err, obj_flux_other,
                comp_flux_other) = differential_photometry(
                                flux, fluxerr, cindex, other_comps)
            
            #Get signal to noise (from oot region if specified)
            signal = np.nanmean(diff_flux_other[:,:,:], axis=2) 
            noise = np.nanstd(diff_flux_other[:,:,:], axis=2, ddof=1)  
            sn_max_bkg = (np.where(signal/noise == 
                                        np.nanmax((signal/noise)[:,lowest_bkg])))
            sn_max_bkg_a, sn_max_bkg_b = get_sn_max(sn_max_bkg)
            
        
            #Plot differential photometry using individual comparisons
            add_plot(xjd, diff_flux_other[sn_max_bkg_a,sn_max_bkg_b,:],
                'Resid. (comp. %d)' %cindex, xoffset=xjd_off, 
                xlabel=plot_time_format, plot_oot_l_p=True, plot_oot_u_p=True,
                plot_rms=True, xlim=time_axis_limits, ylim=norm_flux_limits, 
                alpha=0.5, inc=False)
            
            #Bin data
            finite_mask = np.isfinite(diff_flux_other[sn_max_bkg_a, sn_max_bkg_b, :])
            flux_bin = bin_to_size(diff_flux_other[sn_max_bkg_a, sn_max_bkg_b, :], 
                    binning, block_exp_t, block_ind_bound, finite_mask)
            xjd_bin = bin_to_size(xjd, binning, block_exp_t, block_ind_bound,
                    finite_mask)
            
            #Plot differential photometry of comparison vs comparison residuals
            add_plot(xjd_bin, flux_bin, xoffset=xjd_off,
                plot_rms=True, xlim=time_axis_limits, ylim=norm_flux_limits,
                c='r', inc=True, hold=True)
    
    #Load field image and save as figure
    plot_field_image(dir_, field_file, o_num, c_num)

    #Save figures to output pdf
    with PdfPages(join(dir_, outfile_pdf)) as pdf:
        for fig in figs:
            plt.figure(fig.number)
            #plt.show()
            pdf.savefig()
            
    #Copy params script to dir_
    copyfile(join(dirname(__file__), 'params.py'), join(dir_, 'params.py'))

    print "Plotting complete"
