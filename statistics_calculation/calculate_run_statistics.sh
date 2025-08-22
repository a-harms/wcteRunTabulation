#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset    
#set -o xtrace

# input and output directories for the python scripts
calib_dir=/data/calib/
plots_outdir=./plots_outdir/

# input and output directories for runs and run statistics 
mkdir -p ./stats_output_files
time=$(date '+%F_%H-%M-%S')
stats_output_file='./stats_output_files/stats_output_file_'${time}'.csv'
#input_file="pos_and_neg_sf.csv"
input_file="new.csv"



# activate the virtual environment to run the python scripts
source ./.venv/bin/activate

# initialize start and end lines for iterating through input_file based on command line arguments
start_line=$1
end_line=$2

# write column headings to stats output file
echo 'VME run number,Number of spills,Number of events,Muon entries,Pion entries,Electron entries,Average momentum,Muon momentum,Pion momentum,Muons/spill,Pions/spill,Events/spill,Muon mean time,Pion mean time',Electron mean time > $stats_output_file

sed -n "${start_line},${end_line}p" $input_file | grep -v '^#' | while IFS= read -r line; do
	vme_run_num=$(awk -F, '{print $1}' <<< $line)
	upper_pion_cut=$(awk -F, '{print $2}' <<< $line)
	lower_muon_cut=$(awk -F, '{print $3}' <<< $line)
	upper_muon_cut=$(awk -F, '{print $4}' <<< $line)

	# run wcte_vme_plots_new_arguments.py (make the plots) and keep track of the number of spills
	echo "Running python wcte_vme_plots_new_arguments_2.py for vme run number:" $vme_run_num

	plots_new_output=$(python wcte_vme_plots_new_arguments.py $vme_run_num $upper_pion_cut $lower_muon_cut $upper_muon_cut $calib_dir $plots_outdir)

	num_spills=$( grep 'Total number of spills' <<< $plots_new_output| sed 's/\[INFO\] Total number of spills: //')
	num_events=$( grep 'Total events' <<< $plots_new_output| sed 's/\[INFO\] Total events: //')

	# run wcte_vme_momentum_new_arguments.py
	echo "Running python wcte_vme_momentum_new_arguments.py for vme run number:" $vme_run_num
	momentum_new_output=$(python wcte_vme_momentum_new_arguments.py $vme_run_num $plots_outdir)

	# extracting the muon and pion statistics
	muon_entries=$(awk '/Muon entries/ {print $7}' <<< $momentum_new_output)
	pion_entries=$(awk '/Pion entries/ {print $7}' <<< $momentum_new_output)
	electron_entries=$(awk '/Electron entries/ {print $7}' <<< $momentum_new_output)

	# extracting time of flights
	muon_mean_time=$(awk '/Muon mean time/ {print $4}' <<< $momentum_new_output)
	pion_mean_time=$(awk '/Pion mean time/ {print $4}' <<< $momentum_new_output)
	electron_mean_time=$(awk '/Electron mean time/ {print $4}' <<< $momentum_new_output)

	# calculating the average momentum
	muon_momentum=$(awk '/p=/ {print $15}' <<< $momentum_new_output | tr -d p= | awk 'NR==1')
	pion_momentum=$(awk '/p=/ {print $15}' <<< $momentum_new_output | tr -d p= | awk 'NR==2')
	combined_momentum=$(echo "scale=2 ; $muon_momentum + $pion_momentum" | bc)
	avg_momentum=$(echo "scale=2 ; $combined_momentum / 2" | bc)

	# calculating per spill statistics
	muons_per_spill=$(echo "scale=2 ; $muon_entries / $num_spills" | bc)
	pions_per_spill=$(echo "scale=2 ; $pion_entries / $num_spills" | bc)
	events_per_spill=$(echo "scale=2 ; $num_events / $num_spills" | bc)

	#writing run information to stats output file
	echo "${vme_run_num},${num_spills},${num_events},${muon_entries},${pion_entries},${electron_entries},${avg_momentum},${muon_momentum},${pion_momentum},${muons_per_spill},${pions_per_spill},${events_per_spill},${muon_mean_time},${pion_mean_time},${electron_mean_time}" >> $stats_output_file

done


# deactivate the virtual environment to run the python scripts
deactivate
