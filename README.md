# SAFPhot

A series of scripts to analyse data taken with SHOC on the 1m and 1.9m telescopes at SAAO. 

## Requirements

A recent version of Numpy and Scipy is required. SEP (http://sep.readthedocs.io/en/v1.0.x/index.html) is used to perform photometry on the the sciences images. Currently both FITSIO and PyFITs needs to be installed for the pipeline to work. This is due to bugs in the versions of the libraries available on the ALICE/SPECTRE super computer systems in the University of Leicester where this code is primarily run. PyFITS needs to be callable as "pyfits", so installing via astropy.io will not work at this stage. Donuts (https://donuts.readthedocs.io/en/master/) is required to calculate the shift of each frame relative to the first frame. The current release version of Donuts (V0.2.1) still uses function arguments which have been depricated in more recent versions. E.g. in skimage.transform.resize, mode='nearest'.

All libraries are instalable via pip, e.g. "pip install fitsio". 

## Running SAFPhot

SAFPhot has been designed to be run on a full observing run's worth of data, once the data has been collected. As such it is expected that SAFPhot will only be run once for each science target, and repeated attempts to run SAFPhot on the same directory will cause errors (at this stage). Simply use the following command "python safphot.py -c SH* -d /path/to/your/dir/". 
The "-c" parameter takes the camera name (SHA/SHD/SHH), the "-t" parameter takes the telescope (1.0/1.9) and the "-d" parameters takes the path to the directory. 

SAFPhot will produce: a calframes folder (holding the current calibration frames), a reduction folder (holding the split and reduced frames) and .dat files with the jd and flux values for the data. 


## ToDo - Version 0.1 

- Add an end-to-end test to the code with examples from the 1.0m and 1.9m telescope header files. Add other tests as appropriate. 
- Add functionality in photsort.py to continue from a partially completed run of SAFPhot. In other words don't re-run all processing.
- Review mandatory vs optional arguments so safphot can be run on reduced
  images from other programs.
- Review output format of all files. Consolidate as much as possible, particularly main output file from plot.py. Combine flux into FITS megafiles? 
- Check compatability with latest DONUTS version. 
- Add comments _everywhere_. 
- Remove need for separate phot files for each telescope by defining default plate scales, background params and aperture radii in a file. Also create optional arguments to let user specify their own at runtime. Save the values used to a file for downstream use by plot.py
- Review binning logic. Currently binning relies on user specifying frame
  intervals and corresponding exposure times. Use header keyword to determine binning?
- Create subplot pdf of most important plots and add plots to show systematics e.g. FWHM, background, CCDX, CCDY, comparison-X vs comparison-Y residuals etc
- In phot.py, create separate ingress and egress times for expected vs actual so predicted times can still be shown but highest S/N can use more accurate values.
  determined by user.
- In phot.py, modify comparison ensamble to use weighted sum/average according
  to flux errors
