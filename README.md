# SAFPhot

A series of scripts to analyse data taken with SHOC on the 1m telescope in SAAO. 

## Requirements

A recent version of Numpy and Scipy is required. SEP (http://sep.readthedocs.io/en/v1.0.x/index.html) is used to perform photometry on the the sciences images. Currently both FITSIO and PyFITs needs to be installed for the pipeline to work. This is due to bugs in the versions of the libraries available on the ALICE/SPECTRE super computer systems in the University of Leicester where this code is primarily run. PyFITS needs to be callable as "pyfits", so installing via astropy.io will not work at this stage. 

All libraries are instalable via pip, e.g. "pip install fitsio". 

## Running SAFPhot

SAFPhot has been designed to be run on a full observing run's worth of data, once the data has been collected. As such it is expected that SAFPhot will only be run once for each science target, and repeated attempts to run SAFPhot on the same directory will cause errors (at this stage). Simply use the following command "python safphot.py -c SH* -d /path/to/your/dir/". 
The "-c" parameter takes the camera name (SHA/SHD/SHH) and the -d parameters takes the path to the directory. 

SAFPhot will produce: a calframes folder (holding the current calibration frames), a reduction folder (holding the split and reduced frames) and .dat files with the jd and flux values for the data. 


