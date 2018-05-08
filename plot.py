#============ LC Plotting Script for SAAO Pipeline Photometry Output ==========#
# 1) Place this file in the same directory containing the reduction directory 
# generated by the SAAO pipeline created by Alex Chaushev.
#
# 2) Identify target and comparison object numbers from annotated map generated
# by SAAO pipeline.
#
# 3) Change variables below accordingly and run script
#==============================================================================#

import numpy as np
import matplotlib.pyplot as plt
import warnings; warnings.simplefilter('ignore') 
import sys

from os.path import join
from astropy.table import Table
from astropy.time import Time
from fitsio import FITS
from glob import glob
from matplotlib.backends.backend_pdf import PdfPages

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
        plt.cla()
        
        #Initialise variables
        used_axes = []
        
        #Define figure and axes
        fig, ax = plt.subplots(
                nrows, ncols, figsize=figsize, dpi=dpi, sharex=True)
        axf = ax.flat
        fig.suptitle(target_name+', '+observat+' '
                +telescop+', '+filtera+', '+str(dateobs))

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
        axf[npp].tick_params(axis='x', labelbottom=True)
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

def save_data_fits(table, header, file_name, comp_name):

    #Save data as FITS
    fits_name = join(dir_, "SAAO_"+ file_name + '_%s.fits' % comp_name) 
    table.write(fits_name, header=header, overwrite=True)

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
    nan_mask = np.logical_or(np.isnan(comp_flux_raw),
            np.isnan(comp_flux_err_raw))
    comp_flux = np.ma.masked_array(comp_flux_raw, mask=nan_mask)
    comp_flux_err = np.ma.masked_array(comp_flux_err_raw, mask=nan_mask)
    comp_flux = np.average(comp_flux, weights=1/(comp_flux_err**2), axis=1)
    comp_flux_err = np.sqrt(1/np.sum(1/(comp_flux_err**2), axis=1))
    '''comp_norm = (np.nanmedian(comp_flux[:, :, norm_mask], 
            axis=2).reshape((comp_flux.shape[0], comp_flux.shape[1], 1)))'''

    #Get differential flux and error, normalised by median OOT region
    diff_flux = obj_flux / comp_flux
    diff_flux_err = diff_flux * np.sqrt((obj_flux_err/obj_flux)**2 +
                (comp_flux_err/comp_flux)**2)
    diff_norm = (np.nanmedian(diff_flux[:, :, norm_mask], 
            axis=2).reshape((diff_flux.shape[0], diff_flux.shape[1], 1)))
    diff_flux /= diff_norm
    diff_flux_err /= diff_norm 

    return diff_flux, diff_flux_err, obj_flux, comp_flux 

