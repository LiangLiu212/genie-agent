# The GENIE–INCL QE vertex in formulas: scattering frame and INCL balance

Companion to [`README.md`](README.md); the code is `incl_nucleus.py` (ground state,
potential, local energy) and `ep_incl_scatter.py` (scattering + balance). Every formula
below is what the scripts evaluate, and every "verified" number is the maximum deviation
over the 200k events of the named run (`ep_incl_C12_lf{on,never}[_resample].npz`,
2026-09-11). Sources: the INCL++ tree vendored in the `genie_inclxx` install and the fork
`feature/incl-vertex-local-energy` @ `6bd7803d6`; the convention itself is
[`docs/incl-vertex-local-energy-option-plan.md`](../docs/incl-vertex-local-energy-option-plan.md)
("Convention revised").

## 0. Notation

Units MeV, MeV/c, fm. Column 0 of a 4-vector is the energy.

| symbol | meaning | C12 value |
|---|---|---|
| `m` | INCL nucleon mass (protons and neutrons) | 938.2796 |
| `m_e` | electron mass (`shared/pdg.json`) | 0.511 |
| `p_F` | Fermi momentum, `1.37 ħc · (2Z/A)^{1/3}` | 270.34 |
| `T_F` | `√(p_F² + m²) − m` | 38.17 |
| `S` | INCL separation energy | 6.83 |
| `V0` | well depth `T_F + S` | 45.00 |
| `R_max` | `5.5 + 0.3 (A − 6)/12` | 5.65 |
| `k = (E_e, k⃗)` | beam electron, along +z | E_e = 2445 |
| `P = (E_N, p⃗_N)` | the nucleon handed to the scattering | see §2 |
| `k′, p′` | outgoing electron and proton (final, after the balance) | |
| `k′₀, p′₀` | the same before the balance (scattering frame) | |

## 1. INCL ground state

**Density** (modified harmonic oscillator, `6 < A ≤ 19`):

```
ρ(r) ∝ (1 + α x²) e^{−x²},   x = r/a,   0 ≤ r ≤ R_max
fuzzy correlation (default): HFB table   a = 1.72905 fm, α = 0.849882   (C12 protons)
strict correlation:          medium table a = 1.72 fm,    α = 0.84
```

**r–p correlation.** INCL does not draw r from ρ. It builds the density of *reflection
radii*

```
g(R) = −R³ dρ/dR = 2 R² x² (1 − α + α x²) e^{−x²}         (ModifiedHarmonicOscillatorRP)
F(R) = ∫₀ᴿ g / ∫₀^{R_max} g
```

stores the inverse table `R(u)` with `u = F^{1/3}` at 60 equidistant R nodes (linear
interpolation, clamped), and its inverse `u(r)`. Then

```
max_r_from_p(x) = R(x)            reflection radius of a nucleon with |p| = x p_F
min_p_from_r(r) = u(r)            p_min(r)/p_F: the smallest momentum that reaches r
p_min(r)        = p_F F(r)^{1/3}
```

**Strict sampling** (coefficient ≥ 0.99999):

```
p⃗_ball  uniform in the ball |p| ≤ p_F         ( (p/p_F)³ uniform )
R       = R(|p_ball|/p_F)
r⃗       uniform in the ball |r| ≤ R
p_refl  = |p_ball|                              (reflection momentum)
```

Uniformly filled nested spheres with `dN/dR = g(R)` generate

```
ρ_gen(r) = ∫_r^{R_max} g(R) · 3/(4πR³) dR ∝ ρ(r) − ρ(R_max)
```

i.e. the MHO tail cut sharply at R_max (6.6 % low at 4.8 fm, 80 % low in the last 0.1 fm).
Verified: sampled r vs `r²[ρ(r) − ρ(R_max)]`, chi2/ndf 0.6–1.3 (400k nucleons, 40 bins,
strict/fuzzy × 60/3000 nodes).

**Fuzzy sampling** (coefficient c = 0.5 for protons, 0.73 for neutrons):

```
g₁, g₂ ~ N(0,1);  x_g = g₁,  y_g = c x_g + g₂ √(1 − c²);  u₁ = Φ(x_g), u₂ = Φ(y_g)
x = u₁^{1/3},  y = u₂^{1/3}
|p_ball| = y p_F (isotropic),   R = R(x),   r⃗ uniform in |r| ≤ R,   p_refl = x p_F
```

