# The GENIE-INCL QE vertex in formulas: scattering frame and INCL balance

Companion to [`README.md`](README.md); the code is `incl_nucleus.py` (ground state,
potential, local energy) and `ep_incl_scatter.py` (scattering + balance). Every formula
below is what the scripts evaluate, and every "verified" number is the maximum deviation
over the 200k events of the named run (`ep_incl_C12_lf{on,never}[_resample].npz`,
2026-09-11). Sources: the INCL++ tree vendored in the `genie_inclxx` install and the fork
`feature/incl-vertex-local-energy` @ `6bd7803d6`; the convention itself is
[`docs/incl-vertex-local-energy-option-plan.md`](../docs/incl-vertex-local-energy-option-plan.md)
("Convention revised").

Plain-ASCII conventions used in the formula blocks: `vec x` is a 3-vector, `|x|` its
magnitude, `x'` an outgoing particle, `x_0` a quantity of the scattering frame (before the
balance), `sqrt()`, and Greek letters are spelled out (`alpha, beta, gamma, rho, omega`).

## 0. Notation

Units MeV, MeV/c, fm. Column 0 of a 4-vector is the energy.

| symbol | meaning | C12 value |
|---|---|---|
| `m` | INCL nucleon mass (protons and neutrons) | 938.2796 |
| `m_e` | electron mass (`shared/pdg.json`) | 0.511 |
| `p_F` | Fermi momentum, `1.37 hbar c * (2Z/A)^(1/3)` | 270.34 |
| `T_F` | `sqrt(p_F^2 + m^2) - m` | 38.17 |
| `S` | INCL separation energy | 6.83 |
| `V0` | well depth `T_F + S` | 45.00 |
| `R_max` | `5.5 + 0.3 (A - 6)/12` | 5.65 |
| `k = (E_e, vec k)` | beam electron, along +z | E_e = 2445 |
| `P = (E_N, vec p_N)` | the nucleon handed to the scattering | see section 2 |
| `k', p'` | outgoing electron and proton (final, after the balance) | |
| `k'_0, p'_0` | the same before the balance (scattering frame) | |

## 1. INCL ground state

**Density** (modified harmonic oscillator, `6 < A <= 19`):

```
rho(r) ~ (1 + alpha x^2) exp(-x^2),   x = r/a,   0 <= r <= R_max
fuzzy correlation (default): HFB table    a = 1.72905 fm, alpha = 0.849882   (C12 protons)
strict correlation:          medium table a = 1.72 fm,    alpha = 0.84
```

**r-p correlation.** INCL does not draw r from rho. It builds the density of *reflection
radii*

```
g(R) = -R^3 drho/dR = 2 R^2 x^2 (1 - alpha + alpha x^2) exp(-x^2)     (ModifiedHarmonicOscillatorRP)
F(R) = int_0^R g(R') dR' / int_0^R_max g(R') dR'
```

stores the inverse table `R(u)` with `u = F^(1/3)` at 60 equidistant R nodes (linear
interpolation, clamped), and its inverse `u(r)`. Then

```
max_r_from_p(x) = R(x)            reflection radius of a nucleon with |p| = x p_F
min_p_from_r(r) = u(r)            p_min(r)/p_F: the smallest momentum that reaches r
p_min(r)        = p_F F(r)^(1/3)
```

**Strict sampling** (coefficient >= 0.99999):

```
vec p_ball  uniform in the ball |p| <= p_F       ( (p/p_F)^3 uniform )
R           = R(|p_ball|/p_F)
vec r       uniform in the ball |r| <= R
p_refl      = |p_ball|                           (reflection momentum)
```

Uniformly filled nested spheres with `dN/dR = g(R)` generate

```
rho_gen(r) = int_r^R_max g(R) * 3/(4 pi R^3) dR  ~  rho(r) - rho(R_max)
```

i.e. the MHO tail cut sharply at R_max (6.6 % low at 4.8 fm, 80 % low in the last 0.1 fm).
Verified: sampled r vs `r^2 [rho(r) - rho(R_max)]`, chi2/ndf 0.6-1.3 (400k nucleons,
40 bins, strict/fuzzy x 60/3000 nodes).

**Fuzzy sampling** (coefficient c = 0.5 for protons, 0.73 for neutrons):

