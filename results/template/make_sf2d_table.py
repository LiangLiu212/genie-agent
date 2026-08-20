"""2D nuclear spectral function S(p,E) from the GENIE input table, per tune.

Plot 1 of the per-tune ground-state series (prototype: GEM26_22b_05_000, Fe56).
Unlike make_groundstate2d_incl_sf_lfg.py (event-level realization from gst),
this draws the *theory input*: the Benhar 2D spectral-function table that
genie::SpectralFunc reads (e.g. pke56_tot.data), resolved exactly the way the
tune resolves it at run time:

  tune -> ModelConfiguration.xml  NuclearModel@Pdg=<target>  (comments stripped)
       -> if genie::SpectralFunc: SpectralFunc.xml  SpectFuncTable@Pdg=<pdg>_<nuc>
          under DataPath (tune family dir first, then $GENIE/config), else skip.

Table format (matches SpectralFunc::LoadSFDataFile, SpectralFunc.cxx):
  header: nE np / Emin pmin / Emax pmax   [MeV, equally-spaced bin *edges*]
  body:   np blocks of { p_center, then nE (E_center, S) pairs },
          S = probability density [MeV^-4], tabulated with an overall factor
          of N_nucleons that GENIE divides out per hit nucleon.

Two panels, same (E,k) orientation as results/groundstate2d_incl_ar40_sf_lfg.png:
  left  = S(p,E) as tabulated                       [MeV^-4, log color]
  right = GENIE per-bin sampling weight 4*pi*p^2*S*dp*dE, area-normalized
          (this is the distribution TH2::GetRandom2 actually draws).

Usage:
  pixi run python results/template/make_sf2d_table.py                # 22b, Fe56
  pixi run python results/template/make_sf2d_table.py --tune GEM26_11a_05_000
  pixi run python results/template/make_sf2d_table.py --all-tunes    # campaign 4
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "genie-agent")
import numpy as np
from lib.pdg import resolve_pdg                     # noqa: E402
from plot_style import (apply_style, FS_LABEL, FS_TITLE, FS_TICK,
                        FS_SUPTITLE, PANEL_SIZE)    # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TUNES_DIR = REPO / "genie-agent" / "tunes"
CAMPAIGN_TUNES = ["GEM26_11a_05_000", "GEM26_22a_05_000",
                  "GEM26_22b_05_000", "GEM21_11a_05_000"]


def genie_root() -> Path:
    """$GENIE/.. of the selected installation ($GENIE_AGENT_INSTALLATION
    overrides active_installation, as everywhere in genie-agent). The
    GEM26/GEM21 campaign ran under genie_inclxx — pin that when the active
    installation has moved on (its SpectralFunc.xml lacks the C12 tables)."""
    import os
    cfg = json.load(open(REPO / "genie-agent" / "config" / "genie_env.json"))
    name = os.environ.get("GENIE_AGENT_INSTALLATION",
                          cfg["active_installation"])
    inst = cfg["installations"][name]
    return Path(inst["genie_bin_dir"]).parent


def _strip_comments(xml_text: str) -> str:
    return re.sub(r"<!--.*?-->", "", xml_text, flags=re.S)


def _param(xml_text: str, name: str):
    m = re.search(r'name="%s">\s*(\S+)\s*</param>' % re.escape(name), xml_text)
    return m.group(1) if m else None


def resolve_ground_state(tune: str, target_pdg: int) -> str:
    family = "_".join(tune.split("_")[:2])
    xml = _strip_comments((TUNES_DIR / family / "ModelConfiguration.xml").read_text())
    return (_param(xml, f"NuclearModel@Pdg={target_pdg}")
            or _param(xml, "NuclearModel"))


def resolve_sf_table(tune: str, target_pdg: int, hitnuc: int) -> Path:
    """Table path for genie::SpectralFunc, honoring GXMLPATH search order."""
    family = "_".join(tune.split("_")[:2])
    candidates = [TUNES_DIR / family / "SpectralFunc.xml",
                  genie_root() / "config" / "SpectralFunc.xml"]
    for cand in candidates:
        if not cand.exists():
            continue
        xml = _strip_comments(cand.read_text())
        # restrict to the Default param_set (the tunes use SpectralFunc/Default)
        m = re.search(r'<param_set name="Default">(.*?)</param_set>', xml, flags=re.S)
        body = m.group(1) if m else xml
        fname = _param(body, f"SpectFuncTable@Pdg={target_pdg}_{hitnuc}")
        if fname:
            data_path = _param(body, "DataPath")
            return genie_root() / data_path / fname
    raise SystemExit(f"no SpectFuncTable for pdg {target_pdg} hitnuc {hitnuc}")


def read_pke_table(path: Path):
    """Parse the pke table exactly as SpectralFunc::LoadSFDataFile does."""
    tok = path.read_text().split()
    n_E, n_p = int(tok[0]), int(tok[1])
    E_min, p_min = float(tok[2]), float(tok[3])
    E_max, p_max = float(tok[4]), float(tok[5])
    body = np.array(tok[6:], dtype=float)
    assert body.size == n_p * (1 + 2 * n_E), f"token count mismatch in {path}"
    blocks = body.reshape(n_p, 1 + 2 * n_E)
    p_centers = blocks[:, 0]                            # [MeV/c]
    E_centers = blocks[0, 1::2]                         # [MeV], same every block
    assert np.allclose(blocks[:, 1::2], E_centers), "E grid varies between blocks"
    S = blocks[:, 2::2]                                 # [MeV^-4], shape (n_p, n_E)
    p_edges = np.linspace(p_min, p_max, n_p + 1)
    E_edges = np.linspace(E_min, E_max, n_E + 1)
    return p_centers, E_centers, p_edges, E_edges, S


def make_figure(tune: str, target: str) -> bool:
    target_pdg = resolve_pdg(target)
    model = resolve_ground_state(tune, target_pdg)
    if "genie::SpectralFunc/" not in model:
        print(f"{tune}: {target} ground state = {model} "
              "(no 2D SF input table) -- skipped")
        return False

    table = resolve_sf_table(tune, target_pdg, 2212)
    table_n = resolve_sf_table(tune, target_pdg, 2112)
    shared = " (protons and neutrons)" if table_n == table else ""
    p_c, E_c, p_e, E_e, S = read_pke_table(table)
    dp = np.diff(p_e).mean()
    dE = np.diff(E_e).mean()

    # GENIE sampling weight per bin: 4*pi*p^2*S*dp*dE (the /N nucleon-count
    # normalization cancels once area-normalized for display)
    W = 4.0 * np.pi * p_c[:, None] ** 2 * S * dp * dE
    Wn = W / W.sum()

    frac_p250 = Wn[p_c > 250.0, :].sum()
    frac_E100 = Wn[:, E_c > 100.0].sum()
    print(f"{tune}: {target} -> {model} -> {table.name}{shared}")
    print(f"  grid: {len(p_c)} p-bins [{p_e[0]:.0f},{p_e[-1]:.0f}] MeV/c x "
          f"{len(E_c)} E-bins [{E_e[0]:.1f},{E_e[-1]:.1f}] MeV")
    print(f"  sampled tails: P(p>250 MeV/c)={frac_p250:.3f}  "
          f"P(E>100 MeV)={frac_E100:.3f}")

    apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    w, h = PANEL_SIZE
    fig, axes = plt.subplots(1, 2, figsize=(w * 2.4, h), sharey=True,
                             layout="constrained")
    # orientation: x = missing momentum P_miss, y = removal (missing) energy E_miss
    Xe, Ye = np.meshgrid(p_e, E_e, indexing="ij")
    panels = [
        (S,  r"table density  S($P_{\rm miss}$, $E_{\rm miss}$)  [MeV$^{-4}$]"),
        (Wn, r"GENIE sampling weight  4$\pi P_{\rm miss}^2 S\,\Delta P\Delta E$  (norm.)"),
    ]
    for ax, (Z, label) in zip(axes, panels):
        Zm = np.ma.masked_less_equal(Z, 0.0)
        norm = LogNorm(vmin=Zm.max() * 1e-6, vmax=Zm.max())
        pc = ax.pcolormesh(Xe, Ye, Zm, cmap="viridis", norm=norm)
        ax.set_title(label, fontsize=FS_TITLE - 2)
        ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
        ax.tick_params(labelsize=FS_TICK)
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)
    axes[0].set_ylabel(r"$E_{\rm miss}$  [MeV]", fontsize=FS_LABEL)

    shared_short = " (p and n)" if shared else ""
    fig.suptitle(f"{target} 2D spectral function from the GENIE input table\n"
                 f"{tune}:  {model.replace('genie::', '')}  $\\rightarrow$  "
                 f"{table.name}{shared_short}", fontsize=FS_SUPTITLE - 2)
    out = REPO / "results" / "prd-analyzer-v0.1" / f"sf2d_table_{target.lower()}_{tune}.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="GEM26_22b_05_000")
    ap.add_argument("--target", default="Fe56")
    ap.add_argument("--all-tunes", action="store_true",
                    help=f"run for the campaign tunes: {', '.join(CAMPAIGN_TUNES)}")
    args = ap.parse_args()
    tunes = CAMPAIGN_TUNES if args.all_tunes else [args.tune]
    for t in tunes:
        make_figure(t, args.target)
