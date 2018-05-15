.. SAFPhot documentation master file, created by
   sphinx-quickstart on Sun Apr 29 15:14:06 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   
SAFPhot: Photometry for SAAO telescopes 
===================================

.. toctree::
   :caption: Table on Contents
 
The SAFPhot pipeline was designed to enable fast, automatic reduction and photometric analysis of data taken using the 1.0 and 1.9m telescopes at the South African Astonomical Observatory (SAAO). The photometry components of SAFPhot have been optimised for differential photometry of transiting and eclipsing targets but can also be used be used for other astronomical targets and, in principle, applied to reduced data obtained with other (non-SAAO) telescopes.

Installation
============

SAFPhot is available in the Python pacakge index (PyPI) and so can be installed with pip. Navigate to the directory where you would like to install SAFPhot. If installing SAFPhot on a personal machine, run the following command::

    sudo pip install -e git+https://github.com/apchsh/SAFPhot.git#egg=safphot
         
For installation on ALICE and managed systems, run::

    pip install --user -e git+https://github.com/apchsh/SAFPhot.git#egg=safphot

After running the pip install command there should now be a directory called 'src'. The directory structure should look something like this::

    src/
       + safphot/
          - SAFPhot/
            ++ safphot.py
            ++ params.py
            ++ ... 
          - docs/
          - tests/
          - docs/
          - utilities/
          - setup.py
          - ...  

For clarity, we recommend the user moves the 'safphot' directory and all subdirectories within to the same root directory as 'src'. The 'src' directory should then contain only a single .txt file; the 'src' directory can be deleted.

The sub-folder 'SAFPhot' contains all the scripts needed to run the pipeline. The scripts the user must run or edit are as follows::

    safphot.py - main script to run
    params.py - configuration script to edit, where the user can define options
    plot.py - plotting script to run, analyses the photometry output

At present the directory is overly-complicated as we are still under-development and testing. Future releases of safphot will have a cleaner and simpler installation. 


Quickstart
==========

1. Copy science image fits files, along with appropriate flat field and bias
   calibration files, into a new directory with appropriate name for the target
   object.

2. Configure options in 'params.py' file according to preference
    
3. Then run the following command::
        
        python safphot.py {path/to/data/dir/} {mode}

   Available modes include::

        reduction - reduction only
        photometry - photometry only (on reduced data)
        both - reduction and photometry



   Optional arguments::
        --p   match only files with specified pattern prefix in their name

4. To analyse the photometry, view the field PNG image in the photometry sub
   directory to assertain the object numbers of the taget and comparison stars. Update the 'TARGET_OBJECT_NUM', 'COMPARISON_OBJECT_NUMS', and other relevant keywords in the 'PLOT PARAMETERS' section of the 'params.py' file. Run::

        plot.py {path/to/data/photometry/dir/}



Test dataset
=============

We have provided a dataset to test the pipeline, available on RFS at::
    /rfs/XROA/Shared/SAFPhot_test_data/NOI_101380_5th_v . 

To use the test dataset, first copy the files into a local directory. Then switch to the directory where you have SAFPhot installed. You should be able to see the full list of python scripts including "safphot.py"::

   cp -r /rfs/XROA/Shared/SAFPhot_test_data/ /path/to/data/dir/ 
   cd /path/to/SAFPhot/ 

To run the pipeline on the test set use the following command::

   python safphot.py --p SHA* path/to/data/dir/ both 

Once the pipeline has finished running there will be three new folders in the data directory::
    'calframes/' - contains the master bias and flat field calibration frames
    'reduction/' - contains the individual reduced images
    'photometry/' - contains a fits file with the photometric data and a PNG of the
                first image with objects numbered

To analyse the photometry, run::

    python plot.py path/to/data/photometry/dir/

After the script has finished running, some new files will appear in the
photometry subdirectory::

    '*_plot.pdf' - a PDF file containing photometric plots and field image
    '*comp_ensamble.fits' - data file containing differential photometry using
                        comparison star ensable
    '*comp_X.fits' - data file containing differential photometry using
                        individual star number X
    'params.py' - copy of params.py file at the time the plot.py script was
                        run. Serves as a reference of runtime configuration


The pipeline parameters can be changed by modifying the params.py in the installation directory. A pipeline that fails half-way can be resumed by re-running the pipeline. Any output files that already exist will not be re-created. If new data is added to a lightcurve, the photometry file for the lightcurve needs to the deleted, in order for the new data to be incorporated. SAFPhot can be run on multiple nights of data, for multiple objects, by simply placing all the files in the same directory. 

..   Tutorial
..   --------
..   API
..   ---
..   Troubleshooting
..   ---------------
..   for help running SAFPhot, run:  python safphot.py -h

Acknowledgements
================

The pipeline uses the SEP package (http://sep.readthedocs.io/en/v1.0.x/) for aperture photometry and source extraction. The Donuts package (https://donuts.readthedocs.io/en/latest/) is used for image alignment. 