```
g1, g2 ~ N(0,1);  x_g = g1,  y_g = c x_g + g2 sqrt(1 - c^2);  u1 = Phi(x_g), u2 = Phi(y_g)
x = u1^(1/3),  y = u2^(1/3)
|p_ball| = y p_F (isotropic),   R = R(x),   vec r uniform in |r| <= R,   p_refl = x p_F
```

The marginals of r and p are those of the strict draw; only the joint correlation is
loosened (corr(p, r) = +0.34 instead of +0.68), and 22 % of the nucleons lie below
`p_min(r)`.

**The fork's redraw at fixed r** (`ResamplingHitNucleon`, flag `--resample`; what GENIE's
event loop feeds the vertex):

```
u = min_p_from_r(r),   |p_ball|^3 uniform on [u^3 p_F^3, p_F^3],   isotropic,   p_refl = |p_ball|
```

so `p_min(r) <= |p_ball| <= p_F` (corr(p, r) = +0.47, <p> = 225.5 MeV/c).

In every case `E_ball = sqrt(p_ball^2 + m^2)`, `T_ball = E_ball - m <= T_F`.

## 2. Potential energy and local energy

**Potential** (`NuclearPotentialEnergyIsospin`, alpha_V = 0.223):

```
V(T) = V0                                          T < T_F
     = max(0, V0 - alpha_V/(1 - alpha_V) * (T - T_F))
     = max(0, V0 - 0.287 (T - T_F))                T >= T_F
```

`V = 0` above `T ~ 195 MeV`; every ball nucleon has `V(T_ball) = V0`.

**Local energy** (`KinematicsUtils::getLocalEnergy`) for a nucleon at radius r with
momentum p and reflection momentum p_refl:

```
pfl0 = p_F                                     T <= T_F
     = sqrt(tf0 (tf0 + 2m)),  tf0 = V(T) - S    T > T_F   (v_loc = 0 if tf0 < 0 or r > R_max)
p_l  = pfl0 * min_p_from_r( r * R(p/pfl0) / R(p_refl/pfl0) )
v_loc(r, p) = sqrt(p_l^2 + m^2) - m
```

For a ball nucleon with `p_refl = |p|` (strict draw, or after the redraw) the ratio is 1
and `v_loc = T_F(r) = sqrt(p_min(r)^2 + m^2) - m`: 0 at the centre, `T_F` at R_max. For a
fuzzy nucleon the ratio `R(y)/R(x)` guarantees `v_loc <= T_ball` (0 clipped nucleons of
200k).

**Local frame** (fork `getHitNucleonP4`; `transformToLocalEnergyFrame` without mutation):

```
on:     E_loc = max(E_ball - v_loc, m),   vec p_red = sqrt(E_loc^2 - m^2) * p_hat_ball   (on shell)
never:  E_loc = E_ball,                   vec p_red = vec p_ball                          (v_loc = 0)
P = (E_loc, vec p_red)   is the nucleon handed to the scattering
```

## 3. Scattering frame (before the balance)

Two-body phase space on `P`: isotropic in the CM of `k + P`, then boosted to the lab, so
the 4-momentum of `e + P` is conserved exactly:

```
s  = (k + P)^2
p* = sqrt[(s - (m_e + m)^2)(s - (m_e - m)^2)] / (2 sqrt(s))      CM momentum
k + P = k'_0 + p'_0
```

Missing quantities of this state (the green curves of the figures):

```
omega_0  = E_e - E'_0 = E_p'_0 - E_loc
vec q_0  = vec k - vec k'_0 = vec p'_0 - vec p_red

E_miss_0     = omega_0 - T_p'_0 = m - E_loc = -T_red        (never: -T_ball)
vec p_miss_0 = vec p'_0 - vec q_0 = vec p_red               (never: vec p_ball)
```

Verified: `|E_miss_0 + T_red| <= 2.4e-12 MeV`, `| |p_miss_0| - |p_red| | <= 1.8e-12 MeV/c`
(all four runs). No binding appears here: the scattering sees an on-shell nucleon whose
kinetic energy is `T_red` (about 0 at the surface with local energy on).

## 4. INCL balance

INCL's `InteractionAvatar` rule as implemented in `G4INCLGENIEAvatar` (`preInteraction`,
`ViolationLeptonEMomentumFunctor`, `RootFinder`):

