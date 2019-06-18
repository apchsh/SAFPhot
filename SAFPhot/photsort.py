import numpy as np

from astropy.io import fits
from fnmatch import fnmatch
from os import path, walk
from glob import glob
from validate import ValidateFits

class InputDirError(Exception):
    pass

def get_all_files(folder, extension=".fits"):

    filestore = []

    for root, dirs, files in walk(folder):
        for file_ in files:
            if fnmatch(file_, extension):
                filestore.append(path.join(root, file_))

    return sorted(filestore)

class fits_sort():

    # results
    dir_ = ""
    bias = []
    flat = []; flat_filter = [];
    target = []; target_filter = []; target_name = []; 
    target_ra = []; target_dec = []

    def __init__(self, params, search_dir, pattern, verbose=False):


        if path.isdir(search_dir):

            # run the main function of the object, search and classify files
            self.search(params, search_dir, pattern, verbose)

            self.dir_ = search_dir

        else:

            raise InputDirException("%s does not exist." % search_dir)

    def search(self, params, search_dir, pattern, verbose):

        if verbose: print("Searching directory %s" % search_dir)

        # Find all files
        token = pattern + "*.fits" 
        files =  get_all_files(search_dir, extension=token)

        if verbose: print("%i files found." % len(files))
 
        # Prepare validator object
        fitsval = ValidateFits(params)
        skip_count = 0 

        for file_ in files:

            # CHECK FILE EXISTS, HAS VALID HEADER AND ISN'T IN OUTPUT DIR
            if fitsval.check(file_):

                # OPEN FILES
                f = fits.open(file_) 
                fobstype = f[0].header[params.obstype]
                fobject = f[0].header[params.target]
                if not(params.filtera == ''):
                    filtera = f[0].header[params.filtera]
                if not(params.filterb == ''):
                    filterb = f[0].header[params.filterb]
            
                # CLEAN FILTERS
                filtera, _, _ = filtera.strip().strip('\n').partition(' - ')
                if 'Empty' in filtera: filtera = ''
                filterb, _, _ = filterb.strip().strip('\n').partition(' - ')
                if 'Empty' in filterb: filterb = ''
                filter_ = filtera + filterb 
                if filter_ == '': filter_ = 'WHITE'

                # SPLIT FILES INTO OBJECTS
                if params.biasid in fobstype.upper() or params.biasid in fobject.upper():
                    self.bias.append(file_) 
                elif params.flatid in fobstype.upper() or params.flatid in fobject.upper():
                    self.flat.append(file_)
                    self.flat_filter.append(filter_) 
                else:
                    self.target.append(file_)
                    self.target_filter.append(filter_)
                    self.target_name.append((fobject + " (%s)") % filter_)
                    self.target_ra.append(f[0].header[params.ra])
                    self.target_dec.append(f[0].header[params.dec])

                #CLOSE THE FILE
                f.close()

            else: skip_count += 1 
                
        if skip_count > 0: 
            print("%i files skipped, which were either invalid or in the \
                specified calibration, reduction or photometry directories." \
                % skip_count)
        

        if verbose: print("Files sorted.")

    def summary_ra_dec(self):

        #Information about targets
        print("Found %i target files:" % len(self.target_name))
        temp_targs = np.array(self.target_name, dtype=str)
        for targ, ra, dec in zip(self.target_name, self.target_ra,
                self.target_dec):
            print("\t %s, ra: %s, dec %s." % (targ, ra, dec))


