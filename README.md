
# Sub Directory Descriptions

## run_lister

Contains run_lister.py script used to take in csv files derived from "WCTE Calibration and Beam Run tracker" and "Beam Monitor Run Log" google sheets and filter the runs by date, beam momentum and trigger_config.

## statistics_calculation

Contains the calculate_run_statistics.sh script which automates statistics extraction of vme data using the python scripts wcte_vme_plots_new_arguments.py and wcte_vme_momentum_new_arguments.py (altered versions of Bruno's Code).

calcualte_run_statistics.sh takes in a csv file to know which vme runs to process along with their respective cuts. An example csv file used for low momentum runs, pos_and_neg_sf.csv can be seen included in this directory.