```
E_tot    = E_e + E_ball - V0                       conserved total: E - V of the GLOBAL nucleon,
                                                   no local-energy term
vec beta = (vec k + vec p_red) / (E_e + E_loc)     CM of e + local-frame nucleon
vec k*_0, vec p*_0 = k'_0, p'_0 boosted by -beta   (vec k*_0 + vec p*_0 = 0)
vec k* = alpha vec k*_0,   vec p* = alpha vec p*_0,   E* = sqrt(|.|^2 + mass^2)   one common alpha
k', p'   = boost back by +beta
V_p'     = V(T_p')                                 energy-dependent potential of the outgoing proton
on, slow protons only:  E_p' <- E_p' + v_loc(r, |p'|)  iterated to |delta v_loc| < 1e-4 MeV,
                        |p'| re-adjusted on shell   (scaleParticleMomenta; v_loc = 0 when V_p' < S)
solve for alpha:   E' + E_p' - V_p' = E_e + E_ball - V0      (bisection, |delta E| < 2e-12 MeV here;
                                                              INCL: 1e-4 MeV)
```

`alpha` is 0.980-1.014 (mean 0.988 on, 0.983 never); no bracketing failures in 800k events.

**Record** (what GENIE writes): initial nucleon `(vec p_ball, E_ball - V0)`, lepton `k'`,
pre-FSI proton `p'`. Then

```
omega = E_e - E',   vec q = vec k - vec k',   E_miss = omega - T_p',
vec p_miss = vec p' - vec q = vec k' + vec p' - vec k
```

## 5. Closed forms

**Energy.** Insert the balance condition into `omega - T_p'`:

```
E_miss = V0 - T_ball - V(T_p')
       = V0 - T_ball  in [S, V0] = [6.83, 45.0]      for fast protons (V = 0, T_p' > ~195 MeV)
```

Independent of the local-energy setting: `v_loc` moves the scattering nucleon and the
lepton, never `E_miss`. Slow protons keep `V(T_p') > 0` and reach `E_miss` down to
`-T_F = -38 MeV`. Verified: `<= 2.1e-12 MeV` in all four runs.

**Momentum.** In the CM the two momenta cancel for every alpha, so the lab total after the
boost is `gamma vec beta E*_tot(alpha)`; before scaling it was
`vec k + vec p_red = gamma vec beta sqrt(s)`. The energy condition fixes
`gamma (E*_tot(alpha) - sqrt(s)) = V(T_p') - V0 + v_loc`, hence

```
vec p_miss = vec p_red + vec beta * (V(T_p') - V0 + v_loc(r))     (never: v_loc = 0, vec p_red = vec p_ball)
           = vec p_red - vec beta * (V0 - v_loc)                  fast protons
```

The rescaling therefore shifts the final-state momentum against the beam by
`beta_z (V0 - v_loc)`: mean 22 MeV/c (on, <beta_z> = 0.72, <v_loc> = 13.9) and 32 MeV/c
(never), the difference between the blue and green `|p_miss|` curves; the remnant absorbs
it (review note item 3). Verified: `<= 2.8e-12 MeV/c` for fast protons in all four runs.
For slow protons with local energy on the fixed point `E_p' <- E_p' + v_loc` re-adjusts
`|p'|` after the boost and the closed form no longer applies (deviations up to 236 MeV/c,
mean 18, for the 9 % of phase-space events with `V(T_p') > 0`).

## 6. Summary of the two settings

| | scattering nucleon `P` | scattering frame `E_miss_0`, `vec p_miss_0` | record `E_miss` | record `vec p_miss` (fast p') |
|---|---|---|---|---|
| on | `(E_ball - v_loc, vec p_red)` | `-T_red`, `vec p_red` | `V0 - T_ball - V(T_p')` | `vec p_red - vec beta (V0 - v_loc)` |
| never | `(E_ball, vec p_ball)` | `-T_ball`, `vec p_ball` | `V0 - T_ball - V(T_p')` | `vec p_ball - vec beta V0` |

Numbers (200k events, 2.445 GeV, seed 1, `--resample`): <|p_red|> 147.8 MeV/c with
corr(p_red, r) = -0.66 (on) vs <|p_ball|> 225.5, +0.47 (never); `E_miss` of fast protons
mean 17.46 in [6.83, 44.80] in both; <|p_miss|> 148.4 (on) / 224.2 (never).
