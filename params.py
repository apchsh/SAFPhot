from validate import Validator

def get_params():

    #create the parameter dictionary
    params = {}

    #OBSERVING KEYWORDS
    params["PLATESCALE"] = 0.167 # platescale [arcsec/pix]
    params["FIELD_ANGLE"] = 180.0 # rotate the example field image by [deg]
    
    #PHOTOMETRY KEYWORDS 
    params["RADII"] = [3.0, 3.1] # Aperture radii to use
    params["BOX_SIZE"] = [16, 32] # Background estimation box size
    params["FILTER_SIZE"] = [3.0] # Background estimation filter length (boxes)
    params["SOURCE_THRESH"] = 7.0 # Source detection threshold
    params["BKG_APP_RAD"] = 4.0 # Aperture radius to measure background residuals
    params["NUM_BKG_APPS"] = 100 # Num apertures per frame to measure bkg residuals

    #HEADER KEYWORDS 
    '''Here you can either pass in the keyword name contained within the image
    headers or explicitly set the value of the keyword. The default behaviour
    of SAFPhot is to first check whether the keyword is defined within the
    image headers and if so set that value, otherwise it will set the value to
    the one specified.'''
    
    #Setting compulsory
    params["TARGET"] = "OBJECT" # Target/object name
    params["EXPOSURE"] = "EXPOSURE" # Exposure time [s]
    params["RA"] = "OBJRA" # RA of target object [h:m:s]
    params["DEC"] = "OBJDEC" # DEC of target object [d:m:s]
    params["EPOCH"] = "OBJEPOCH" # EPOCH of target coordinates
    params["VBIN"] = "VBIN" # CCD vertical bin factor
    params["HBIN"] = "HBIN" # CCD horizontal bin factor
    params["PREAMP"] = "PREAMP" # Preamplifier gain [e-/ADU]
    params["JD"] = "JD" # Julian Date
    params["DATEOBS"] = "GPSSTART" # Start time of obs [YYYY-MM-DDTHH:MM:SS.ss]
    params["OBSERVER"] = "OBSERVER" # Observer name
    params["OBSERVATORY"] = "SAAO" # Observatory
    params["TELESCOPE"] = "TELESCOP" # Telescope
    params["INSTRUMENT"] = "INSTRUME" # Instrument
    params["FILTERA"] = "FILTERA" # Filter, first wheel
    params["FILTERB"] = "FILTERB" # Filter, second wheel
    params["OBSTYPE"] = "OBSTYPE" #keyword for observation type
    
    #Setting optional
    params["ANALYSER"] = "CHAUSHEV" # Person who analysed the data
    params["EQUINOX"] = "OBJEQUIN" # Equinox of target coordinates
    params["AIRMASS"] = "AIRMASS" # Airmass during observation
    params["HJD"] = "HJD" # Heliocentric Julian Date
    params["BJD"] = "BJD" # Barycentric Julian Date
    params["LAT"] = 0.334 # latitude of telescope in Earth geodetic co-ords
    params["LON"] = 0.334 # longitude of telescope in Earth geodetic co-ords
    params["ALT"] = 300.0 # Altitude of telescope [meters]

    #OUTPUT KEYWORDS 
    params["OUT_DIR"] = "" # output directory, if blank the input dir is used 
    params["RED_DIR"] = "reduction/" # sub-directory of output folder in which to store 
                                    # reduced files
    params["PHOT_DIR"] = "photometry/" # sub-directory of input folder in which to store
                                    # photometric files
    params["PHOT_PREFIX"] = "SAAO_" # prefix to attach to the photometric output
    params["RED_PREFIX"] = "CAL_" # prefix to attach to reduction output 
    params["BIASID"] = "BIAS" # keyword to id BIAS frames 
    params["FLATID"] = "FLAT" # keyword to id FLAT frames

    return Validator(params) 

if __name__ == "__main__":

    params = get_params()


