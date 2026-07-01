# Normalizing GENIE Events to an Absolute Cross Section

Companion to `simc-eep-normalization.md`. Documents how to turn a GENIE `gevgen`
event sample into an absolutely-normalized (per-nucleus) cross section, so GENIE and
SIMC (e,e'p) results come out in the same units (microbarn per nucleus).

Grounded in a real run from this repo:

- Command (`genie-agent/genie-runs/GEM26_11a_00_000-2026-06-02/…105732.log`):
  `gevgen -p 11 -t 1000060120 -n 1000 -e 2.445 --cross-sections <spline.xml>
  --tune GEM26_11a_00_000 --event-generator-list EMQE`
- i.e. e- (PDG 11) on C12, mono-energetic 2.445 GeV, electromagnetic quasi-elastic.
- Date: 2026-07-01

---

## 1. The principle

`gevgen` produces **unweighted** events (verified: the gst `wght` branch is identically
1 in this sample). Events are thrown proportional to the total differential cross
section, summed over all enabled channels and hit nucleons. Therefore the event density
in any observable already has the shape of dsigma/dx.

GENIE does **not** attach a physical normalization to the raw event count. To make a
distribution absolute you supply exactly one scale factor: the total cross section
`sigma_tot`. Everything else (which channel, which hit nucleon) is already encoded in how
events are distributed.

---

## 2. Recipe A -- differential cross section

For an observable x with bin width dx:

```
dsigma/dx |_bin = sigma_tot * N_bin / (N_gen * dx_bin)
```

- `sigma_tot` -- total cross section for all enabled processes on the target at the run
  energy (or flux-averaged), per nucleus.
- `N_gen` -- total generated events (1000 here).
- `N_bin` -- events in the bin (unweighted count; for weighted samples use sum of `wght`).
- Units follow `sigma_tot` (microbarn per nucleus if converted as below).

This yields an absolute, per-nucleus differential cross section directly comparable to
SIMC's per-nucleus A(e,e'p) result and to data.

---

## 3. Where sigma_tot comes from

### 3.1 Units of the gst cross-section branches

