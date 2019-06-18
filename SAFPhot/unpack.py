from os.path import join, exists, basename
from os import makedirs
from astropy.time import Time, TimeDelta
from astropy import coordinates as coord, units as u
from astropy.io import fits
from copy import copy
from glob import glob

class Mapper():
    def __init__(self, hdr, p, keylist):
        for key in keylist:
            try:
                setattr(self, key.lower(), hdr[getattr(p, key)])
            except:
                setattr(self, key.lower(), getattr(p, key))
            try:
                setattr(self, key.lower()+'_com',
                        hdr.get_comment(getattr(p,key)))
            except:
                pass
 

def get_airmass(jd, ra, dec, loc):
    
    #Get time in correct format
    time = Time(jd, format='jd', scale='utc', location=loc)
    
    #Get object sky coords in correct format
    coords = coord.SkyCoord(ra, dec, unit=(u.hourangle, u.deg), frame='icrs')
    
    #Convert coords to AltAz
    altaz = coords.transform_to(coord.AltAz(obstime=time,location=loc))

    #Get airmass
    airmass = altaz.secz.value

    return airmass

def correct_time(header, frame_num, m, deadtime=0.00676):
    '''Function to correct time of each frame to mid-exposure time'''

    #Load time from header
    t = Time(m.dateobs, format='isot', scale='utc')
    
    #Calculate centre of exposure time for a given frame in data cube
    dt = TimeDelta(val=((frame_num * (m.exposure + deadtime))
        + ((m.exposure + deadtime) * 0.5)), format='sec')
    return t + dt

def convert_jd_hjd(jd, ra, dec, loc):
   
    #Get RA and DEC
    ra = ra.replace(" ", ":")
    dec = dec.replace(" ", ":")

    #Get object sky coords in correct format
    coords = coord.SkyCoord(ra, dec,
                unit=(u.hourangle, u.deg), frame='icrs')

    #Define JD as time object
    times = Time(jd, format='jd', scale='utc', location=loc)

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
    times = Time(jd, format='jd', scale='utc', location=loc)

    #Define light travel time
    ltt_bary = times.light_travel_time(coords)

    #Correct JD to BJD
    bjd = times.tdb + ltt_bary
    return bjd.jd

def unpack_reduce(files, calframes, params, verbose=True):

    #prepare for unpacking process
    master_outdir = join(params.out_dir , params.red_dir) 

    #Retrieve Earth coords of telescope, use SALT
    loc = coord.EarthLocation.of_site('SALT')

    for file_, target, filt in zip(files.target, files.target_name,
            files.target_filter):    

        if verbose: print("Unpacking %s: %s " % (target, file_))

        #Create directory within reduction subfolder
        outdir = join(master_outdir, target)
        outdir = outdir.replace(' - ', '_')
        outdir = outdir.replace(' ', '_')
        outdir = outdir.replace('(', '').replace(')','')
        outdir = outdir.replace('\'', '_prime')

        if not exists(outdir): 
            makedirs(outdir)
            if verbose: print("%s folder created." % outdir)
            
        #Open master files
        f = fits.open(file_) 
        prihdr = copy(f[0].header) 
       
        #Try and map parameters to header keywords otherwise set the keyword
        keylist = {'ra', 'dec', 'dateobs', 'exposure'}
        m = Mapper(prihdr, params, keylist)

        #If GPSSTART time is missing, calculate it from time file was written
        if (m.dateobs == '', m.dateobs == 'NA'):
            frame_time = Time([prihdr['FRAME']], format='isot', scale='utc',
                    precision=7)
            dt_exp = TimeDelta(val=m.exposure, format='sec')
            cal_gps_time = (frame_time - dt_exp).isot[0]
            prihdr['GPSSTART'] = cal_gps_time
        
        #Counter to track how many files were skipped
        count_skip = 0 

        #Iterate through individual HDUs of master file
        for count in range(0, f[0].data.shape[0]):
            
            fname = basename(file_).replace('.fits', '.%04d.fits' % (count+1))

            if not exists(join(outdir, fname)): 

                #Reduce data
                red_data = ( f[0].data[count, :, :] - calframes['bias'] ) / calframes[filt]
            
                #Create new header
                temp_header = copy(prihdr)
                newtime = correct_time(temp_header, count, m)        
                temp_header['JD'] = newtime.jd
                temp_header['HJD'] = convert_jd_hjd(newtime.jd, m.ra, m.dec, loc)
                temp_header['BJD'] = convert_jd_bjd(newtime.jd, m.ra, m.dec, loc)
                temp_header['AIRMASS'] = get_airmass(newtime.jd, m.ra, m.dec, loc)
            
                #Write HDU as its own FITS
                hdu = fits.PrimaryHDU(red_data, header=temp_header)
                hdu.writeto(join(outdir, fname))
                f.close()

            else: count_skip += 1

        if count_skip > 0: print("%i files skipped because they already exist."
                % count_skip)

    print("Reduction and unpacking complete.")
