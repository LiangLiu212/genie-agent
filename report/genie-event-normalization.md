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

## 6. Gotchas

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

## 7. gst branch reference (this run)

- Event weight: `wght` (identically 1 here).
- Cross sections: `XSec` (channel total), `DXSec` (differential), both in 1e-38 cm^2.
- Selected vs true kinematics: `xs, ys, ts, Q2s, Ws` (selected) vs `x, y, t, Q2, W` (true).
- Reaction flags: `qel, mec, res, dis, coh, em, cc, nc, …` (here `qel & em` true for all).
- Target / hit nucleon: `tgt, Z, A, hitnuc` (2212 proton / 2112 neutron).
- Kinematic phase-space code: `KPS` (12 here).

---

## 8. Units summary

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
