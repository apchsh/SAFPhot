import numpy as np
import matplotlib.pyplot as plt
from astropy.stats import sigma_clip
from os.path import join
from astropy.table import Table
import warnings

warnings.simplefilter('ignore')

def bin_to_size(data, num_points_bin):
    num_bins = int(len(data) / num_points_bin)
    return rebin(data[0:num_bins*num_points_bin], num_bins)

def rebin(a, *args):
    """From the scipy cookbook on rebinning arrays
    rebin ndarray data into a smaller ndarray of the same rank whose dimensions
    are factors of the original dimensions. eg. An array with 6 columns and 4 
    rows can be reduced to have 6,3,2 or 1 columns and 4,2 or 1 rows.
    example usages:
    a=rand(6,4); b=rebin(a,3,2)
    a=rand(6); b=rebin(a,2)"""
    shape = a.shape
    lenShape = len(shape)
    factor = np.asarray(shape)/np.asarray(args)
    evList = ['a.reshape('] + \
             ['args[%d],factor[%d],'%(i,i) for i in range(lenShape)] + \
             [')'] + ['.sum(%d)'%(i+1) for i in range(lenShape)] + \
             ['/factor[%d]'%i for i in range(lenShape)]
    return eval(''.join(evList))

def fold(jd, period, epoch):
    jd = ((jd - epoch) / period) % 1
    return jd


#Load LC 1 data
dir_1 = ""
file_1 = ""
band_1 = "V"
t1 = Table.read(join(dir_1, file_1))
jd_1 = np.array(t1['JD'])
flux_1 = np.array(t1['Relative flux'])

#Load LC 2 data
dir_2 = ""
file_2 = ""
band_2 = "z'"
t2 = Table.read(join(dir_2, file_2))
jd_2 = np.array(t2['JD'])
flux_2 = np.array(t2['Relative flux'])

#System parameters
obj_id = "NOI_XXX"
period = 1.234
epoch = 2457393.939572

#Fold LCs
ph_1 = fold(jd_1, period, epoch)
ph_2 = fold(jd_2, period, epoch)
ph_1[ph_1 > 0.8] -=  1.0
ph_2[ph_2 > 0.8] -=  1.0

#Remove offset from jd if plotting jd on x-axis
off = np.floor(np.min(jd_1))
jd_1 -= off
jd_2 -= off

#Line up curves with phase offset
ph_2 += 0.0

# Binning
b = 10*60 #sec

#Plot
plt.figure(1, figsize=(8,6), dpi=100)
plt.scatter(ph_2, flux_2, alpha=0.5, c='g', label=band_2)
plt.scatter(ph_1, flux_1, alpha=0.5, c='r', label=band_1)
plt.title(obj_id)
plt.xlabel('Phase')
plt.ylabel('Relative flux')
plt.legend(loc=2)
plt.autoscale(enable=True, axis='y')

#Save plots as png
png_name = obj_id + "_multiple_lcs.png"
plt.savefig(png_name)
plt.show()
plt.close()
