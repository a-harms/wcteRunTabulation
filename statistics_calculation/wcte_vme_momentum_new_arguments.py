#!/usr/bin/env python3

# ================= Momentum Reconstruction =================
# Bruno Ferrazzi (bferrazzi@uregina.ca)
# April 2025

import os
import ROOT
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

#additions
import sys


def vme_momentum_calculator(run_number, base_input_dir, base_output_dir):


    # Paths based on run number
    input_folder  = os.path.join(base_input_dir,  f"run{run_number}")
    output_folder = os.path.join(base_output_dir, f"run{run_number}")
    if not os.path.isdir(input_folder):
        raise FileNotFoundError(f"Input folder does not exist: {input_folder}")
    os.makedirs(output_folder, exist_ok=True)

    input_file = os.path.join(input_folder, f"hist_run{run_number}.root")
    output_fig = os.path.join(output_folder,  f"tof_fits_run{run_number}.png")
    
    # Open ROOT file and retrieve histograms
    f = ROOT.TFile.Open(input_file)
    if not f or f.IsZombie():
        raise FileNotFoundError(f"Cannot open ROOT file: {input_file}")
    hist_raw = f.Get("t0t1_raw")
    hist_ele = f.Get("t0t1_ele")
    hist_pi  = f.Get("t0t1_pi")
    hist_mu  = f.Get("t0t1_mu")

    # Entries count
    n_ele = hist_ele.GetEntries()
    n_mu  = hist_mu.GetEntries()
    n_pi  = hist_pi.GetEntries()
    n_ru  = hist_raw.GetEntries()

    # Convert TH1 to numpy arrays
    def hist_to_arrays(hist):
        nbins = hist.GetNbinsX()
        x = np.array([hist.GetBinCenter(i+1)   for i in range(nbins)])
        y = np.array([hist.GetBinContent(i+1)  for i in range(nbins)])
        yerr = np.array([hist.GetBinError(i+1) for i in range(nbins)])
        yerr[yerr == 0] = 1.0
        return x, y, yerr

    x_ele, y_ele, yerr_ele = hist_to_arrays(hist_ele)
    x_mu,  y_mu,  yerr_mu  = hist_to_arrays(hist_mu)
    x_pi,  y_pi,  yerr_pi  = hist_to_arrays(hist_pi)
    x_ru,  y_ru,  yerr_ru  = hist_to_arrays(hist_raw)

    # Gaussian model and fit
    def gauss(x, A, mu, sigma):
        return A * np.exp(-0.5 * ((x - mu) / sigma)**2)

    def fit_gauss(x, y, yerr):
        p0 = [y.max(), x[np.argmax(y)], np.std(x)]
        popt, pcov = curve_fit(gauss, x, y, sigma=yerr, absolute_sigma=True, p0=p0)
        yfit = gauss(x, *popt)
        chi2 = np.sum(((y - yfit) / yerr)**2)
        ndf = len(x) - len(popt)
        return popt, np.sqrt(np.diag(pcov)), chi2/ndf

    # Perform fits for electron, muon, pion
    ele_popt, ele_perr, chi2_ele = fit_gauss(x_ele, y_ele, yerr_ele)
    mu_popt,  mu_perr,  chi2_mu  = fit_gauss(x_mu,  y_mu,  yerr_mu)
    pi_popt,  pi_perr,  chi2_pi  = fit_gauss(x_pi,  y_pi,  yerr_pi)

    # Extract fit centers and widths
    mu_ele    = ele_popt[1]
    sigma_ele = abs(ele_popt[2])
    mu_mu     = mu_popt[1]
    sigma_mu  = abs(mu_popt[2])
    mu_pi     = pi_popt[1]
    sigma_pi  = abs(pi_popt[2])

    # Count "good" events within ±2σ
    def count_good(hist, mu, sigma):
        low_edge, high_edge = mu - 2*sigma, mu + 2*sigma
        low_bin  = hist.FindBin(low_edge)
        high_bin = hist.FindBin(high_edge)
        return hist.Integral(low_bin, high_bin)

    good_ele = count_good(hist_ele, mu_ele, sigma_ele)
    good_mu  = count_good(hist_mu,  mu_mu,  sigma_mu)
    good_pi  = count_good(hist_pi,  mu_pi,  sigma_pi)

    # === Momentum calculation with offset correction ===
    c = 0.299792458  # m/ns
    L = 4.44         # m
    # Expected electron TOF and offset
    t_e_expected = L / c
    offset       = mu_ele - t_e_expected
    # Corrected TOFs for muon and pion
    t_mu_corr   = mu_mu - offset
    t_pi_corr   = mu_pi - offset
    
    # Calculate β, γ, momentum
    mass = {'ele':0.511, 'mu':105.66, 'pi':139.57}  # MeV/c^2
    beta_mu = L / (t_mu_corr * c)
    beta_pi = L / (t_pi_corr * c)
    gamma_mu= 1.0/np.sqrt(1 - beta_mu**2)
    gamma_pi= 1.0/np.sqrt(1 - beta_pi**2)
    momentum_mu = mass['mu'] * beta_mu * gamma_mu
    momentum_pi = mass['pi'] * beta_pi * gamma_pi

    # Print summary
    print(f"Electron entries: {n_ele:.0f}, good events (±2σ): {good_ele:.0f}")
    print(f"Muon entries:     {n_mu:.0f}, good events (±2σ): {good_mu:.0f}")
    print(f"Pion entries:     {n_pi:.0f}, good events (±2σ): {good_pi:.0f}")
    print(f"Raw entries:      {n_ru:.0f}\n")
    print(f"Electron mean time: {mu_ele:.3f} ± {ele_perr[1]:.3f} ns, σ={sigma_ele:.3f} ns, χ²/ndf={chi2_ele:.2f}")
    print(f"Expected e TOF: {t_e_expected:.3f} ns, Offset: {offset:.3f} ns")
    print(f"Muon mean time:     {mu_mu:.3f} ± {mu_perr[1]:.3f} ns, Corrected time: {t_mu_corr:.3f} ns, σ={sigma_mu:.3f} ns, χ²/ndf={chi2_mu:.2f}, p={momentum_mu:.2f} MeV/c")
    print(f"Pion mean time:     {mu_pi:.3f} ± {pi_perr[1]:.3f} ns, Corrected time: {t_pi_corr:.3f} ns, σ={sigma_pi:.3f} ns, χ²/ndf={chi2_pi:.2f}, p={momentum_pi:.2f} MeV/c")

    # Plotting (with offset annotation on electron)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    marker_kwargs = dict(marker='o', markersize=3, markeredgecolor='black', markerfacecolor='black', linestyle='')

    # Electron plot
    axes[0,0].errorbar(x_ele, y_ele, yerr_ele, **marker_kwargs, label='Data')
    axes[0,0].plot(x_ele, gauss(x_ele, *ele_popt), label='Fit')
    axes[0,0].set_title(f'VME run{run_number}:Electron TOF')
    axes[0,0].text(0.05, 0.95,
               f"μ={mu_ele:.3f} ns\nσ={sigma_ele:.3f} ns\nχ²/ndf={chi2_ele:.2f}\nN={n_ele:.0f}\nGood={good_ele:.0f}\noffset={offset:.3f} ns",
               transform=axes[0,0].transAxes, va='top')
    axes[0,0].legend()

    # Muon plot
    axes[0,1].errorbar(x_mu, y_mu, yerr_mu, **marker_kwargs, label='Data')
    axes[0,1].plot(x_mu, gauss(x_mu, *mu_popt), label='Fit')
    axes[0,1].set_title(f'VME run{run_number}:Muon TOF')
    axes[0,1].text(0.05, 0.95,
               f"μ={mu_mu:.3f} ns\nσ={sigma_mu:.3f} ns\nχ²/ndf={chi2_mu:.2f}\nN={n_mu:.0f}\nGood={good_mu:.0f}\np={momentum_mu:.2f} MeV/c",
               transform=axes[0,1].transAxes, va='top')
    axes[0,1].legend()

    # Pion plot
    axes[1,0].errorbar(x_pi, y_pi, yerr_pi, **marker_kwargs, label='Data')
    axes[1,0].plot(x_pi, gauss(x_pi, *pi_popt), label='Fit')
    axes[1,0].set_title(f'VME run{run_number}:Pion TOF')
    axes[1,0].text(0.05, 0.95,
               f"μ={mu_pi:.3f} ns\nσ={sigma_pi:.3f} ns\nχ²/ndf={chi2_pi:.2f}\nN={n_pi:.0f}\nGood={good_pi:.0f}\np={momentum_pi:.2f} MeV/c",
               transform=axes[1,0].transAxes, va='top')
    axes[1,0].legend()

    # Raw with fits
    axes[1,1].errorbar(x_ru, y_ru, yerr_ru, **marker_kwargs, label='Raw')
    axes[1,1].plot(x_ru, gauss(x_ru, *ele_popt), label='Electron')
    axes[1,1].plot(x_ru, gauss(x_ru, *mu_popt),  label='Muon')
    axes[1,1].plot(x_ru, gauss(x_ru, *pi_popt),  label='Pion')
    axes[1,1].set_title(f'VME run{run_number}:Raw TOF w/ Fits')
    axes[1,1].text(0.05, 0.95,
               f"N={n_ru:.0f}",
               transform=axes[1,1].transAxes, va='top')
    axes[1,1].legend()

    fig.tight_layout()
    fig.savefig(output_fig,facecolor='w')


    # save Raw with fits plot seperately from other plots
    seperate_output_fig = os.path.join(output_folder,  f"tof_fits_raw_run{run_number}.png")
    extent = axes[1,1].get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(seperate_output_fig, bbox_inches=extent.expanded(1.25, 1.15))



# Prompt user for VME run number
def get_run_number():
    #run = input("Enter VME run number (e.g., 1632): ")
    run = sys.argv[1]
    if not run.isdigit():
        raise ValueError("VME Run number must be numeric.")
    return run



if __name__ == '__main__':
    run_str = get_run_number()
    # === Configuration ===

    base_input_dir = sys.argv[2]
    base_output_dir = sys.argv[2]

    vme_momentum_calculator(run_str, base_input_dir, base_output_dir)
