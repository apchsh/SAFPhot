'''

Parameter file for the SAFPhot pipeline.

The file contains the params class which includes most options that can be
modified in SAFPhot, controlling the background subtraction, aperture 
photometry and the structure of the output files. 

The main pipeline script SAFPhot.py imports the class and then the parameters
can be set. Once the create method has been run over the 

'''

import fitsio 

from os.path import isfile 

class KeyNotKnownError(Exception):
    pass

class KeyMissingError(Exception):
    pass

class KeyValueError(Exception):
    pass 

#Functions to validate the keywords 
def tuple_two(num):
    
    if type(num) == tuple:
        if len(num) == 2:
            return True
        else: return False

def float_positive(num):
    
    if type(num) == float:
        if num >= 0:
            return True
        else: return False 

def float_or_int_positive(num):
    
    if type(num) == float or type(num) == int:
        if num >= 0:
            return True
        else: return False 

def int_positive(num):

    if type(num) == int:
        if num >= 0:
            return True
    else: return False 
    
def list_int(list_):

    result = True
    for item in list_: 
        if not(type(item) == int):
            result = False 
        
    return result 

def list_float(list_):
    
    result = True
    for item in list_:
        if not(type(item) == float):
            result = False

    return result

def check_string(string):

    if type(string) == str:
        return True
    else: return False 

def string_or_float(value):

    if check_string(value) or type(value) == float:
        return True 
    else: return False 

def string_or_int(value):
    if check_string(value) or type(value) == int:
        return True
    else: return False

class Validator(object): 
       
    _keylist = { "PLATESCALE":float_positive,
                "FIELD_ANGLE":float_positive,
                "RADII":list_float,
                "BOX_SIZE":list_int,
                "FILTER_SIZE":list_int,
                "SOURCE_THRESH":float_or_int_positive,
                "BKG_APP_RAD":float_or_int_positive,
                "NUM_BKG_APPS":float_or_int_positive,
                "DATEOBS":check_string, 
                "OBSERVER":check_string,
                "OBSERVATORY":check_string,
                "TELESCOPE":check_string,
                "INSTRUMENT":check_string,
                "FILTERA":check_string,
                "FILTERB":check_string,
                "TARGET":check_string,
                "EXPOSURE":check_string,
                "RA":string_or_float,
                "DEC":string_or_float,
                "EPOCH":check_string,
                "EQUINOX":check_string,
                "VBIN":string_or_int,
                "HBIN":string_or_int,
                "PREAMP":string_or_float,
                "AIRMASS":check_string, 
                "JD":check_string,
                "HJD":check_string,
                "BJD":check_string,
                "LAT":string_or_float,
                "LON":string_or_float,
                "ALT":string_or_float,
                "ANALYSER":check_string,
                "OUT_DIR":check_string,
                "RED_DIR":check_string,
                "PHOT_DIR":check_string,
                "PHOT_PREFIX":check_string,
                "RED_PREFIX":check_string,
                "BIASID":check_string,
                "FLATID":check_string,
                "OBSTYPE":check_string,
                "TARGET_OBJECT_NUM":int_positive,
                "COMPARISON_OBJECT_NUMS":list_int,
                "NORM_FLUX_UPPER":float_or_int_positive,
                "NORM_FLUX_LOWER":float_or_int_positive,
                "PLOT_TIME_FORMAT":check_string,
                "BINNING":int_positive,
                "PREDICTED_INGRESS":float_positive,
                "PREDICTED_EGRESS":float_positive,
                "ACTUAL_INGRESS":float_positive,
                "ACTUAL_EGRESS":float_positive,
                "NCOLS":int_positive,
                "NROWS":int_positive,
                "FIGSIZE":tuple_two,
                "DPI":int_positive,
                "PHOT_FILE_IN":check_string,
                "FIELD_IMAGE_IN":check_string
               }

    def __init__(self, pardict): 

        set_pardict = set(pardict)
        set_keylist = set(self._keylist)
 
        if set_pardict == set_keylist: 

            for key in pardict: 

                if self._keylist[key](pardict[key]):

                    setattr(self, key.lower(), pardict[key])

                else:

                    raise KeyValueError("%s is not a valid value for %s" %
                                            (pardict[key], key))

        else: 

            if len(set_pardict) > len(set_keylist):
                raise KeyNotKnownError("Parameters not recognised: %s" % 
                        ', '.join(set_pardict - set_keylist))    
            else:
                raise KeyMissingError("The following keys are required: %s" % 
                        ', '.join(set_keylist - set_pardict))


class ValidateFits(object):

    params = [] #replaced by Validator object

    mandatoryKeys = [
            "EXPOSURE"         
            ]

    def __init__(self, par):

        if type(par).__name__ == "Validator":
                self.params = par

        else: 
            raise ValueError("Invalid parameter object passed.")


    def check(self, file_):

        valid = True

        if isfile(file_):

            with fitsio.FITS(file_) as f: 

                header = f[0].read_header() 
                fitsKeys = header.keys() 
    
                for key in self.mandatoryKeys:
                    
                    paramName = self.params.__getattribute__(key.lower())

                    if not(paramName in fitsKeys): valid = False

        else:

            raise ValueError("Fits file %s does not exist." % file_) 

        return valid 


