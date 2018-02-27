import numpy as np
import matplotlib.pyplot as plt
import warnings; warnings.simplefilter('ignore')

from astropy.stats import sigma_clip
from os.path import join
from astropy.table import Table
from scipy.io import savemat, loadmat
from glob import glob

#Specify directory and target names
dir_ = 'reduction'
name = 'NG2058-0248.003718'

#Specify Safphot output data files
flux_file = glob(dir_ + '/*obj_flux.mat')[0]
jd_file = glob(dir_ + '/*jd.dat')[0]

flux = loadmat(flux_file)['flux']
jd = np.loadtxt(jd_file)
jd_off = np.floor(np.nanmin(jd))
jd = jd - jd_off

for i in range(0, flux.shape[0], 4):
    print i
    plt.cla()
    plt.figure(1, figsize=(8,6), dpi=100)
    plt.scatter(jd, flux[i, :, :, :][2, :, :][8, :])
    plt.xlabel('JD - %d' %jd_off)
    plt.ylabel('Relative flux')
    plt.savefig(join(dir_, 'raw_object_%d.png' %i))


