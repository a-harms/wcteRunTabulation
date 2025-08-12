#!/usr/bin/env bash

# the same as the input file for calculate_run_statistics.sh
input_file="./pos_and_neg_sf.csv"


mkdir -p './pdf_plots'

> ./pdf_plots/run_list.txt

grep -v '^#' < $input_file | while FPS= read -r line; do
	vme_run_num=$(awk -F, '{print $1}' <<< $line)
	echo './pdf_plots/plot_'$vme_run_num'.pdf' >> ./pdf_plots/run_list.txt

	vme_run_num_plot='./plots_outdir/run'${vme_run_num}'/h_run'${vme_run_num}'_act2_vs_t0t1_e-veto_visible_cuts.png'

	vme_run_num_pdf='./pdf_plots/plot_'$vme_run_num'.pdf'

	img2pdf $vme_run_num_plot --output $vme_run_num_pdf
done

cat ./pdf_plots/run_list.txt | xargs gs -q -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress -sOutputFile=merged.pdf
