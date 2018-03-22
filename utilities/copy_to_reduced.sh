#Copy science images to reduce directory for processing
#And drop in appropriate calibration frames

dir_=NOI_102040_3rd_v

cp -r $dir_ ../reduced/
cp ../flats/flats_28th_v/* ../flats/flats_2nd_v/* ../flats/flats_3rd_v/* \
    ../reduced/$dir_
cp ../biases/biases_25th/* ../biases/biases_3rd/* \
    ../reduced/$dir_
cp /scratch/ngts/lr182/SAAO_scripts/plot.py \
    ../reduced/$dir_
#cp /scratch/ngts/lr182/SAAO_scripts/utilities/sync_to_opis.sh \
#        ../reduced/$dir_/reduction/

