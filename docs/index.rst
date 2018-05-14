.. SAFPhot documentation master file, created by
   sphinx-quickstart on Sun Apr 29 15:14:06 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   
SAFPhot: Photometry for SAAO telescopes 
===================================

.. toctree::
   :caption: Table on Contents
 
The SAFPhot pipeline was designed to enable fast and automatic processing of data taken using the 1.0 and 1.9m telescopes at the South African Astonomical Observatory. SAFPhot is focused on producing high quality photometry with a focus on transit photometry, however it is a general package which can be applied to data taken from any stellar sources. 

Installation
============

SAFPhot is available in the Python pacakge index (PyPI) and so can be installed with pip. Navigate to the directory where you would like to install SAFPhot and run the following command:::

   pip install safphot 

Pip will automatically install package dependencies if they are not satisfied. There should now be a folder called SAFPhot in the directory. This contains all the scripts used to run the pipeline. 
 

Quickstart
==========

We have provided a dataset to test the pipeline on RFS at /rfs/XROA/Shared/SAFPhot_test_data/NOI_101380_5th_v . 
Copy the files into a local directory. Then switch to the directory where you have SAFPhot installed. You should be able to 
see the full list of python scripts including "safphot.py".::

   cp -r /rfs/XROA/Shared/SAFPhot_test_data/NOI_101380_5th_v /path/to/data/dir/ 
   cd /path/to/SAFPhot/ 

To run the pipeline on the test set use the following command:::

   python safphot.py --p SHH* testset/ both 

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



