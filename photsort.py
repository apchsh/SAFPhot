import numpy as np

from astropy.io import fits
from fnmatch import fnmatch
from os import path, walk
from glob import glob

def get_all_files(folder, extension=".fits"):

    filestore = []

    for root, dirs, files in walk(folder):
        for file_ in files:
            if fnmatch(file_, extension):
                filestore.append(path.join(root, file_))

    return sorted(filestore)

class fits_sort():

    # directory
    dir_ = ""
    cam = ""
    verbose = False

    # results
    bias = []
    flat = []; flat_filter = [];
    target = []; target_filter = []; target_name = []; 
    target_ra = []; target_dec = []

    def __init__(self, search_dir, camera, verbose=False):

        # add check in here to check the directory is real and camera is valid
        self.dir_ = search_dir
        self.cam = camera
        self.verbose = verbose

        # run the main function of the object, search and classify files
        self.search()

        # print a summary
        self.summary()

    def search(self):

        if self.verbose: print "Searching directory %s" % self.dir_

        # Find all files
        token = self.cam +  "_*.fits" 
        files =  get_all_files(self.dir_, extension=token)

        if self.verbose: print "%i files found." % len(files)

        for file_ in files:
        
            # OPEN FILES
            f = fits.open(file_)  
            fobstype = f[0].header['OBSTYPE']
            fobject = f[0].header['OBJECT']
            filtera = f[0].header['FILTERA']
            filterb = f[0].header['FILTERB']
        
            # CLEAN FILTERS
            filtera = filtera.strip().strip('\n')
            if 'Empty' in filtera: filtera = ''
            filterb = filterb.strip().strip('\n') 
            if 'Empty' in filterb: filterb = ''
            filter_ = filtera + filterb 
            if filter_ == '': filter_ = 'WHITE'

            # SPLIT FILES INTO OBJECTS
            if "BIAS" in fobstype.upper() or "BIAS" in fobject.upper():
                self.bias.append(file_) 
            elif "FLAT" in fobstype.upper() or "FLAT" in fobject.upper():
                self.flat.append(file_)
                self.flat_filter.append(filter_) 
            else:
                self.target.append(file_)
                self.target_filter.append(filter_)
                self.target_name.append((fobject + " (%s)") % filter_)
                self.target_ra.append(f[0].header['OBJRA'])
                self.target_dec.append(f[0].header['OBJDEC'])

            #CLOSE THE FILE
            f.close()

        if self.verbose: print "Files sorted." 

    def summary(self):

        #Information about bias files
        print "Found %i bias files." % len(self.bias)
        
        #Information about flat files
        print "Found %i flat files:" % len(self.flat)
        temp = np.array(self.flat_filter, dtype=str)
        for filter_ in set(self.flat_filter):
            print "\t %i files in %s band." % (sum(temp==filter_), filter_)
        
        #Information about targets
        print "Found %i target files:" % len(self.target_name)
        temp_targs = np.array(self.target_name, dtype=str)
        for object_ in set(self.target_name): 
            print "\t %i files for target %s." % (sum(temp_targs==object_),
                    object_)

    def summary_ra_dec(self):

        #Information about targets
        print "Found %i target files:" % len(self.target_name)
        temp_targs = np.array(self.target_name, dtype=str)
        for targ, ra, dec in zip(self.target_name, self.target_ra,
                self.target_dec):
            print "\t %s, ra: %s, dec %s." % (targ, ra, dec) 


