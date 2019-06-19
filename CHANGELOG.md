# Changelog
All notable changes to this project will be documented in this file.


## [0.1.4] - 2019-06-19
### Added
- Solid x-axis lines, corresponding to actual ingress and egress times, can now be
  shown on lightcurve plots in the output PDF from plot.py. Actual ingress and egress lines will 
  only be shown if (PLOT_ACTUAL_INGRESS == True) and (PLOT_ACTUAL_EGRESS ==
True) respectively, in params.py. Predicted ingress and egress lines are now
dashed and will be shown if values are set for those parameters, i.e.
(PREDICTED_INGRESS != None) and (PREDICTED_EGRESS != None).

### Changed
- Fixed bug when unpacking science frames, which calculates the
  observation start time if the GPSSTART header keyword is blank, such as when
SAAO observations are triggered manually.

### Removed


## [0.1.3] - 2019-06-18
### Added
- Support for Python 3
- Binning times to data labels of lightcurve plots, in plot.py output PDF

### Changed
- Plot.py runtime parameter for data directory must now exclude the /photometry sub-directory. This is now in line with SAFPhot.py.

### Removed
