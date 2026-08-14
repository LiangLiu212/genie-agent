"""(e,e'p) QEL kinematics, NO Q^2 cut, N_p = 1 — v1.0.

The prd-analyzer-v1.0 kinematics figure: v0.1's uncut five variables
(El, theta_e', T_p, theta_p, Q^2) with v0.3's exactly-one-final-state-proton
selection on the proton panels:

    qel                            (El / theta_e' / Q^2 panels)
    qel && N_p(final state) = 1    (T_p / theta_p panels)

NO Q^2 window is applied — the Dutta Q^2 = 1.28 +- 5 % slice is drawn on the
Q^2 panel as grey-dashed REFERENCE lines only. The t05 generation cut
EM-MinQ2Limit = 1.18 GeV^2 remains the hard lower edge of the samples, so
"uncut" means the full generated phase space, not Q^2 -> 0.

Reads the v0.1 caches (cache/kin_qel_<target>/<tune>.npz, n_p column
included since v0.3; run make_kin_qel.py first if missing) and masks at
plot time; no streaming here.

Figures per target, written to results/prd-analyzer-v1.0/:
    kin_qel_<target>.png         area-normalized (shape comparison)
    kin_qel_<target>_counts.png  raw events/bin (equal ntot = 2M/tune)
    empm_<target>.png            E_m/p_m overlays, log y (no E_m/p_m cuts;
                                 sec-4 Dutta window grey-dashed as reference)
    empm_<target>_lin.png        linear-y companion
    empm_<target>_counts.png     raw events/bin companion

Usage:
  pixi run python results/template/make_kin_qel_v1.py --target C12
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

REPO = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO / "results/prd-analyzer-v0.1/cache"    # v0.1 caches, reused
OUT_DIR = REPO / "results/prd-analyzer-v1.0"

Q2_CENTER, Q2_FRAC = 1.28, 0.05                          # reference only
Q2_LO, Q2_HI = Q2_CENTER * (1 - Q2_FRAC), Q2_CENTER * (1 + Q2_FRAC)
KEYS = ["El", "theta_e", "Tp", "theta_p", "Q2", "E_miss", "p_miss", "n_p"]

# tune -> (color, linestyle, ground-state label): the v0.1 series convention
TUNES = {
    "GEM26_11a_05_000": ("C0", "-",  "LocalFGM"),
    "GEM26_22a_05_000": ("C2", "-",  "SF"),
    "GEM26_22b_05_000": ("C3", "-",  "SF"),
    "GEM21_11a_05_000": ("C4", "--", "LocalFGM"),
}

# panel -> (cache key, axis label, nice range step, nbins)
PANELS = [
    ("El",      r"E$_{e'}$  [GeV]",       0.1,   60),
    ("theta_e", r"$\theta_{e'}$  [deg]",  1.0,   60),
    ("Tp",      r"T$_p$  [GeV]",          0.1,   60),
    ("theta_p", r"$\theta_p$  [deg]",     5.0,   56),
    ("Q2",      r"Q$^2$  [(GeV/c)$^2$]",  0.02,  56),
]


def load_cache(target, tune):
    """v0.1 kin_qel cache -> dict, qel selection only (no Q^2 mask)."""
    path = CACHE_ROOT / f"kin_qel_{target.lower()}" / f"{tune}.npz"
    if not path.exists():
        raise SystemExit(f"missing v0.1 cache {path} — run make_kin_qel.py "
                         f"--target {target} first")
    c = dict(np.load(path))
    out = {k: c[k] for k in KEYS}
    out["has_p"] = c["has_p"]
    out["ntot"] = c["ntot"]
    return out


def panel_range(cache, key, step):
    """Pooled p0.2-p99.8 across tunes, rounded outward to `step`."""
    x = np.concatenate([cache[t][key] for t in TUNES])
    x = x[np.isfinite(x)]
    lo, hi = np.percentile(x, [0.2, 99.8])
    lo = np.floor(lo / step) * step
    hi = np.ceil(hi / step) * step
    return float(lo), float(hi)


def make_fig(target, cache, density):
    fig, axes = new_panels(ncols=3, nrows=2, sharey=False)
    for ax, (key, lab, step, nb) in zip(axes, PANELS):
        rng = panel_range(cache, key, step)
        if density:
            print(f"  panel {key}: range [{rng[0]:g}, {rng[1]:g}]")
        bins = np.linspace(rng[0], rng[1], nb)
        for tune, (color, ls, gs) in TUNES.items():
            x = cache[tune][key]
            m = np.isfinite(x)
            if key in ("Tp", "theta_p"):     # proton panels: exactly one FS p
                m &= cache[tune]["n_p"] == 1
            x = x[m]
            ax.hist(x, bins=bins, histtype="step", linewidth=1.8, color=color,
                    ls=ls, density=density,
                    label=f"{tune} ({gs}, N={len(cache[tune]['Q2']):,})")
        if key == "Q2":                       # Dutta window, reference only
            for v in (Q2_LO, Q2_HI):
                ax.axvline(v, color="0.5", ls="--", lw=1.0)
        style_axis(ax, title=None, xlabel=lab, logx=False, logy=False, ymin=None)
        ax.set_ylabel("normalized / bin" if density else "events / bin",
                      fontsize=FS_LABEL)
    axes[5].axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[5].legend(handles, labels, title="campaign tune", loc="center",
                   fontsize=FS_LEGEND - 1, title_fontsize=FS_LEGEND_TITLE)
    norm_note = ("area-normalized" if density
                 else "raw events/bin (equal ntot = 2M/tune)")
    fig.suptitle(f"(e,e'p) QEL kinematics, NO Q² cut (qel; T$_p$/$\\theta_p$: "
                 f"N$_p$=1)  —  e⁻ on {target} (t05, genlist EM), {norm_note}\n"
                 "grey dashed on Q² = Dutta 1.28 ± 5 % window (reference only, "
                 "NOT applied); hard edge at 1.18 = t05 EM-MinQ2Limit",
                 fontsize=FS_SUPTITLE - 1)
    fig.tight_layout()
    suffix = "" if density else "_counts"
    out = OUT_DIR / f"kin_qel_{target.lower()}{suffix}.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)


def make_empm_fig(target, cache, density, logy=True):
    """E_miss = omega - T_p and p_miss of the unique proton (N_p = 1), full
    generated phase space (NO Q^2 cut) and NO E_m/p_m cuts -- the Dutta
    window drawn grey-dashed as reference only (E_m: 0 and 80 MeV;
    p_m: 300 MeV/c). logy=False writes the linear-y companion (_lin)."""
    PANELS2 = [("E_miss", r"$E_m=\omega-T_p$  [MeV]",  20.0, 55, (0.0, 80.0)),
               ("p_miss", r"$p_m$  [MeV/c]",           50.0, 55, (300.0,))]
    fig, axes = new_panels(ncols=2, sharey=False)
    frac = {}
    for ax, (key, lab, step, nb, refs) in zip(axes, PANELS2):
        rng = panel_range(cache, key, step)
        bins = np.linspace(rng[0], rng[1], nb)
        for tune, (color, ls, gs) in TUNES.items():
            c = cache[tune]
            m = np.isfinite(c[key]) & (c["n_p"] == 1)
            if tune not in frac:
                w = (m & (c["E_miss"] >= 0) & (c["E_miss"] < 80)
                     & (c["p_miss"] < 300))
                frac[tune] = w.sum() / max(m.sum(), 1)
            ax.hist(c[key][m], bins=bins, histtype="step", linewidth=1.8,
                    color=color, ls=ls, density=density,
                    label=f"{tune} ({gs}, in-win {100*frac[tune]:.0f}%)")
        for v in refs:
            ax.axvline(v, color="0.5", ls="--", lw=1.0)
        style_axis(ax, title=None, xlabel=lab, logx=False, logy=logy, ymin=None)
        if not logy:
            ax.set_ylim(0, None)
        ax.set_ylabel("normalized / bin" if density else "events / bin",
                      fontsize=FS_LABEL)
    axes[0].legend(fontsize=FS_LEGEND - 4, loc="upper right",
                   title="the unique p (N$_p$=1); grey dashed =\n"
                         "Dutta window (reference, NOT applied)",
                   title_fontsize=FS_LEGEND_TITLE - 4)
    norm_note = ("area-normalized" if density
                 else "raw events/bin (equal ntot = 2M/tune)")
    fig.suptitle(f"E$_m$ / p$_m$, NO Q² cut, E$_m$/p$_m$ uncut — "
                 f"{target} (t05), {norm_note}",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    suffix = ("" if density else "_counts") + ("" if logy else "_lin")
    out = OUT_DIR / f"empm_{target.lower()}{suffix}.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)
    if density and logy:
        for t, f in frac.items():
            print(f"  {t}: in-window fraction (of qel && N_p=1) = {f:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="C12", choices=["Fe56", "C12"])
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()
    cache = {t: load_cache(args.target, t) for t in TUNES}
    for t in TUNES:
        npc = cache[t]["n_p"]
        print(f"  {t}: qel multiplicity 0p={np.mean(npc==0):.3f} "
              f"1p={np.mean(npc==1):.3f} 2p+={np.mean(npc>=2):.3f}")
    make_fig(args.target, cache, density=True)
    make_fig(args.target, cache, density=False)
    make_empm_fig(args.target, cache, density=True)
    make_empm_fig(args.target, cache, density=False)
    make_empm_fig(args.target, cache, density=True, logy=False)
    for t in TUNES:
        c = cache[t]
        print(f"  {t:18s} qel N={len(c['Q2']):7,d} of ntot={int(c['ntot'][0]):,}"
              f"  has_p={100*np.mean(c['has_p']):.1f}%")
