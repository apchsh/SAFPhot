# Script to convert JD in SAAO pipeline output .fits to HJD using loc of SALT #

import numpy as np
from astropy import time, coordinates as coord, units as u
from astropy.table import Table, Column
#from astropy.io import ascii

#Define input file
#f_in='/scratch/ngts/lr182/SAAO_september_2017/reduced/NG2058-0248.003718_z_prime_23rd_1.0m/reduction/NG2058-0248.003718_comparison_mean.fits'
#f_in='/scratch/ngts/lr182/SAAO_september_2017/reduced/NG2058-0248.003718_v_23rd_1.9m/reduction/NG2058-0248.003718_comparison_mean.fits'
#f_in='/scratch/ngts/lr182/SAAO_september_2017/reduced/NG2058-0248.003718_b_27th_1.0m/reduction/NG2058-0248.003718_comparison_mean.fits'
f_in='/scratch/ngts/lr182/SAAO_september_2017/reduced/NG2058-0248_003718_NGTS_data_file.fits'

#Get co-ords of observatory
loc = coord.EarthLocation.of_site('SALT')

#Define RA and DEC of object
RA = "20:53:29.3"
DEC = "-01:37:03.73"
coords = coord.SkyCoord(RA, DEC,
    unit=(u.hourangle, u.deg), frame='icrs')

#Load data
t1 = Table.read(f_in)
jd = np.array(t1['HJD'])
flux = np.array(t1['Relative flux'])
print t1

#Define JD as time object
times = time.Time(jd, format='jd',
    scale='utc', location=loc)

#Define light travel time
ltt_helio = times.light_travel_time(coords, 'heliocentric')

#Correct JD to HJD
hjd = times.utc + ltt_helio
hjd = hjd.jd

#Add HJD column, remove JD
t1.add_column(Column(hjd, name='HJD', dtype=np.float64), index=0)
t1.remove_column('JD')
#t1.rename_column('HJD_new', 'HJD')

#Save updated table as ascii file
f_out = f_in.replace('.fits', '_hjd.dat')
t1.write(f_out, format='ascii', overwrite=True)
#ascii.write(t1, f_out)

'''
#Save updated table as new fits file
f_out = f_in.replace('.fits', '_hjd.fits')
print t1
t1.write(f_out, overwrite=True)
'''
