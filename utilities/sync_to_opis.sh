#Copy plots and data files to OPIS

NOI_name="NOI-102040"

rsync -avr *comparison_mean.fits \
    *by_itself.png *vs_other_comps.png *comparison*.png \
    *_field.png *.log *_fwhm.dat \
    lr182@ngtshead.warwick.ac.uk:/ngts/opis/uploads/$NOI_name
