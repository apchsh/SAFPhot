from setuptools import setup, find_packages

setup(
  name = 'safphot',
  packages=find_packages(exclude=['*.pyc', 'utilities']),
  #packages = ['SAFPhot', 'docs', 'tests'],
  version = '0.1',
  description = 'Reduction and photometry pipeline for SAAO small telescopes',
  author = 'Alexander Chaushev, Liam Raynard',
  author_email = 'apc34@le.ac.uk',
  url = 'https://github.com/apchsh/SAFPhot', # use the URL to the github repo
  download_url = 'https://github.com/apchsh/SAFPhot/archive/0.1.tar.gz',
  keywords = ['SAAO', 'reduction', 'photometry', 'pipeline', 'astronomy'],
  classifiers = [
       'Development Status :: 3 - Alpha',
       'Programming Language :: Python :: 2.7'
   ],
  python_requires=['2.7'],
  install_requires=['numpy>=1.14.2', 'astropy>=2.0.5', 'sep>=1.0.0',
      'fitsio>=0.9.10', 'donuts>=0.2.4', 'matplotlib>=2.0.0', 'scipy>=1.0.0',
      'scikit-image>=0.13.0'
   ]
)
