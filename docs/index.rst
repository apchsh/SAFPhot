.. SAFPhot documentation master file, created by
   sphinx-quickstart on Sun Apr 29 15:14:06 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:tocdepth: 2 

SAFPhot: Photometry for SAAO telescopes 
===================================

.. toctree::
   :capition: Table on Contents
 
The SAFPhot pipeline was designed to enable fast and automatic processing of data taken using the 1.0 and 1.9m telescopes at the South African Astonomical Observatory. SAFPhot is focused on producing high quality photometry with a focus on transit photometry, however it is a general package which can be applied to data taken from any stellar sources. 

Installation
------------

SAFPhot is available in the Python pacakge index (PyPI) and so can be installed with pip. Navigate to the directory where you would like to install SAFPhot and run the following command: 

.. codeblock::
   pip install safphot 

Pip will automatcially install package dependencies if they are not satisfied.
 

Quickstart
----------

We have provided 


Tutorial
--------

..
   API
   ---

   Troubleshooting
   ---------------

Acknowledgements
----------------

The pipeline uses the SEP package (http://sep.readthedocs.io/en/v1.0.x/) for aperture photometry and source extraction. The Donuts package (https://donuts.readthedocs.io/en/latest/) is used for image alignment. 



