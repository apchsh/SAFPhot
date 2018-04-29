from os.path import join, exists, basename
from os import makedirs
from astropy.time import Time, TimeDelta
from astropy import coordinates as coord, units as u
from astropy.io import fits
from copy import copy
from glob import glob

def difheader(head1, head2): 
    '''Function for checking the difference between two headers. Not used for
    correction. Just for comparison'''

    #get a list of keys 
    key1 = []
    for key in head1: key1.append(key)
    key2 = [] 
    for key in head2: key2.append(key) 

    #make a copy of key1 to iterate through
    temp = copy(key1)
    for key in temp:
        if (key in key1) and (key in key2):
            key1.remove(key); key2.remove(key)

    return key1, key2 

def correct_time(header, frame_num):
    '''Function to fix the UTC time for each frame.'''

    #Load time from header
    t = Time([header['GPSSTART']], format='isot', scale='utc')
    #Create the time delta object which corrects the exposure time
    dt = TimeDelta(val=frame_num*(header['EXPOSURE']+ 0.00676) +
    header['EXPOSURE'] * 0.5, format='sec')
    return t + dt

def convert_jd_hjd(jd, ra, dec, loc):
   
    #Get RA and DEC
    ra = ra.replace(" ", ":")
    dec = dec.replace(" ", ":")

    #Get object sky coords in correct format
    coords = coord.SkyCoord(ra, dec,
                unit=(u.hourangle, u.deg), frame='icrs')

    #Define JD as time object
    times = Time(jd, format='jd',
                scale='utc', location=loc)

    #Define light travel time
    ltt_helio = times.light_travel_time(coords, 'heliocentric')

    #Correct JD to HJD
    hjd = times.utc + ltt_helio
    return hjd.jd

def convert_jd_bjd(jd, ra, dec, loc):
   
    #Get RA and DEC
    ra = ra.replace(" ", ":")
    dec = dec.replace(" ", ":")

    #Get object sky coords in correct format
    coords = coord.SkyCoord(ra, dec,
                unit=(u.hourangle, u.deg), frame='icrs')

    #Define JD as time object
    times = Time(jd, format='jd',
                scale='utc', location=loc)

    #Define light travel time
    ltt_bary = times.light_travel_time(coords)

    #Correct JD to BJD
    bjd = times.tdb + ltt_bary
    return bjd.jd

def unpack_reduce(files, calframes, verbose=True, ra=None, dec=None):

    #prepare for unpacking process
    master_outdir = join(files.dir_ , 'reduction') 

    #Retrieve Earth coords of telescope, use SALT
    loc = coord.EarthLocation.of_site('SALT')

    for file_, target, filt in zip(files.target, files.target_name,
            files.target_filter):    

        if verbose: print "Unpacking %s: %s " % (target, file_)

        #Create directory within reduction subfolder
        outdir = join(master_outdir, target)
        outdir = outdir.replace(' - ', '_')
        outdir = outdir.replace(' ', '_')
        outdir = outdir.replace('(', '').replace(')','')
        outdir = outdir.replace('\'', '_prime')

        if not exists(outdir): 
            makedirs(outdir)
            if verbose: print "%s folder created." % outdir
            
        #Open master files
        f = fits.open(file_) 
        prihdr = copy(f[0].header) 
        #If GPSSTART time is missing, calculate it
        if (prihdr['GPSSTART'] == '', prihdr['GPSSTART'] == 'NA'):
            frame_time = Time([prihdr['FRAME']], format='isot', scale='utc')
            dt_exp = TimeDelta(val=prihdr['EXPOSURE'], format='sec')
            cal_gps_time = (frame_time - dt_exp).isot[0]
            prihdr['GPSSTART'] = cal_gps_time

        for count in range(0, f[0].data.shape[0]):

            temp_header = copy(prihdr)
            red_data = ( f[0].data[count, :, :] - calframes['bias'] ) / calframes[filt]

            newtime = correct_time(temp_header, count)        
            temp_header['JD'] = newtime.jd[0]

            if (ra is not None) and (dec is not None):
                #Overwrite header RA and DEC with runtime input params
                temp_header['OBJRA'] = ra
                temp_header['OBJDEC'] = dec
            temp_header['HJD'] = convert_jd_hjd(newtime.jd[0],
                                temp_header['OBJRA'], temp_header['OBJDEC'], loc)
            temp_header['BJD'] = convert_jd_bjd(newtime.jd[0],
                                temp_header['OBJRA'], temp_header['OBJDEC'], loc)

            fname = basename(file_).replace('.fits', '.%04d.fits' % count)
            hdu = fits.PrimaryHDU(red_data, header=temp_header)
            hdu.writeto(join(outdir, fname), clobber=True)
        f.close()

    print "Reduction and unpacking complete." 
