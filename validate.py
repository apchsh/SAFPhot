'''

Parameter file for the SAFPhot pipeline.

The file contains the params class which includes most options that can be
modified in SAFPhot, controlling the background subtraction, aperture 
photometry and the structure of the output files. 

The main pipeline script SAFPhot.py imports the class and then the parameters
can be set. Once the create method has been run over the 

'''

class KeyNotKnownError(Exception):
    pass

class KeyMissingError(Exception):
    pass

class KeyValueError(Exception):
    pass 

def validate_back_method():
    return True

def validate_list_int():
    return True 


class Validator(): 
       

    keylist = {"BACK_METHOD":validate_back_method(), 
               "BOX_WIDTH":validate_list_int(),
               "RADII":validate_list_int()}
    
    def __init__(self, pardict): 

        set_pardict = set(pardict)
        set_keylist = set(self.keylist)
 
        if set_pardict == set_keylist: 

            for key in pardict_: 

                if self.keylist[key](pardict[key]):

                    setarrt(self, key.lower_case(), pardict[key])

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

