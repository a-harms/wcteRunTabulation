#!/usr/bin/env python3

# ================= VME Analysis =================
# Bruno Ferrazzi (bferrazzi@uregina.ca)
# April 2025

import os
import uproot
import awkward as ak
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LogNorm
import re
import ROOT
ROOT.gROOT.SetBatch(True)
from ROOT import TH1F, TH2F, TCanvas

#additions
import sys

def vme_analysis(run_str, upper_pion_cut, lower_muon_cut, upper_muon_cut, calib_dir, outdir):
    print("[INFO] Starting VME analysis...")
    infile = os.path.join(calib_dir, f"beamline_run{run_str}_tuple_calib.root")
    if not os.path.isfile(infile):
        raise FileNotFoundError(f"Input file not found: {infile}")
    print(f"[INFO] Opening file: {infile}")

    # Load branches into awkward arrays
    print("[INFO] Reading ROOT tree into arrays...")
    with uproot.open(infile) as f:
        tree = f["beam_monitor_calib"]
        arrs = tree.arrays([
            "beamline_qdc_charge",
            "beamline_tdc_time",
            "beamline_id_name",
            "beamline_spill"      
        ], library="ak")

    q        = arrs["beamline_qdc_charge"]
    tdc      = arrs["beamline_tdc_time"]
    id_names = arrs["beamline_id_name"]
    spills   = arrs["beamline_spill"]

    spill_np = ak.to_numpy(spills).ravel()

    if spill_np.size:
        max_spill = int(spill_np.max())
    else:
        max_spill = 0
    print(f"[INFO] Total number of spills: {max_spill}")

    total_events = len(q)
    print(f"[INFO] Total events: {total_events}")

    # ------------------------------------------------------------------
    # Quick‐look plots for every channel, no cuts
    # ------------------------------------------------------------------
    def plot_all_channels(q, tdc, id_names, run_str, outdir, rf):

        # raw_dir = os.path.join(outdir, "/home/bferrazzi/Desktop/vme_plots/plots", f"run{run_str}/raw_plots")
        raw_dir = os.path.join(outdir, f"run{run_str}/raw_plots")
        os.makedirs(raw_dir, exist_ok=True)

        n_ch = len(q[0])

        dir_raw = rf.GetDirectory("raw_plots") or rf.mkdir("raw_plots")

        for ch in range(n_ch):

            try:
                tdc_times = ak.flatten(tdc[:, ch])
                tdc_np = ak.to_numpy(tdc_times)
            except Exception:
                tdc_np = np.array([])

            try:
                q_np = ak.to_numpy(q[:, ch])
                counts = ak.to_numpy(ak.num(tdc[:, ch]))
                q_repeat = np.repeat(q_np, counts)
            except Exception:
                q_np = np.array([])
                q_repeat = np.array([])
            # make 3×1 figure

            try:
                rawname     = id_names[0, ch]            # first event, this channel
                channel_name = str(rawname)
            except Exception:
                channel_name = f"chan{ch}"
            # sanitize filename 
            safe_name = re.sub(r"\W+", "_", channel_name)

            # ─── WRITE histograms into ROOT ─────────────────────────────
            ch_dir = dir_raw.GetDirectory(safe_name) or dir_raw.mkdir(safe_name)

            # 1) TDC histogram
            h_tdc = TH1F(f"{safe_name}_tdc", f"TDC times for {channel_name}", 200, np.nanmin(tdc_np) if tdc_np.size else 0, np.nanmax(tdc_np) if tdc_np.size else 1)
            for x in tdc_np:
                h_tdc.Fill(x)
            h_tdc.SetDirectory(ch_dir)

            # 2) QDC histogram
            h_q = TH1F(f"{safe_name}_q", f"QDC for {channel_name}", 200, np.nanmin(q_np) if q_np.size else 0, np.nanmax(q_np) if q_np.size else 1)
            for x in q_np:
                h_q.Fill(x)
            h_q.SetDirectory(ch_dir)

            # 3) 2D TDC vs QDC
            h2 = TH2F(f"{safe_name}_tdc_vs_q", f"TDC vs QDC for {channel_name}",
                        200, np.nanmin(tdc_np) if tdc_np.size else 0, np.nanmax(tdc_np) if tdc_np.size else 1,
                        200, np.nanmin(q_repeat) if q_repeat.size else 0, np.nanmax(q_repeat) if q_repeat.size else 1)
            for x,y in zip(tdc_np, q_repeat):
                h2.Fill(x,y)
            h2.SetDirectory(ch_dir)

            rf.cd(f"raw_plots/{safe_name}")

            h_tdc.Write()
            h_q.Write()
            h2.Write()

            # go back up so mkdir will work for the next channel
            rf.cd()

            fig, axs = plt.subplots(3, 1, figsize=(8, 12))
            # 1) TDC distribution
            if tdc_np.size > 0:
                axs[0].hist(tdc_np, bins=200, histtype='stepfilled', alpha=0.7)
            else:
                axs[0].text(0.5, 0.5, "No TDC data",
                            ha='center', va='center', transform=axs[0].transAxes)
            axs[0].set_title(f"Run {run_str} – {channel_name} – TDC times")
            axs[0].set_xlabel("TDC time")
            axs[0].set_ylabel("Counts")
            axs[0].set_yscale("log")
            axs[0].grid(True, linestyle=':', linewidth=0.5)
            # 2) QDC distribution
            if q_np.size > 0:
                axs[1].hist(q_np, bins=200, histtype='stepfilled', color='red', alpha=0.7)
            else:
                axs[1].text(0.5, 0.5, "No QDC data",
                            ha='center', va='center', transform=axs[1].transAxes)
            axs[1].set_title(f"Run {run_str} – {channel_name} – Charge (QDC)")
            axs[1].set_xlabel("Charge")
            axs[1].set_ylabel("Counts")
            axs[1].set_yscale("log")
            axs[1].grid(True, linestyle=':', linewidth=0.5)
            # 3) 2D TDC vs QDC
            if tdc_np.size > 0 and q_repeat.size > 0:
                h = axs[2].hist2d(tdc_np, q_repeat, bins=200, norm=LogNorm())
                plt.colorbar(h[3], ax=axs[2])
            else:
                axs[2].text(0.5, 0.5, "No TDC–Q data",
                            ha='center', va='center', transform=axs[2].transAxes)
            axs[2].set_title(f"Run {run_str} – {channel_name} – TDC vs QDC")
            axs[2].set_xlabel("TDC time")
            axs[2].set_ylabel("Charge")
            axs[2].grid(True, linestyle=':', linewidth=0.5)
            fig.tight_layout()
            outname = os.path.join(raw_dir, f"{safe_name}_overview.png")
            fig.savefig(outname, dpi=150, facecolor='w')
            plt.close(fig)
            print(f"[INFO] Saved channel overview: {outname}")

    # ------------------------------------------------------------------

    # Compute sums and TOF
    print("[INFO] Computing ACT sums and TOF values...")

    # ACTS
    act1 = ak.sum(q[:, 12:18], axis=1)
    act2 = ak.sum(q[:, 18:22], axis=1)
    act2_right = ak.sum(q[:, [19, 21]], axis=1)
    act2_left = ak.sum(q[:, [18, 20]], axis=1)

    # T0 / T1
    t0_chs = list(range(4))
    t1_chs = list(range(4,8))

    first_t0 = [ak.firsts(tdc[:,i], axis=1) for i in t0_chs]
    first_t1 = [ak.firsts(tdc[:,i], axis=1) for i in t1_chs]

    hit_t0 = ak.all([ak.num(tdc[:,i]) > 0 for i in t0_chs], axis=0)
    hit_t1 = ak.all([ak.num(tdc[:,i]) > 0 for i in t1_chs], axis=0)

    time_t0 = ak.all([vals < -100 for vals in first_t0], axis=0)
    time_t1 = ak.all([vals < -100 for vals in first_t1], axis=0)

    t0_list = [ak.fill_none(ak.firsts(tdc[:, i], axis=1), 0) for i in t0_chs]
    t1_list = [ak.fill_none(ak.firsts(tdc[:, i], axis=1), 0) for i in t1_chs]

    t0_avg = sum(t0_list) / 4.0
    t1_avg = sum(t1_list) / 4.0
    tof = t1_avg - t0_avg

    # Additional cuts
    print("[INFO] Applying additional cuts...")
    mask_t0 = time_t0 & hit_t0
    mask_t1 = time_t1 & hit_t1

    mask_T4 = (
        (ak.num(tdc[:, 42]) > 0) & (ak.num(tdc[:, 43]) > 0)
        & (q[:, 42] > 300) & (q[:, 43] > 300)
    )
    mask_HC0_1 = ~((q[:, 9] > 150) | (q[:, 10] > 100))

    slab_masks = [
        (ak.num(tdc[:, slab]) > 0) & (ak.num(tdc[:, slab + 8]) > 0)
        for slab in range(48, 56)
    ]
    mask_TOF = ak.any(ak.from_iter(slab_masks), axis=0)

    # tofsipm slab hit
    slab_hits_np = np.vstack([ak.to_numpy(m) for m in slab_masks]).T
    ev_idx, slab_idx = np.where(slab_hits_np)       

    act_x_point = 2000.0
    act_y_point = 2500.0
    slope     = -act_y_point / act_x_point    
    intercept = act_y_point
    mask_act_lr = act2_right >= (slope * act2_left + intercept)

    # Define cuts
    print("[INFO] Defining cut sequences...")
    cuts = {
        'raw': [('T0', mask_t0), ('T1', mask_t1)],
        'test': [('T0', mask_t0), ('T1', mask_t1), ('act1<1000', act1 < 1000), ('T4', mask_T4), ('HC0_1', mask_HC0_1), ('TOF', mask_TOF), ('ACTLine', mask_act_lr)],
        'e-veto': [ ('T0', mask_t0), ('T1', mask_t1),('act1<1000', act1 < 1000), ('T4', mask_T4), ('HC0_1', mask_HC0_1), ('TOF', mask_TOF) ],
        'e-only': [ ('T0', mask_t0), ('T1', mask_t1),('act1>1000', act1 > 1000), ('T4', mask_T4), ('HC0_1', mask_HC0_1), ('TOF', mask_TOF) ],
        'pion-only': [ ('T0', mask_t0), ('T1', mask_t1),('act2_pions', act2 < upper_pion_cut), ('act1<1000', act1 < 1000), ('T4', mask_T4), ('HC0_1', mask_HC0_1), ('TOF', mask_TOF)],
        'muon-only': [ ('T0', mask_t0), ('T1', mask_t1),('act2_muons', (act2 >= lower_muon_cut) & (act2 < upper_muon_cut)), ('act1<1000', act1 < 1000), ('T4', mask_T4), ('HC0_1', mask_HC0_1), ('TOF', mask_TOF)],
    }

    # Convert to numpy
    print("[INFO] Converting to NumPy for stats...")
    tof_np = ak.to_numpy(tof)
    act1_np = ak.to_numpy(act1)
    act2_np = ak.to_numpy(act2)
    act2_right_np = ak.to_numpy(act2_right)
    act2_left_np = ak.to_numpy(act2_left)

    # Stats
    print("[INFO] Gathering statistics per cut set...")
    stats_data = {}
    for name, seq in cuts.items():
        prev_mask = np.ones(total_events, dtype=bool)
        fail_counts = []
        for _, mask in seq:
            m_np = ak.to_numpy(mask)
            fail_counts.append(int(np.sum(prev_mask & ~m_np)))
            prev_mask &= m_np
        stats_data[name] = {
            'total': total_events,
            'passed': int(np.sum(prev_mask)),
            'fail_counts': fail_counts,
            'mask': prev_mask,
        }

    # Plots
    print("[INFO] Configuring plots (1D & 2D)...")
    plots = [
        {"cut_set":"raw","name":"t0t1_raw","type":"1d","data":"tof_np","bins":200,"range":(12,18)},
        {"cut_set":"e-veto","name":"t0t1_ev","type":"1d","data":"tof_np","bins":200,"range":(12,18)},
        {"cut_set":"e-only","name":"t0t1_ele","type":"1d","data":"tof_np","bins":200,"range":(12,18)},
        {"cut_set":"pion-only","name":"t0t1_pi","type":"1d","data":"tof_np","bins":200,"range":(12,18)},
        {"cut_set":"muon-only","name":"t0t1_mu","type":"1d","data":"tof_np","bins":200,"range":(12,18)},

        {"cut_set":"raw","name":"act1_raw","type":"1d","data":"act1_np","log_y": True,"bins":200,"range":(0,10000)},
        {"cut_set":"e-veto","name":"act1_ev","type":"1d","data":"act1_np","log_y": True,"bins":200,"range":(0,10000)},

        {"cut_set":"raw","name":"act2_raw","type":"1d","log_y": True,"data":"act2_np","bins":200,"range":(0,20000)},
        {"cut_set":"e-veto","name":"act2_ev","type":"1d","log_y": True,"data":"act2_np","bins":200,"range":(0,20000)},

        {"cut_set":"raw","name":"act2l_vs_act2r_raw","type":"2d","x":"act2_left_np","y":"act2_right_np","xbins":250,"xrange":(0,12500),"ybins":250,"yrange":(0,12500)},
        {"cut_set":"e-veto","name":"act2l_vs_act2r_ev","type":"2d","x":"act2_left_np","y":"act2_right_np","xbins":250,"xrange":(0,12500),"ybins":250,"yrange":(0,12500)},
        {"cut_set":"test","name":"act2l_vs_act2r_test","type":"2d","x":"act2_left_np","y":"act2_right_np","xbins":250,"xrange":(0,12500),"ybins":250,"yrange":(0,12500)},
        
        {"cut_set":"raw","name":"act2_vs_t0t1_raw","type":"2d","x":"tof_np","y":"act2_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},
        {"cut_set":"e-veto","name":"act2_vs_t0t1_e-veto","type":"2d","x":"tof_np","y":"act2_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},

        {"cut_set":"e-veto","name":"act2_vs_t0t1_e-veto_visible_cuts","type":"2d","x":"tof_np","y":"act2_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)}, # added for visible cuts

        {"cut_set":"pion-only","name":"act2_vs_t0t1_pion","type":"2d","x":"tof_np","y":"act2_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},
        {"cut_set":"muon-only","name":"act2_vs_t0t1_muon","type":"2d","x":"tof_np","y":"act2_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},
        {"cut_set":"test","name":"act2_vs_t0t1_test","type":"2d","x":"tof_np","y":"act2_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},
        {"cut_set":"raw","name":"act1_vs_t0t1_raw","type":"2d","x":"tof_np","y":"act1_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},
        {"cut_set":"e-veto","name":"act1_vs_t0t1_e-veto","type":"2d","x":"tof_np","y":"act1_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},
        {"cut_set":"pion-only","name":"act1_vs_t0t1_pion","type":"2d","x":"tof_np","y":"act1_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},
        {"cut_set":"muon-only","name":"act1_vs_t0t1_muon","type":"2d","x":"tof_np","y":"act1_np","xbins":150,"xrange":(12,18),"ybins":150,"yrange":(0,18000)},
    ]

    # Output
    print("[INFO] Creating output directories and ROOT file...")
    run_out = os.path.join(outdir, f"run{run_str}")
    os.makedirs(run_out, exist_ok=True)
    rf = ROOT.TFile.Open(os.path.join(run_out, f"hist_run{run_str}.root"), 'RECREATE')

    # create top‐level directory for raw channel plots
    dir_raw = rf.mkdir("raw_plots")
    
    plot_all_channels(q, tdc, id_names, run_str, outdir, rf)

    # Histograms and plots
    print("[INFO] Generating histograms and saving plots...")
    for p in plots:
        stats = stats_data[p['cut_set']]
        mask = stats['mask']

        if p['type'] == '1d':
            arr = locals()[p['data']][mask]
            counts, _ = np.histogram(arr, bins=p['bins'], range=p['range'])
            h = ROOT.TH1F(p['name'], p['name'], p['bins'], *p['range'])
            for i, c in enumerate(counts, 1): h.SetBinContent(i, c)
            h.SetEntries(stats['passed'])
            h.Write()

            plt.figure(figsize=(8,6))
            plt.hist(arr, bins=p['bins'], range=p['range'], histtype='stepfilled', alpha=0.7)
            ax = plt.gca()
            if p.get('log_y'):
                ax.set_yscale('log')
        else:
            x = locals()[p['x']][mask]
            y = locals()[p['y']][mask]
            counts2d, _, _ = np.histogram2d(x, y, bins=[p['xbins'],p['ybins']], range=[p['xrange'],p['yrange']])
            h2 = ROOT.TH2F(p['name'], p['name'], p['xbins'], p['xrange'][0], p['xrange'][1], p['ybins'], p['yrange'][0], p['yrange'][1])
            for ix in range(p['xbins']):
                for iy in range(p['ybins']):
                    h2.SetBinContent(ix+1, iy+1, int(counts2d[ix,iy]))
            h2.Write()

            plt.figure(figsize=(8,6))
            plt.hist2d(x, y, bins=[p['xbins'],p['ybins']], range=[p['xrange'],p['yrange']], norm=LogNorm())
            plt.colorbar()

        # added for visible cuts
        if p['name'] == 'act2_vs_t0t1_e-veto_visible_cuts':
            plt.axhline(y=upper_pion_cut, color='r', linewidth=0.5, label='Upper Pion Cut')
            plt.axhline(y=lower_muon_cut, color='r', linewidth=0.5, label='Lower Muon Cut')
            plt.axhline(y=upper_muon_cut, color='r', linewidth=0.5, label='Upper Muon Cut')

        # label logic
        xlabel = 'T1 - T0 (ns)' if (p.get('data') == 'tof_np' or p.get('x') == 'tof_np') else p.get('data', p.get('x', ''))
        ylabel = 'Counts' if p['type'] == '1d' else p.get('y', '')
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(f"Run {run_str}: {p['name']}")
        plt.grid(True, linestyle=':', linewidth=0.5)

        # Stats box
        lines = [f"Total: {stats['total']}", f"Passed: {stats['passed']}", "Removed:"]
        for lbl, cnt in zip([l for l,_ in cuts[p['cut_set']]], stats['fail_counts']):
            lines.append(f"  {lbl}: {cnt}")
        ax = plt.gca()
        ax.text(0.95, 0.95, "\n".join(lines), transform=ax.transAxes,
                fontsize=8, va='top', ha='right', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        png = os.path.join(run_out, f"h_run{run_str}_{p['name']}.png")
        plt.savefig(png, dpi=150, facecolor='w')
        plt.close()
        print(f"[INFO] Saved plot: {png}")

#===================TOF PLOTs=============================#
    # Occupancy per slab
    fig, ax = plt.subplots(figsize=(8,4))
    ax.hist(slab_idx, bins=np.arange(9)-0.5, histtype='stepfilled', alpha=0.7)
    ax.set_xticks(range(8))
    ax.set_xlabel('Slab index (0–7)')
    ax.set_ylabel('Counts')
    ax.set_title(f'Run {run_str} – TOF SiPM occupancy per slab')
    ax.grid(True, linestyle=':', linewidth=0.5)
    out_png = os.path.join(run_out, f"h_run{run_str}_TOFSipm_occupancy.png")
    fig.savefig(out_png, dpi=150, facecolor='w')
    plt.close(fig)
    print(f"[INFO] Saved TOF SiPM occupancy plot: {out_png}")
#===================TOF PLOTs=============================#
    # Ocuupancy per geometry
    occupancy    = np.bincount(slab_idx, minlength=8)                 # counts per slab
    slab_lengths = np.array([41, 94, 112, 123, 123, 112, 94, 41])     # mm
    text_pad     = 5.0                                               # mm padding for labels
    bar_height   = 1.0                                                # thickness of each bar
    # Set up figure 
    fig, ax = plt.subplots(figsize=(12, 6))
    # Color‐map
    norm = mpl.colors.Normalize(vmin=occupancy.min(), vmax=occupancy.max())
    cmap = plt.cm.viridis
    # Draw bars + annotate channels
    for slab in range(8):
        y_pos     = 7 - slab            # slab 0 at top
        length    = slab_lengths[slab]
        left_edge = -length / 2.0       # center on x=0
        # draw horizontal bar
        ax.barh(y_pos,width=length,left=left_edge,height=bar_height,color=cmap(norm(occupancy[slab])))
        # annotate: left end = slab+8, right end = slab
        ax.text(left_edge - text_pad+2,   y_pos, str(slab+8),va='center', ha='right')
        ax.text(left_edge + length + text_pad-2, y_pos, str(slab),va='center', ha='left')
    # Symmetric x‐axis
    half_max = slab_lengths.max() / 2.0
    ax.set_xlim(-half_max-5 - text_pad, half_max + text_pad)
    # Axes and grid
    ax.set_yticks(7 - np.arange(8))
    ax.set_yticklabels(np.arange(8))
    ax.set_ylabel("Slab index")
    ax.set_xlabel("Physical length (mm)")
    ax.set_title(f"Run {run_str} – TOF SiPM occupancy")
    ax.grid(axis='x', linestyle=':', linewidth=0.5)
    # Colorbar for occupancy
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.02)
    cbar.set_label("Occupancy (TDC events)")
    # Save
    out_png = os.path.join(run_out, f"h_run{run_str}_TOFSipm_geometry.png")
    fig.savefig(out_png, dpi=150, bbox_inches='tight',facecolor='w')
    plt.close(fig)
    print(f"[INFO] Saved TOF SiPM geometry plot: {out_png}")

if __name__ == '__main__':
    #run_str = input("Enter VME run number: ").strip()
    #if not run_str.isdigit():
    #    print("Invalid VME run number; digits only.")
    #    exit(1)

    ## calib_dir = '/home/bferrazzi/Desktop/calib'
    ## outdir = '/home/bferrazzi/Desktop/vme_plots/plots'
    #calib_dir = '/eos/experiment/wcte/data/ReadoutTest_Feb2025/calib_backup' 
    #outdir = '/eos/user/a/ajamieso/SWAN_projects/RunStatsChecker/vme_plots/plots'
    ##calib_dir = '/home/wcte/Desktop/calib_backup'
    ##outdir = '/home/wcte/Desktop/vme_plots/plots'
    #vme_analysis(run_str, calib_dir, outdir)

    run_str = sys.argv[1]
    if not run_str.isdigit():
        print("Invalid VME run number; digits only.")
        exit(1)

    upper_pion_cut = int(sys.argv[2])
    lower_muon_cut = int(sys.argv[3])
    upper_muon_cut = int(sys.argv[4])

    calib_dir = sys.argv[5]
    outdir = sys.argv[6]

    vme_analysis(run_str, upper_pion_cut, lower_muon_cut, upper_muon_cut, calib_dir, outdir)

