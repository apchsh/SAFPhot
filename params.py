from validate import Validator

def get_params():

    #create the parameter dictionary
    params = {}

    #OBSERVING KEYWORDS
    params["PLATESCALE"] = 0.167 #arcsec / pix 
    params["FIELD_ANGLE"] = 180.0 #rotates the example field image
    
    #PHOTOMETRY KEYWORDS 
    params["RADII"] = [3.0, 3.1]
    params["BOX_SIZE"] = [16, 32]
    params["FILTER_SIZE"] = [3.0] 
    params["SOURCE_THRESH"] = 7.0

    #HEADER KEYWORDS 
    #Here you can either pass in the keyword name in the SAAO observation file or explicitly set the value of the keyword. The default behaviour of SAFPhot is to check the first fits file containing observations to see if the keyword exists and if not it sets the value with the one specified. 

    params["DATE-OBS"] = "GPSSTART"
    params["OBSERVER"] = "CHAUSHEV" 
    params["OBSERVATORY"] = "OBSERVAT"
    params["TELESCOPE"] = "TELESCOP"
    params["INSTRUMENT"] = "INSTURUMT"
    params["FILTERA"] = "FILTERA" #SAAO telescopes have two filters
    params["FILTERB"] = "FILTERB"
    params["TARGET"] = "OBJECT"
    params["EXPOSURE"] = "EXP"

    #optional
    params["RA"] = "RA"
    params["DEC"] = "DEC"
    params["EPOCH"] = "EPOCH"
    params["EQUINOX"] = "EQUINOX" 
    params["VBIN"] = "VBIN"
    params["HBIN"] = "HBIN"
    params["AIRMASS"] = "AIRMASS"
    params["JD"] = "JD"
    params["HJD"] = "HJD"
    params["BJD"] = "BJD"
    params["LAT"] = 0.334
    params["LON"] = 0.334
    params["ALT"] = 300.0
    
    #OUTPUT KEYWORDS 
    params["OUT_DIR"] = "" #output directory, if blank the input dir is used 
    params["RED_DIR"] = "reduction/" #sub-directory of output folder in which to store reduced files
    params["PHOT_DIR"] = "phot/" #sub-directory of input folder in which to store photometric files
    params["PHOT_PREFIX"] = "SAAO_" #prefix to attach to the photometric output
    params["RED_PREFIX"] = "CAL_" #prefix to attach to reduction output 

    return Validator(params) 

if __name__ == "__main__":

    params = get_params()


