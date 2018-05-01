from validate import Validator

def get_params():

    #create the parameter dictionary
    params = {}

    #OBSERVING KEYWORDS
    params["PLATESCALE"] = 0.167 # [arcsec/pix]
    params["FIELD_ANGLE"] = 180.0 # rotate the example field image by [deg]
    
    #PHOTOMETRY KEYWORDS 
    params["RADII"] = [3.0, 3.1]
    params["BOX_SIZE"] = [16, 32]
    params["FILTER_SIZE"] = [3.0] 
    params["SOURCE_THRESH"] = 7.0

    #HEADER KEYWORDS 
    '''Here you can either pass in the keyword name in the SAAO observation file or
    explicitly set the value of the keyword. The default behaviour of SAFPhot is to
    check the first fits file containing observations to see if the keyword exists and
    if not it sets the value with the one specified.'''

    params["DATE-OBS"] = "GPSSTART" # Start date/time of observation
    params["OBSERVER"] = "CHAUSHEV" # Observer name
    params["OBSERVATORY"] = "OBSERVAT" # Observatory
    params["TELESCOPE"] = "TELESCOP" # Telescope
    params["INSTRUMENT"] = "INSTURUMT" # Instrument
    params["FILTERA"] = "FILTERA" # Filter, first wheel
    params["FILTERB"] = "FILTERB" # Filter, second wheel
    params["TARGET"] = "OBJECT" # Target/object name
    params["EXPOSURE"] = "EXP" # Exposure time

    #optional
    params["RA"] = "RA" # RA of target object
    params["DEC"] = "DEC" # DEC of target object
    params["EPOCH"] = "EPOCH" # EPOCH of target coordinates
    params["EQUINOX"] = "EQUINOX" # Equinox of target coordinates
    params["VBIN"] = "VBIN" # CCD vertical bin factor
    params["HBIN"] = "HBIN" # CCD horizontal bin factor
    params["AIRMASS"] = "AIRMASS" # Airmass during observation
    params["JD"] = "JD"
    params["HJD"] = "HJD"
    params["BJD"] = "BJD"
    params["LAT"] = 0.334 # latitude of telescope in Earth geodetic co-ords
    params["LON"] = 0.334 # longitude of telescope in Earth geodetic co-ords
    params["ALT"] = 300.0 # Altitude of telescope in meters
    
    #OUTPUT KEYWORDS 
    params["OUT_DIR"] = "" #output directory, if blank the input dir is used 
    params["RED_DIR"] = "reduction/" #sub-directory of output folder in which to store 
                                    #reduced files
    params["PHOT_DIR"] = "photometry/" #sub-directory of input folder in which to store
                                    #photometric files
    params["PHOT_PREFIX"] = "SAAO_" #prefix to attach to the photometric output
    params["RED_PREFIX"] = "CAL_" #prefix to attach to reduction output 

    return Validator(params) 

if __name__ == "__main__":

    params = get_params()


