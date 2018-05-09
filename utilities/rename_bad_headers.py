# Script to change headers if information has been entered wrong accidentally

import sys
from astropy.io import fits
from copy import copy
from os.path import basename

# Correct wrong observation type, e.g. flat >> object
for x in range(23, 28):
    #Get file handle
    sci_name = 'SHD_20170922.00' + str(x)+'.fits'

    #Open file, copy data
    with fits.open(sci_name) as g:
        g_hdr = copy(g[0].header)
        g_data = copy(g[0].data[:,:,:])

    #Update header keywords
    g_hdr['OBJECT'] = 'NG2132+0248_027823'
    g_hdr['OBJEPOCH'] = '2000'
    g_hdr['OBJEQUIN'] = '2000'
    g_hdr['OBJRA'] = '21:37:17'
    g_hdr['OBJDEC'] = '02:19:37'
    g_hdr['OBSTYPE'] = 'object'
    
    #Write as new file
    new_name = basename(sci_name).replace('.fits', '_fixed_hdr.fits')
    hdu = fits.PrimaryHDU(g_data, header=g_hdr)
    hdu.writeto(new_name, overwrite=True)