The marginals of r and p are those of the strict draw; only the joint correlation is
loosened (corr(p, r) = +0.34 instead of +0.68), and 22 % of the nucleons lie below
`p_min(r)`.

**The fork's redraw at fixed r** (`ResamplingHitNucleon`, flag `--resample`; what GENIE's
event loop feeds the vertex):

```
u = min_p_from_r(r),   |p_ball|³ uniform on [u³ p_F³, p_F³],   isotropic,   p_refl = |p_ball|
```

so `p_min(r) ≤ |p_ball| ≤ p_F` (corr(p, r) = +0.47, ⟨p⟩ = 225.5 MeV/c).

In every case `E_ball = √(p_ball² + m²)`, `T_ball = E_ball − m ≤ T_F`.

## 2. Potential energy and local energy

**Potential** (`NuclearPotentialEnergyIsospin`, α_V = 0.223):

```
V(T) = V0                                     T < T_F
     = max(0, V0 − α_V/(1 − α_V) · (T − T_F))  = max(0, V0 − 0.287 (T − T_F))   T ≥ T_F
```

`V = 0` above `T ≈ 195 MeV`; every ball nucleon has `V(T_ball) = V0`.

**Local energy** (`KinematicsUtils::getLocalEnergy`) for a nucleon at radius r with
momentum p and reflection momentum p_refl:

```
pfl0 = p_F                                   T ≤ T_F
     = √(tf0 (tf0 + 2m)),  tf0 = V(T) − S    T > T_F   (v_loc = 0 if tf0 < 0 or r > R_max)
p_l  = pfl0 · min_p_from_r( r · R(p/pfl0) / R(p_refl/pfl0) )
v_loc(r, p) = √(p_l² + m²) − m
```

For a ball nucleon with `p_refl = |p|` (strict draw, or after the redraw) the ratio is 1
and `v_loc = T_F(r) ≡ √(p_min(r)² + m²) − m`: 0 at the centre, `T_F` at R_max. For a
fuzzy nucleon the ratio `R(y)/R(x)` guarantees `v_loc ≤ T_ball` (0 clipped nucleons of 200k).

**Local frame** (fork `getHitNucleonP4`; `transformToLocalEnergyFrame` without mutation):

```
on:     E_loc = max(E_ball − v_loc, m),   p⃗_red = √(E_loc² − m²) · p̂_ball      (on shell)
never:  E_loc = E_ball,                   p⃗_red = p⃗_ball                      (v_loc ≡ 0)
P = (E_loc, p⃗_red)   is the nucleon handed to the scattering
```

## 3. Scattering frame (before the balance)

Two-body phase space on `P`: isotropic in the CM of `k + P`, then boosted to the lab, so
the 4-momentum of `e + P` is conserved exactly:

```
s  = (k + P)²
p* = √[(s − (m_e + m)²)(s − (m_e − m)²)] / (2√s)      CM momentum
k + P = k′₀ + p′₀
```

Missing quantities of this state (the green curves of the figures):

```
ω₀ = E_e − E′₀ = E_p′₀ − E_loc
q⃗₀ = k⃗ − k⃗′₀ = p⃗′₀ − p⃗_red

E_miss⁽⁰⁾ = ω₀ − T_p′₀ = m − E_loc = −T_red        (never: −T_ball)
p⃗_miss⁽⁰⁾ = p⃗′₀ − q⃗₀ = p⃗_red                      (never: p⃗_ball)
```

Verified: `|E_miss⁽⁰⁾ + T_red| ≤ 2.4e-12 MeV`, `||p_miss⁽⁰⁾| − |p_red|| ≤ 1.8e-12 MeV/c`
(all four runs). No binding appears here: the scattering sees an on-shell nucleon whose
kinetic energy is `T_red` (≈ 0 at the surface with local energy on).

## 4. INCL balance

INCL's `InteractionAvatar` rule as implemented in `G4INCLGENIEAvatar` (`preInteraction`,
`ViolationLeptonEMomentumFunctor`, `RootFinder`):

