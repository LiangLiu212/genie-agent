# incl-potential-test — INCL potential energy and local energy at the QE vertex, in numpy

A standalone toy of the GENIE-INCL quasi-elastic vertex (electron on a C12 proton), built
to test the bookkeeping of INCL's potential energy `V0`, local energy `v_loc(r)` and r–p
correlated ground state with two-body phase space instead of a cross section. Everything
is ported from the INCL++ sources vendored in the `genie_inclxx` install and from the fork's
vertex code (`feature/incl-vertex-local-energy` @ `6bd7803d6`); file:line references are in
the module docstrings. Units: MeV, fm. Run everything through pixi from the repo root.

## Files

| file | what |
|---|---|
| `ep_phase_space.py` | step 0: e + p(free, at rest) → e' + p', flat two-body phase space; `scatter`, `boost`, `missing` helpers. E_miss = p_miss = 0 to 1e-12 (`ep_free_proton.*`). |
| `incl_nucleus.py` | `INCLNucleus`: MHO density, INCL's r–p correlation tables (`max_r_from_p`, `min_p_from_r`), strict/fuzzy `sample`, the fork's truncated-ball `resample_at_r`, `potential_energy(T)`, `local_energy(r, p, p_refl)`, `local_frame`. Self-test: `pixi run python incl-potential-test/incl_nucleus.py`. |
| `formulas.md` | the scattering-frame and INCL-balance formulas, closed forms for E_miss and p_miss, and their verification. |
| `formulas.tex`, `formulas.pdf` | the same document in LaTeX, compiled with tectonic (command below). |
| `ep_incl_scatter.py` | step 1: e + p(INCL C12) → e' + p' on the local-frame nucleon, then INCL's energy balance (`GENIEAvatar` functor port), then E_miss / p_miss of the record. |
| `ep_incl_C12_lf{on,never}[_resample].{png,txt,npz}` | outputs, 200k events, 2.445 GeV, seed 1. `.txt` = histdiag readouts (read these, not the PNG); `.npz` = event arrays (gitignored, 55 MB each). |

```bash
pixi run python incl-potential-test/ep_phase_space.py
pixi run python incl-potential-test/incl_nucleus.py                       # density self-test
pixi run python incl-potential-test/ep_incl_scatter.py --local-energy on   # add --never / --resample / --rp-coefficient 1
cd incl-potential-test && pixi run --manifest-path /exp/dune/data/users/liangliu/texenv/pixi.toml \
    tectonic --outdir . formulas.tex                                   # -> formulas.pdf
```

## The chain (per event)

1. **ground state** — momentum uniform in the p_F ball (p_F = 270.34 MeV/c), reflection
   radius R(p/p_F) from the inverse table of F(R) = ∫₀ᴿ(−r³ρ′) / ∫₀^Rmax(−r³ρ′), position uniform
   inside that sphere; default fuzzy coefficient 0.5 (HFB MHO a = 1.72905 fm, α = 0.849882),
   `--rp-coefficient 1` = strict (medium tables a = 1.72, α = 0.84). `--resample` applies the
   fork's `ResamplingHitNucleon` (|p|³ uniform on [p_min(r)³, p_F³] at the sampled r) — that is
   what GENIE's event loop actually feeds the vertex.
2. **scattering** on the local-frame nucleon: `on` → on-shell (p_red, E_ball − v_loc(r)),
   `never` → (p_ball, E_ball). Pure phase space (isotropic CM), no cross-section weight.
3. **INCL balance** — E_lep′ + E_p′ − V(T_p′) = E_lep + E_ball − V0 by scaling both CM momenta
   by one α (boost = CM of e + local-frame nucleon); the proton takes the energy-dependent
   V(T) = V0 − 0.287 (T − T_F) (0 above ≈195 MeV) and, with local energy on, the v_loc
   fixed point. Bisection to |ΔE| < 1e-12 MeV.
4. **record** — initial nucleon (p_ball, E_ball − V0); E_miss = ω − T_p′, p_miss = p_p′ − q.

## Results (200k events each; fork validation numbers from `docs/incl-vertex-local-energy-option-plan.md` in brackets)

| setting | record ⟨p_ball⟩, corr(p, r) | scattering ⟨\|p\|⟩, corr | E_miss fast protons: mean, range | ⟨\|p_miss\|⟩, ratio to p_red / p_ball |
|---|---|---|---|---|
| on | 202.6, +0.341 | 117.8, −0.499 | 21.98, [6.83, 44.97] | 119.4, 1.058 |
| never | 202.6, +0.341 | 202.6, +0.341 | 21.97, [6.83, 44.97] | 201.9, 1.0005 |
| on + resample | 225.5, +0.467 [225.6, +0.466] | 147.8, −0.664 [148.3, −0.668] | 17.46, [6.83, 44.80] [17.46, [6.83, 44.67]] | 148.4, 1.027 [1.02] |
| never + resample | 225.5, +0.467 [225.5, +0.466] | 225.5, +0.467 [225.8, +0.468] | 17.45, [6.83, 44.80] [17.50] | 224.2, 0.995 [1.007] |

- **E_miss identity is exact**: E_miss = V0 − T_ball − V(T_p′) to 2e-12 MeV in every setting.
  Fast protons (V = 0, 91 % of phase-space events) sit in [S, V0] = [6.83, 45.0]; the local
  energy never enters E_miss (it only moves the scattering nucleon and the lepton).
- **Slow outgoing protons** (T_p′ ≲ 195 MeV, 9 % here because phase space is flat in Q²)
  keep a potential V(T_p′) > 0, so their E_miss = V0 − T_ball − V(T_p′) runs down to −38 MeV.
- **INCL's rescaling does not conserve 3-momentum**: scaling the CM momenta changes the lab
  total by γβ ΔE* along the beam — mean −21 MeV/c (on) / −31 MeV/c (never), up to 36 MeV/c
  — so |p_miss| ≠ p_red exactly (review item 3, "the remnant absorbs it").
- **The r–p scheme reproduces ρ(r) − ρ(R_max)**, not ρ(r): positions live inside spheres capped
  at R_max = 5.65 fm, so the MHO tail is cut sharply (6.6 % low at 4.8 fm, 80 % low in the
  last 0.1 fm). Self-test chi2/ndf 0.6–1.3 against that form (400k nucleons, 40 bins) for
  strict/fuzzy × 60/3000 table nodes. This is the "deficit beyond 4.5 fm" of
  `docs/incl-ground-state-review.md` §1.
- With the fuzzy ground state and no resampling, v_loc uses INCL's R(y)/R(x) reflection
  ratio and never exceeds T_ball (0 clipped nucleons of 200k); 22 % of fuzzy nucleons lie
  below the strict floor p_min(r), which is why the resampled ⟨p⟩ is 225 instead of 203.