class Logger(object):
    def __init__(self, _dir):
        self._dir = _dir
        self.terminal = sys.stdout
        self.log = open(join(self._dir, "SAAO_phot.log"), "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        pass


if __name__ == "__main__":

    '''===== START OF INPUT PARAMETERS ======'''
    
    #Specify input-output directory and file names
    dir_ = '/scratch/ngts/lr182/SAAO_test_data/NOI_101380_5th_v/photometry'
    infile_ = 'SAAO_NOI-101380_V_Green_phot.fits'
    outfile_pdf = infile_.replace(".fits", "_plot.pdf")

    #Define target and comparison object numbers (indicies) from field plot
    o_num = 1           # As integer
    c_num = [0, 2]      # As list

    #Define normalised flux limits outside which outliers are clipped
    norm_flux_upper = 1.2
    norm_flux_lower = 0

    #Define plot time format to use [JD, HJD, BJD]
    plot_time_format = "JD"
    
    #Define time to bin up light curve (seconds)
    binning = 10 * 60
   
    #Ingress and egress times [None, value]
    global xjd_oot_l_p; xjd_oot_l_p = 2458155.36      # predicted ingress
    global xjd_oot_u_p; xjd_oot_u_p = 2458155.46      # predicted egress
    global xjd_oot_l; xjd_oot_l = 2458155.36       # actual ingress
    global xjd_oot_u; xjd_oot_u = 2458155.46        # actual egress
    
    #Define max number of plot panel rows and columns per page and other vars
    global ncols; ncols = 2
    global nrows; nrows = 3
    global figsize; figsize = (12,8)
    global dpi; dpi = 100

    '''===== END OF INPUT PARAMETERS ====='''

    
    #Initialise instance of Logger which saves screen prints to .log file 
    sys.stdout = Logger(dir_) 
    
    #Load data from photometry file
    with FITS(glob(join(dir_, infile_))[0]) as f:
        hdr = f[0].read_header()
        flux = f['OBJ_FLUX'][:,:,:,:]
        fluxerr = f['OBJ_FLUX_ERR'][:,:,:,:]
        #fluxflags = f['OBJ_FLUX_FLAGS'][:,:,:,:]
        obj_bkg_app_flux = f['OBJ_BKG_APP_FLUX'][:,:,:,:]
        bkg_flux = f['RESIDUAL_BKG_FLUX'][:,:,:]
        ccdx = f['OBJ_CCD_X'][:,:]
        ccdy = f['OBJ_CCD_Y'][:,:]
        fwhm = f['MEAN_OBJ_FWHM'][:,:]
        jd = f['JD'][:]
        hjd = f['HJD_utc'][:]
        bjd = f['BJD_tdb'][:]
        #frame_shift_x = f['FRAME_SHIFT_X'][:]
        #frame_shift_y = f['FRAME_SHIFT_Y'][:]
        exp = f['EXPOSURE_TIME'][:]
        airmass = f['AIRMASS'][:]
        apps = f['VARIABLES_APERTURE_RADII'][:]
        bkgs = np.char.strip(np.asarray(f['VARIABLES_BKG_PARAMS'][:],
            dtype='S10'))

    #Get key header infiormation
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

    #Get base data table for FITS output
    base_table = Table([jd, hjd, bjd, flux[0,o_num,0,:], fluxerr[0,o_num,0,:], 
        obj_bkg_app_flux[0,o_num,0,:], ccdx[o_num, :], ccdy[o_num, :], 
        fwhm[0,:], exp, airmass], 
        names=('JD_UTC', 'HJD_UTC', 'BJD_TDB', 'RELATIVE_FLUX', 'FLUX_ERROR',
            'BACKGROUND_FLUX', 'CCD_X', 'CCD_Y', 'SEEING_ARCSECONDS',
            'EXPOSURE_TIME_SECONDS', 'AIRMASS'))
    
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
    print ("Bkg subtraction residual flux for each parameter combination "\
        "summed across frames:")
    print np.nansum(bkg_flux, axis=(0,2))
    lowest_bkg = np.where(np.nansum(bkg_flux, axis=(0,2)) == np.nanmin(
        np.nansum(bkg_flux, axis=(0,2))))[0][0]
 
    #Initialise first page of output pdf
    global npp; npp = 0
    global figs; figs = []
    global n_plot_tot; n_plot_tot = 6 + 2*len(c_num)
    global n_plotted; n_plotted = 0

    '''TARGET VS MEAN/ENSAMBLE COMPARISON'''
    #Perform differential photometry using comparison ensamble
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
    print ("Max S/N overall: {:.2f}; aperture "\
            "rad: {:.1f} pix; bkg params: {}".format(np.nanmax((signal/noise)[:,:]),
            apps[sn_max_a], bkgs[sn_max_b]))
    print ("Max S/N with lowest bkg residuals: "\
            "{:.2f}; aperture rad: {:.1f} pix; bkg params: {}".format(
                np.nanmax((signal/noise)[:,lowest_bkg]),
                apps[sn_max_bkg_a],bkgs[sn_max_bkg_b]))
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

    #Plot differential photometry using comparison ensamble
    add_plot(xjd, diff_flux[sn_max_bkg_a,sn_max_bkg_b],
        'Rel. flux (ensamble)', xoffset=xjd_off, xlabel=plot_time_format, plot_oot_l_p=True,
        plot_oot_u_p=True, plot_rms=True, rms_mask=norm_mask,
        ylim=[norm_flux_lower, norm_flux_upper], alpha=0.5, inc=False)
    #Binned
    add_plot(xjd_bin, flux_bin, xoffset=xjd_off,
        plot_rms=True, rms_mask=norm_mask_bin, ylim=[norm_flux_lower,
            norm_flux_upper], c='r', inc=True, hold=True)
    
    ''''PLOT SYSTEMATIC INDICATORS'''
    add_plot(xjd, obj_bkg_app_flux[sn_max_bkg_a,o_num,sn_max_bkg_b,:],
            ylabel='Background flux', xoffset=xjd_off, xlabel=plot_time_format, inc=True)
    add_plot(xjd, ccdx[o_num,:], ylabel='CCD_X', xoffset=xjd_off,
            xlabel=plot_time_format, inc=True)
    add_plot(xjd, fwhm[sn_max_bkg_b,:], xoffset=xjd_off, xlabel=plot_time_format,
            inc=False)
    add_plot(xjd_bin, fwhm_bin, 
            ylabel='FWHM (arcsec)', xoffset=xjd_off, xlabel=plot_time_format,
            inc=True, hold=True, c='r')
    add_plot(xjd, ccdy[o_num,:], ylabel='CCD_Y', xoffset=xjd_off,
            xlabel=plot_time_format, inc=True)
    add_plot(xjd, airmass, ylabel='Airmass', xoffset=xjd_off,
            xlabel=plot_time_format, inc=True)
    

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
    
        #Bin data
        finite_mask = np.isfinite(diff_flux[sn_max_bkg_a, sn_max_bkg_b, :])
        flux_bin = bin_to_size(diff_flux[sn_max_bkg_a, sn_max_bkg_b, :], binning, 
                block_exp_t, block_ind_bound, finite_mask)
        xjd_bin = bin_to_size(xjd, binning, block_exp_t, block_ind_bound,
                finite_mask)
        norm_mask_bin = bin_to_size(norm_mask, binning, block_exp_t, block_ind_bound,
                finite_mask)
    
        #Plot differential photometry using individual comparisons
        add_plot(xjd, diff_flux[sn_max_bkg_a,sn_max_bkg_b],
            'Rel. flux (comp. %d)' %cindex, xoffset=xjd_off,
            xlabel=plot_time_format, plot_oot_l_p=True,
            plot_oot_u_p=True, plot_rms=True, rms_mask=norm_mask,
            ylim=[norm_flux_lower, norm_flux_upper], alpha=0.5, inc=False)
        #Binned
        add_plot(xjd_bin, flux_bin, xoffset=xjd_off,
            plot_rms=True, rms_mask=norm_mask_bin, ylim=[norm_flux_lower,
                norm_flux_upper], c='r', inc=True, hold=True)
        
        
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
            
            #Bin data
            finite_mask = np.isfinite(diff_flux_other[sn_max_bkg_a, sn_max_bkg_b, :])
            flux_bin = bin_to_size(diff_flux_other[sn_max_bkg_a, sn_max_bkg_b, :], 
                    binning, block_exp_t, block_ind_bound, finite_mask)
            xjd_bin = bin_to_size(xjd, binning, block_exp_t, block_ind_bound,
                    finite_mask)
            #norm_mask_bin = bin_to_size(
            #        norm_mask, binning, block_exp_t, block_ind_bound,finite_mask)
        
            #Plot differential photometry using individual comparisons
            add_plot(xjd, diff_flux_other[sn_max_bkg_a,sn_max_bkg_b],
                'Resid. (comp. %d)' %cindex, xoffset=xjd_off, 
                xlabel=plot_time_format, plot_oot_l_p=True, plot_oot_u_p=True,
                plot_rms=True, ylim=[norm_flux_lower, norm_flux_upper], 
                alpha=0.5, inc=False)
            #Binned
            add_plot(xjd_bin, flux_bin, xoffset=xjd_off,
                plot_rms=True, ylim=[norm_flux_lower,
                    norm_flux_upper], c='r', inc=True, hold=True)
    
    #Save figures to output pdf
    with PdfPages(join(dir_, outfile_pdf)) as pdf:
        for fig in figs:
            plt.figure(fig.number)
            pdf.savefig()
