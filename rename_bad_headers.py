import sys

from astropy.io import fits
from copy import copy
from os.path import basename

'''
name='../SAAO_september_2017/reduced/NG2132+0248.027823_z_prime_22nd_1.0m/SHA_20170922.0010.fits'
#name = 'SHD_20170922.0001.fits'

f = fits.open(name)
f_hdr = copy(f[0].header)
f.close()

print (repr(f_hdr))
'''

sci_name = ('/scratch/ngts/lr182/SAAO_september_2017/reduced/NG2142+0826.033774_v_1st_1.0m'\
        '/SHA_20171001.0001.fits')
print sci_name

g = fits.open(sci_name)
g_hdr = copy(g[0].header)
g_data = copy(g[0].data[:,:,:])
g.close()

g_hdr['GPSSTART'] = 'NA'

hdu = fits.PrimaryHDU(g_data, header=g_hdr)
hdu.writeto(sci_name, overwrite=True)


'''
for x in range(23, 28):

    sci_name = 'SHD_20170922.00' + str(x)+'.fits'

    g = fits.open(sci_name)
    g_hdr = copy(g[0].header)
    g_data = copy(g[0].data[:,:,:])
    g.close()

    g_hdr['OBJECT'] = 'NG2132+0248_027823'
    g_hdr['OBJEPOCH'] = '2000'
    g_hdr['OBJEQUIN'] = '2000'
    g_hdr['OBJRA'] = '21:37:17'
    g_hdr['OBJDEC'] = '02:19:37'
    g_hdr['OBSTYPE'] = 'object'
    

    new_name = basename(sci_name).replace('.fits', '_fixed_hdr.fits')
    hdu = fits.PrimaryHDU(g_data, header=g_hdr)
    hdu.writeto(new_name, overwrite=True)
    '''