The gst tree (`gntpc -f gst`) carries `XSec` (total for the event's channel) and `DXSec`
(differential at the event's kinematics). Both are in **1e-38 cm^2**.

Conversion: 1 microbarn = 1e-30 cm^2, so

```
sigma[microbarn] = XSec_gst * 1e-8
```

### 3.2 Verified channel cross sections for the example run

`XSec` is constant within a channel; the two enabled channels (hit proton vs hit neutron)
give:

| channel (`hitnuc`) | gst `XSec` (1e-38 cm^2) | sigma (microbarn / C12) |
|--------------------|-------------------------|-------------------------|
| proton QE  (2212)  | 3.364e9                 | 33.6                    |
| neutron QE (2112)  | 1.921e8                 | 1.92                    |

### 3.3 Summing, not averaging

Events are thrown proportional to each channel's cross section, so:

```
sigma_tot = sigma_p + sigma_n ~= 35.6 microbarn per C12
```

Do **not** average the per-event `XSec` to get `sigma_tot`. The event-average is

```
<XSec> = sum_c (N_c/N) sigma_c = sum_c (sigma_c/sigma_tot) sigma_c = (sum_c sigma_c^2)/sigma_tot
```

which is not `sigma_tot`. Sum over the distinct channel values instead.

### 3.4 General / robust source

For many-channel or flux-driven runs, take `sigma_tot` from the **total cross-section
spline** (the `--cross-sections` XML) evaluated at E, or dump it with `gspl2root`, rather
than reconstructing it from the gst. For a flux run,

```
sigma_tot -> <sigma> = integral sigma(E) phi(E) dE / integral phi(E) dE
```

which the GENIE driver already applies to the event distribution; use that flux-averaged
total.

---

## 4. Recipe B -- absolute rate / luminosity (SIMC tie-in)

For counts in a real experiment with integrated luminosity L (cm^-2):

```
N_phys      = L * sigma_tot
w_event     = L * sigma_tot / N_gen
```

This is exactly SIMC's `luminosity * cross section`. For electron scattering
`L = (Q/e) * (N_A * rho * t / A)` folds beam charge and target thickness -- the same
quantities that become `targetfac` / `luminosity` in `simc.f:94,101` (see the SIMC
report). Matching L between the two simulations puts GENIE and SIMC yields on a common
absolute footing.

---

## 5. Worked example (uproot)

```python
import uproot, numpy as np

t = uproot.open("….gst.root")["gst"]
XSec, hitnuc, w = (t[b].array(library="np") for b in ("XSec", "hitnuc", "wght"))

# total cross section = sum of the DISTINCT per-channel XSec values (1e-38 cm^2 -> ub)
sig_tot_ub = sum(np.unique(XSec[hitnuc == n])[0] for n in np.unique(hitnuc)) * 1e-8

# absolute differential cross section in an observable (here Q2)
Q2 = t["Q2"].array(library="np")
counts, edges = np.histogram(Q2, bins=50, weights=w)
dsig_dQ2 = sig_tot_ub * counts / (w.sum() * np.diff(edges))   # microbarn / GeV^2, per C12
```

For the example run this gives `sig_tot_ub ~= 35.6` microbarn per C12.

---

## 6. Fiducial cuts and binning

Comparing to SIMC (or data) means restricting to a phase-space box. Keep two ideas apart:

- **Cuts** = the fiducial box in the 6-fold phase space (E', theta_e', E_p, theta_p, and
  the two azimuths). They define WHICH region you measure.
- **Binning** = the differential variable you histogram INSIDE that box.

### 6.1 Cuts are boolean selections on true kinematics -- they do not change the prefactor

gevgen threw `N_gen` unweighted events over the FULL 6-fold phase space, distributed
proportional to the true dsigma. So for any fiducial selection C and bin in x:

```
dsigma/dx |_{x-bin, event passes C} = sigma_tot * N(passes C & in x-bin) / (N_gen * dx)
```

`sigma_tot` and `N_gen` stay the FULL total and FULL generated count; the cut changes only
the numerator. Consequences:

- No acceptance correction and NO Jacobian are needed -- for the cut or for a nonlinear
  change of binning variable. The MC event density transforms automatically; apply the cut
  as a boolean and histogram x with the constant weight `sigma_tot/N_gen`.
- Do NOT shrink `sigma_tot` or `N_gen` to "events passing cuts" -- that double-counts the
  acceptance. The cut lives only in the numerator.

The result is the cross section integrated over the fiducial box, differential in x --
exactly what an (e,e'p) measurement within spectrometer acceptances reports.

### 6.2 What the four cuts constrain (fixed beam energy)

| cut (gst branch)             | fixes                          | spectral-function axis         |
|------------------------------|--------------------------------|--------------------------------|
| E' (`El`), theta_e' (`cthl`) | Q2, nu, \|q\|, x_B             | the (Q2, nu) hard-scatter point |
| E_p (`Ef`) at fixed nu       | E_m = nu - T_p - T_recoil      | removal / separation energy    |
| theta_p (`cthf`) at fixed q  | \|p_m\| (via theta_pq)         | initial-nucleon momentum       |

So the electron-arm cut is a cut on (Q2, x); the proton-arm cuts are a cut on (E_m, p_m).
Pick binning by goal:

- Reproduce a specific measurement: cut on the raw arm variables the experiment used, bin
  in its reported observable.
- QE (e,e'p) physics: cut the electron arm to fix (Q2, x~1), then bin in missing momentum
  p_m (and/or E_m) inside the proton-arm acceptance.

### 6.3 Match SIMC's genvol box (cross-check)

SIMC's `genvol` for A(e,e'p) is exactly the generated (Omega_e * Omega_p * E_e * E_p) box
(`simc.f:376-394`). If the GENIE cuts reproduce that same box -- including each arm's
AZIMUTHAL coverage, not just the in-plane angle -- the two integrated cross sections
should agree up to model/FSI differences. Leaving phi at full 4pi in GENIE while SIMC
subtends limited phi makes GENIE over-count. Match dOmega = dcos(theta) dphi on both arms.

### 6.4 Apply cuts at the same level on both sides

- GENIE gst gives TRUE (vertex) kinematics only.
- SIMC applies acceptance on RECONSTRUCTED kinematics (after optics, energy loss,
  resolution). For a theory-to-theory comparison, cut SIMC on its thrown/vertex quantities,
  not recon, so both are true-level. To compare to real data, fold GENIE through the
  detector acceptance (or unfold the data).
- A hard rectangular box is the standard first approximation; the real spectrometer
  acceptance is a smooth function (what SIMC's optics produce). For that fidelity, apply an
  acceptance function/weight to GENIE instead of a hard box.

### 6.5 Missing momentum: two definitions

- **True initial momentum:** `pn` (struck nucleon, pre-FSI) -- the PWIA p_m.
- **Reconstructed:** p_m = \|q - p_p'\|, with q = k - k' from the electron branches and the
  detected proton -- includes FSI distortion, which is what an experiment measures. Use
  this for data comparison, `pn` for the true initial-state distribution. EMQE + FSI shifts
  the two apart.

### 6.6 Cut-applied snippet (verified on the example gst; extends Section 5)

Note: `Ef` is TOTAL energy (includes the 0.938 GeV proton mass); use `Ef - m_p` for kinetic
energy, or `pf` for momentum, depending on what your spectrometer cut is defined on. The
ranges below are placeholders -- set them to your arm settings.

```python
import uproot, numpy as np, awkward as ak

t = uproot.open("….gst.root")["gst"]
a = t.arrays(["El","cthl","pdgf","Ef","cthf","pf","pn","hitnuc","XSec","wght"])

# FULL-sample normalization (unchanged by cuts)
hn = ak.to_numpy(a.hitnuc)
sig_tot_ub = sum(np.unique(ak.to_numpy(a.XSec)[hn==n])[0] for n in np.unique(hn)) * 1e-8
N_gen = len(a)

# electron arm (one value per event)
Ee  = ak.to_numpy(a.El)
the = np.degrees(np.arccos(ak.to_numpy(a.cthl)))

# leading final-state proton per event (pdgf/Ef/cthf/pf are per-particle)
is_p  = (a.pdgf == 2212)
has_p = ak.to_numpy(ak.num(a.pf[is_p]) > 0)
lead  = ak.argmax(ak.mask(a.pf, is_p), axis=1, keepdims=True)
Ep    = ak.to_numpy(ak.fill_none(ak.firsts(a.Ef[lead]),   -1.0))
thp   = np.degrees(np.arccos(ak.to_numpy(ak.fill_none(ak.firsts(a.cthf[lead]), -1.0))))

# fiducial box -- edit ranges to match the spectrometer arms
mask = ( has_p
       & (Ee  > 1.9) & (Ee  < 2.1)      # e' energy bite     [GeV]
       & (the > 12.) & (the < 16.)      # e' polar angle     [deg]
       & (Ep  > 0.9) & (Ep  < 1.6)      # proton total E     [GeV]
       & (thp > 30.) & (thp < 70.) )    # proton polar angle [deg]

# bin in missing momentum p_m (true initial nucleon momentum)
pn = ak.to_numpy(a.pn); w = ak.to_numpy(a.wght)
cnts, edges = np.histogram(pn[mask], bins=40, range=(0,0.4), weights=w[mask])
dsig_dpm = sig_tot_ub * cnts / (N_gen * np.diff(edges))   # microbarn/(GeV/c) per C12
```

`sigma_tot` and `N_gen` are the full-sample values; `mask` selects only the numerator.

---

## 7. Gotchas

- **Per-nucleus vs per-nucleon.** GENIE's `tgt:…;N:2212` cross section already sums over
  the 6 carbon protons -- it is per nucleus, matching SIMC's A(e,e'p) convention. Divide
  by A (or by Z for the proton channel) only if you specifically want per-nucleon.
- **Do not average per-event `XSec`** to get `sigma_tot` (Section 3.3). Sum distinct
  channels, or read the total spline.
- **Weighted samples.** If a run ever produces `wght != 1` (some flux/geometry modes),
  replace every count with the sum of `wght`. This sample is unweighted, so raw counts are
  fine.
- **`DXSec`** is the differential at each event's kinematics (`KPS=12` phase space for this
  run); it is not needed for Recipe A -- the event distribution already carries the
  differential shape.
- **Match the differential variable and per-target convention** between GENIE and SIMC/data
  before comparing, and apply flux-averaging consistently on both sides.

---

## 8. gst branch reference (this run)

- Event weight: `wght` (identically 1 here).
- Cross sections: `XSec` (channel total), `DXSec` (differential), both in 1e-38 cm^2.
- Selected vs true kinematics: `xs, ys, ts, Q2s, Ws` (selected) vs `x, y, t, Q2, W` (true).
- Reaction flags: `qel, mec, res, dis, coh, em, cc, nc, …` (here `qel & em` true for all).
- Target / hit nucleon: `tgt, Z, A, hitnuc` (2212 proton / 2112 neutron).
- Final electron (primary lepton): `El, pl, cthl` (E', |p|, cos theta_e').
- Final-state particles (per-particle arrays of length `nf`): `pdgf, Ef, pf, cthf`; counts
  `nfp` (protons), `nfn` (neutrons). Select the proton with `pdgf == 2212`.
- Struck (initial) nucleon, pre-FSI: `En, pn, cthn` -- `pn` is the PWIA missing momentum.
- Kinematic phase-space code: `KPS` (12 here).

---

## 9. Units summary

| Quantity                | Units                          |
|-------------------------|--------------------------------|
| gst `XSec`, `DXSec`     | 1e-38 cm^2 (per nucleus)       |
| 1 microbarn             | 1e-30 cm^2                     |
| conversion              | microbarn = XSec_gst * 1e-8    |
| `sigma_tot` (example)   | ~35.6 microbarn / C12          |
| `dsigma/dx` (Recipe A)  | microbarn / (unit of x) / nucleus |
| luminosity L            | cm^-2                          |
| `N_phys` (Recipe B)     | counts                         |

See `simc-eep-normalization.md` for the SIMC side (`luminosity`, `normfac`, `genvol`,
and the `normfac/Ngen * Weight` yield recipe).
