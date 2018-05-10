from validate import Validator # SAFPhot script

def get_params():

    #create the parameter dictionary
    params = {}

    #TELESCOPE/OBSERVING PARAMETERS
    params["PLATESCALE"] = 0.167 # platescale [arcsec/pix]
    params["FIELD_ANGLE"] = 180.0 # rotate the example field image by [deg]
    
    #PHOTOMETRY PARAMETERS 
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

    #REDUCTION AND PHOTOMETRY OUTPUT KEYWORDS 
    params["OUT_DIR"] = "" # output directory, if blank the input dir is used 
    params["RED_DIR"] = "reduction/" # sub-directory of output folder in which to store 
                                    # reduced files
    params["PHOT_DIR"] = "photometry/" # sub-directory of input folder in which to store
                                    # photometric files
    params["PHOT_PREFIX"] = "SAAO_" # prefix to attach to the photometric output
    params["RED_PREFIX"] = "CAL_" # prefix to attach to reduction output 
    params["BIASID"] = "BIAS" # keyword to id BIAS frames 
    params["FLATID"] = "FLAT" # keyword to id FLAT frames

    #PLOT PARAMETERS
    params["TARGET_OBJECT_NUM"] = 1         # target number from field image [int]
    params["COMPARISON_OBJECT_NUMS"] = [0, 2] # comparison numbers [int,int,..]
    params["NORM_FLUX_UPPER"] = 1.2   # normalised flux upper filter limit
    params["NORM_FLUX_LOWER"] = 0     # normalised flux lower filter limit
    params["PLOT_TIME_FORMAT"] = "JD"       # time format for plotting [JD,HJD,BJD]
    params["BINNING"] = 10*60               # bin time for flightcurves [seconds]
    params["PREDICTED_INGRESS"] = 2458155.36 # in format of "PLOT_TIME_FORMAT"
    params["PREDICTED_EGRESS"] = 2458155.46 # in format of "PLOT_TIME_FORMAT"
    params["ACTUAL_INGRESS"] = 2458155.36   # in format of "PLOT_TIME_FORMAT"
    params["ACTUAL_EGRESS"] = 2458155.46    # in format of "PLOT_TIME_FORMAT"
    params["NCOLS"] = 2                     # max number of plot columns per page [int]
    params["NROWS"] = 3                     # max number of plot rows per page [int]
    params["FIGSIZE"] = (12,8)              # figure size in inches (width,height)/DPI
    params["DPI"] = 100                     # resolution in dots per inch [int]
    params["PHOT_FILE_IN"] = "*_phot.fits"  # photometry input file
    params["FIELD_IMAGE_IN"] = "*_field.png"    # field image input file
    
    return Validator(params) 

if __name__ == "__main__":

    params = get_params()