```
E_tot = E_e + E_ball − V0                          conserved total: E − V of the GLOBAL nucleon,
                                                   no local-energy term
β⃗     = (k⃗ + p⃗_red) / (E_e + E_loc)                CM of e + local-frame nucleon
k⃗*₀, p⃗*₀ = k′₀, p′₀ boosted by −β⃗                  (k⃗*₀ + p⃗*₀ = 0)
k⃗* = α k⃗*₀,   p⃗* = α p⃗*₀,   E* = √(|·|² + mass²)  one common scale factor α
k′, p′ = boost back by +β⃗
V_p′ = V(T_p′)                                     energy-dependent potential of the outgoing proton
on, slow protons only:  E_p′ ← E_p′ + v_loc(r, |p′|)  iterated to |Δv_loc| < 1e-4 MeV,
                        |p′| re-adjusted on shell  (scaleParticleMomenta; v_loc = 0 when V_p′ < S)
solve for α:   E′ + E_p′ − V_p′ = E_e + E_ball − V0      (bisection, |ΔE| < 2e-12 MeV here;
                                                          INCL: 1e-4 MeV)
```

`α` is 0.980–1.014 (mean 0.988 on, 0.983 never); no bracketing failures in 800k events.

**Record** (what GENIE writes): initial nucleon `(p⃗_ball, E_ball − V0)`, lepton `k′`,
pre-FSI proton `p′`. Then

```
ω = E_e − E′,   q⃗ = k⃗ − k⃗′,   E_miss = ω − T_p′,   p⃗_miss = p⃗′ − q⃗ = k⃗′ + p⃗′ − k⃗
```

## 5. Closed forms

**Energy.** Insert the balance condition into `ω − T_p′`:

```
E_miss = V0 − T_ball − V(T_p′)
       = V0 − T_ball ∈ [S, V0] = [6.83, 45.0]        for fast protons (V = 0, T_p′ ≳ 195 MeV)
```

Independent of the local-energy setting: `v_loc` moves the scattering nucleon and the
lepton, never `E_miss`. Slow protons keep `V(T_p′) > 0` and reach `E_miss` down to
`−T_F = −38 MeV`. Verified: `≤ 2.1e-12 MeV` in all four runs.

**Momentum.** In the CM the two momenta cancel for every α, so the lab total after the
boost is `γβ⃗ E*_tot(α)`; before scaling it was `k⃗ + p⃗_red = γβ⃗ √s`. The energy condition
fixes `γ (E*_tot(α) − √s) = V(T_p′) − V0 + v_loc`, hence

```
p⃗_miss = p⃗_red + β⃗ · (V(T_p′) − V0 + v_loc(r))          (never: v_loc = 0, p⃗_red = p⃗_ball)
       = p⃗_red − β⃗ (V0 − v_loc)                          fast protons
```

The rescaling therefore shifts the final-state momentum against the beam by
`β_z (V0 − v_loc)`: mean 22 MeV/c (on, ⟨β_z⟩ = 0.72, ⟨v_loc⟩ = 13.9) and 32 MeV/c
(never), the difference between the blue and green `|p_miss|` curves — the remnant absorbs
it (review note item 3). Verified: `≤ 2.8e-12 MeV/c` for fast protons in all four runs.
For slow protons with local energy on the fixed point `E_p′ ← E_p′ + v_loc` re-adjusts
`|p′|` after the boost and the closed form no longer applies (deviations up to 236 MeV/c,
mean 18, for the 9 % of phase-space events with `V(T_p′) > 0`).

## 6. Summary of the two settings

| | scattering nucleon `P` | scattering-frame `E_miss⁽⁰⁾`, `p⃗_miss⁽⁰⁾` | record `E_miss` | record `p⃗_miss` (fast p′) |
|---|---|---|---|---|
| on | `(E_ball − v_loc, p⃗_red)` | `−T_red`, `p⃗_red` | `V0 − T_ball − V(T_p′)` | `p⃗_red − β⃗ (V0 − v_loc)` |
| never | `(E_ball, p⃗_ball)` | `−T_ball`, `p⃗_ball` | `V0 − T_ball − V(T_p′)` | `p⃗_ball − β⃗ V0` |

Numbers (200k events, 2.445 GeV, seed 1, `--resample`): ⟨|p_red|⟩ 147.8 MeV/c with
corr(p_red, r) = −0.66 (on) vs ⟨|p_ball|⟩ 225.5, +0.47 (never); `E_miss` of fast protons
mean 17.46 in [6.83, 44.80] in both; ⟨|p_miss|⟩ 148.4 (on) / 224.2 (never).
