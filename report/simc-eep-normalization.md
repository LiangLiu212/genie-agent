# SIMC (e,e'p) Analysis and Cross-Section Normalization

Exploration report on the `simc_gfortran` codebase, focused on the (e,e'p) reaction
path and how the Monte Carlo weight is turned into an absolutely-normalized cross
section / yield.

- Repository: `simc_gfortran/` (vendored, own git checkout; HEAD `60c2047`)
- Working-tree state at time of exploration: clean (no local modifications)
- Date: 2026-07-01

---

## 1. What SIMC is

`simc_gfortran` is **SIMC**, the standard Jefferson Lab Hall A/C Monte Carlo for
**coincidence** electron scattering (written in FORTRAN). For (e,e'p) it:

1. Generates events over the spectrometer acceptances (limited phase space, not a
   generic event generator).
2. Weights each event by a physics cross section times a spectral function (or
   momentum distribution).
3. Folds in luminosity and the generation phase-space volume to produce an
   absolutely-normalized result.

It simulates spectrometer optics (COSY models) and apertures (HMS, SOS, SHMS, HRS,
BigCal), radiative effects, multiple scattering, ionization energy loss, and
particle decay. It is **not** a full GEANT-style detector simulation and does not
generate backgrounds a la Pythia.

Reactions supported (`README.md`): elastic and quasi-elastic `H(e,e'p)`, `A(e,e'p)`;
exclusive pion/kaon production; semi-inclusive pion/kaon; diffractive rho.

Output paths (`README.md`): native FORTRAN `.bin`, or converted to a PAW ntuple
(`util/ntuple`, needs CERNLIB) or a ROOT tree (`util/root_tree`, no CERNLIB). Helper
scripts: `run_simc`, `run_simc_ntup`, `run_simc_tree`.

---

## 2. The (e,e'p) code path

### 2.1 Reaction dispatch

The (e,e'p) subcase is selected purely from the target mass number A. When all the
`doing_*` reaction flags are false, SIMC defaults to (e,e'p).

`dbase.f:6` (comment) and `dbase.f:223-225`:

```fortran
doing_hyd_elast = (nint(targ%A).eq.1)
doing_deuterium = (nint(targ%A).eq.2)
doing_heavy     = (nint(targ%A).ge.3)
```

| Subcase            | Flag              | Set when | Physics model                          |
|--------------------|-------------------|----------|----------------------------------------|
| H(e,e'p) elastic   | `doing_hyd_elast` | A = 1    | `sigep`                                |
| D(e,e'p)           | `doing_deuterium` | A = 2    | `deForest` x momentum distribution     |
| A(e,e'p) quasi-el. | `doing_heavy`     | A >= 3   | `deForest` x spectral function S(E,p)  |

### 2.2 Physics cross section -- `physics_proton.f`

- **`sigep(vertex)`** (`physics_proton.f:1`) -- H elastic cross section:
  `sigMott * (E'/E) * Wp`, with `Wp = W2p + 2*W1p*tan^2(theta/2)`. Units: microbarn/sr.
- **`deForest(ev)`** (`physics_proton.f:25`) -- the off-shell electron-nucleon cross
  section (de Forest sigma_cc1 / sigma_cc2), selected by `deForest_flag`:
  - `0`  -> sigcc1
  - `1`  -> sigcc2
  - `-1` -> sigcc1 ON-SHELL (replace Ebar with E'-nu, qbar with q)

  **Critical units note** (header comment, `physics_proton.f:51-62`): the 6-fold cross
  section is `d6sigma = K * S(E,p) * sigma_eN`. `deForest` returns
  `d6sigma / S(E,p) = K * sigma_eN`, i.e. the spectral function is divided out and
  reapplied later as the event weight. Because S(E,p) has units MeV^-4, `deForest`
  carries units **microbarn * MeV^2 / sr^2**; multiplying by S(E,p) later restores the
  correct 6-fold cross-section units.
- **`sigMott(e0,theta,Q2)`** (`physics_proton.f:176`) -- Mott cross section for a point
  nucleus, microbarn/sr.
- **`fofa_best_fit(qsquar,GE,GM)`** (`physics_proton.f:137`) -- Peter Bosted's fit to
  world proton form-factor data (PRC 51, 409).

### 2.3 Spectral function / momentum distribution

- **Benhar spectral function**: `sf_lookup.f` (`sf_lookup_diff`), driven by data files
  such as `benharsf_12.dat`, `c12.sf`, `he4.sf`. Enabled by `use_benhar_sf` and
  `doing_heavy`.
- **Theory momentum distributions** for deuterium and (non-Benhar) heavy: interpolated
  in `event.f:1405-1431` from a theory file (see `doing_heavy` theory-file line written
  to output, `simc.f:970-972`).

### 2.4 Ready-made input decks -- `infiles/`

- `test_eep_h.inp`     -- H(e,e'p) elastic
- `test_eep_d.inp`     -- D(e,e'p)
- `test_eep_fe.inp`    -- Fe A(e,e'p)
- `test_eep_fe_bh.inp` -- Fe A(e,e'p) with `use_benhar_sf = 1`
- `eep_hydrogen_q8.inp`
- `ee_calcium48.inp`   -- NOTE: sets `doing_nuc_elast = 1`, i.e. coherent **nuclear
  elastic**, not quasi-elastic knockout. Do not use it as an A(e,e'p) template.

Relevant experiment-block flags (from `ee_calcium48.inp`): `ngen` (POS = number of
successes, NEG = number of tries), `EXPER%charge` (mC), `use_benhar_sf`, `transparency`
(proton transparency applied with the Benhar SF).

---

## 3. The normalization chain

This is the core of the exploration: how a generated event becomes a physical yield.

### 3.1 Per-event weight -- `event.f`

Assembled in `complete_main` at `event.f:1565-1566`:

```fortran
main%weight = main%SF_weight * main%jacobian * main%gen_weight * main%sigcc
main%weight = main%weight * tgtweight    ! correct for # nucleons involved
```

Factor by factor:

- **`main%sigcc`** -- the physics cross section. For (e,e'p): `sigep(vertex)` for
  hydrogen (`event.f:1454`), `deForest(vertex)` for D and heavy (`event.f:1462`).
  Optional Coulomb focusing factor `(1 + Coulomb/Ebeam)^2` applied at `event.f:1541`.
- **`main%SF_weight`** -- spectral-function / occupancy weight:
  - `= 1.0` for reactions with no SF (`event.f:1401`: hydrogen elastic, nuclear elastic,
    pion, kaon, delta, phsp, rho, semi).
  - `= targ%Z * transparency * S(Em,Pm)` for Benhar heavy (`event.f:1404`).
  - `= sum over momentum-distribution weights` for deuterium / non-Benhar heavy
    (`event.f:1430`).

  Together, `sigcc * SF_weight` reconstitutes the 6-fold cross section d6sigma in
  microbarn / MeV^2 / sr^2.
- **`main%jacobian`** -- coordinate Jacobian from the generated variables to the cross
  section's differential variables (`event.f:498` default 1.0; set at `event.f:603`,
  `event.f:1014-1022`).
- **`main%gen_weight`** -- generation weight (radiative generation etc.);
  1.0 in the simplest case, modified in `radc.f:521-523`.
- **`tgtweight`** -- number-of-nucleons correction; `= 1.0` for (e,e'p) since the Z/N
  weighting is already inside `SF_weight` (`event.f:1447`).

An event with `SF_weight <= 0` is discarded early unless `force_sigcc` is set
(`event.f:1438`).

### 3.2 End-game normalization -- `simc.f`

After the event loop, `simc.f` builds the normalization factor:

```fortran
targetfac = targ%mass_amu/3.75914d+6/(targ%abundancy/100.)
     >          * abs(cos(targ%angle))/(targ%thick*1000.)          ! simc.f:94
luminosity = EXPER%charge/targetfac                                 ! simc.f:101  (microbarn^-1)
...
normfac = luminosity/ntried*nevent                                 ! simc.f:368
...
genvol = domega_e                                                  ! simc.f:383
! 5-fold: + domega_p * dE_e  (D, heavy, pion, kaon, delta, rho, semi)  simc.f:389
! 6-fold: + dE_p             (doing_heavy, doing_semi)                 simc.f:393
normfac = normfac * genvol                                         ! simc.f:396
if (doing_phsp) normfac = 1.0                                      ! simc.f:397
wtcontribute = wtcontribute*normfac                               ! simc.f:398
```

Notes:

- `EXPER%charge` is in mC; `luminosity` comes out in microbarn^-1 (`simc.f:98-99`).
- **`genvol`** is the generated phase-space volume, built up by reaction dimensionality
  (`simc.f:376-394`):
  - H(e,e'p) elastic: `dOmega_e` only (2-fold; energy and hadron angle are constrained).
  - D(e,e'p) and most others: `x dOmega_p x dE_e` (5-fold).
  - **A(e,e'p) (`doing_heavy`): additionally `x dE_p` (6-fold)** -- the spectral function
    supplies the extra (Em, Pm) dimension.
- `domega_e = (yptar range)*(xptar range)` and similarly `domega_p` (`simc.f:376-381`).

### 3.3 Output header keys -- `simc.f`

Written to the SIMC output/hist file:

- `Ngen (request)` = `ngen`  (`simc.f:916`)
- `Ntried`        = `ntried` (`simc.f:917`)
- `Ncontribute`   (`simc.f:918`)
- `charge` (mC), `targetfac`, `luminosity` (microbarn^-1 and GeV^2), `genvol`,
  `normfac`  (`simc.f:963-968`)
- Random seed, theory file (heavy)  (`simc.f:970-974`)
- Integrated weights report: `wtcontr = wtcontribute/nevent`  (`simc.f:923`)

Each ntuple event carries `Weight = main%weight` (`results_write.f:146, 195, 257, 303`).

---

## 4. Recipe: from SIMC output to a cross section / yield

The estimator implied by the code (`simc.f:398` combined with the
`wtcontribute/nevent` report at `simc.f:923`) is:

```
bin_yield [counts] = (normfac / Ngen) * sum_over_events( Weight )
```

where `Ngen = nevent` (number of generated successes) and `normfac`, `Ngen` are read
from the output header; `Weight` is the per-event ntuple weight.

- Divide by `luminosity` to recover the model cross section (units follow the fold count:
  microbarn / MeV^i / sr^j).
- Standard experimental extraction (`central_xsec_howto.txt`):

  ```
  sigma_exp = (N_data / N_simc) * sigma_model
  ```

  i.e. SIMC provides the acceptance-and-radiative-folded model yield in the denominator;
  the ratio to data, times the model cross section, gives the measured cross section.

Practical note: to histogram a SIMC ROOT tree, weight every event by
`Weight * normfac / Ngen`. This yields counts normalized to the deck's `EXPER%charge`
and target; scale by the real experimental charge/target to compare to data.

---

## 5. Key file / symbol reference

| File                     | Symbol / line                        | Role                                                   |
|--------------------------|--------------------------------------|--------------------------------------------------------|
| `dbase.f`                | `:223-225`                           | (e,e'p) subcase dispatch by target A                   |
| `physics_proton.f`       | `sigep` `:1`                         | H(e,e'p) elastic cross section                         |
| `physics_proton.f`       | `deForest` `:25`                     | Off-shell e-N sigma_cc1/cc2 (D and A(e,e'p))           |
| `physics_proton.f`       | `sigMott` `:176`, `fofa_best_fit` `:137` | Mott xsec; Bosted proton form factors             |
| `sf_lookup.f`            | `sf_lookup_diff`                     | Benhar spectral-function lookup                        |
| `event.f`                | `:1399-1432`                         | SF_weight assembly (Benhar / momentum dist.)           |
| `event.f`                | `:1449-1537`                         | sigcc selection per reaction                           |
| `event.f`                | `:1565-1566`                         | master per-event weight                                |
| `simc.f`                 | `:94`, `:101`                        | targetfac, luminosity                                  |
| `simc.f`                 | `:368`, `:376-396`                   | normfac, genvol (phase-space volume)                   |
| `simc.f`                 | `:916-968`                           | output header (Ngen, normfac, luminosity, ...)         |
| `results_write.f`        | `:146/195/257/303`                   | per-event Weight into ntuple                           |
| `central_xsec_howto.txt` | --                                   | central cross-section extraction how-to                |
| `infiles/test_eep_*.inp` | --                                   | H / D / Fe (e,e'p) input decks                         |

---

## 6. Units summary

| Quantity            | Units                          |
|---------------------|--------------------------------|
| `sigMott`, `sigep`  | microbarn / sr                 |
| `deForest` (sigcc)  | microbarn * MeV^2 / sr^2       |
| `S(E,p)` (SF)       | MeV^-4                         |
| `sigcc * SF_weight` | microbarn / MeV^2 / sr^2 (d6sigma) |
| `luminosity`        | microbarn^-1                   |
| `genvol` (A(e,e'p)) | sr^2 * MeV^2 (6-fold)          |
| `bin_yield`         | counts (dimensionless)         |

---

## 7. Caveats / gotchas

- `ee_calcium48.inp` is **nuclear elastic** (`doing_nuc_elast=1`), not quasi-elastic
  (e,e'p). For A(e,e'p) leave the reaction flags false and set `use_benhar_sf` as needed.
- The final `wtcontribute` in the code has `normfac` multiplied in **and** carries an
  extra factor of `nevent` (`simc.f:368,398`); the physically meaningful integrated
  weight reported to the user is `wtcontribute/nevent` (`simc.f:923`). Downstream
  per-event histogramming must therefore use `normfac / Ngen` (not `normfac` alone).
- de Forest metric is (-1,1,1,1); the code defines inner products with regular signs and
  flips them in the structure-function formulas (`physics_proton.f:42-46`). Do not
  "fix" the signs without reading that comment.
- The QE (e,e'p) cross section factorizes as sigma_eN x S(E,p); this is why the SF is
  divided out of `deForest` and reintroduced as the event weight -- keep that separation
  intact when modifying the normalization.
