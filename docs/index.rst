.. SAFPhot documentation master file, created by
   sphinx-quickstart on Sun Apr 29 15:14:06 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   
SAFPhot: Photometry for SAAO telescopes 
===================================

.. toctree::
   :caption: Table on Contents
 
The SAFPhot pipeline was designed to enable fast and automatic processing of data taken using the 1.0 and 1.9m telescopes at the South African Astonomical Observatory. SAFPhot is focused on producing high quality photometry for transit photometry, however it is a general package which can be applied to data taken from any stellar sources. 

Installation
============

SAFPhot is available in the Python pacakge index (PyPI) and so can be installed with pip. Navigate to the directory where you would like to install SAFPhot and run the following command:::

         sudo pip install -e git+https://github.com/apchsh/SAFPhot.git#egg=safphot
         
We recommend you make a new directory for this as pip will install all the package dependencies in there under a directory called source. After running the script there should now be a folder called src/safphot/ in the directory. The directory structure should now be something like this::

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


The sub-folder SAFPhot contains all the scripts needed to run the pipeline, with safphot.py being the main script and params.py containing all the options. At present the directory is over-complicated as we are still under-development and testing. Future releases of safphot will have a cleaner and simpler installation. 


Quickstart
==========

We have provided a dataset to test the pipeline on RFS at /rfs/XROA/Shared/SAFPhot_test_data/NOI_101380_5th_v . 
Copy the files into a local directory. Then switch to the directory where you have SAFPhot installed. You should be able to 
see the full list of python scripts including "safphot.py".::

   cp -r /rfs/XROA/Shared/SAFPhot_test_data/NOI_101380_5th_v /path/to/data/dir/ 
   cd /path/to/SAFPhot/ 

To run the pipeline on the test set use the following command:::

   python safphot.py --p SHH* testset/ both 


Once the pipeline has finished running there will be three new folders in the data directory. "Calframes" contains the master bias and flat field calibration frames, "reduction" contains the individual reduced images and finally "photometry" contains a fits file with the photometric measurements, time values and a host of other useful information. 

..

   Tutorial
   --------

   API
   ---

   Troubleshooting
   ---------------

Acknowledgements
================

The pipeline uses the SEP package (http://sep.readthedocs.io/en/v1.0.x/) for aperture photometry and source extraction. The Donuts package (https://donuts.readthedocs.io/en/latest/) is used for image alignment. 



