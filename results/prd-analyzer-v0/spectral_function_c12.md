[← prd-analyzer](README.md) · [← Results home](../README.md)

# C12 Benhar spectral function — P(k,E) in missing energy & momentum

The **input ground state** behind the SF prd-analyzer models, read straight from GENIE's
tabulated Benhar 2D spectral function
`data/evgen/nucl/spectral_functions/pke12_tot.data` and drawn in the same
(missing energy `E`, missing momentum `k`) plane the event-level plots use. Both
`GEM26_22a` (SF + Rosenbluth) and `GEM26_22b` (SF + UnifiedQEL) sample their struck nucleon
from *this* distribution — so it is the common baseline against which the two cross-section
models' reconstructed `E_m` should be read.

![C12 Benhar spectral function: 2D P(k,E), removal-energy marginal, momentum marginal](spectral_function_c12.png)
*Left: `4π k² P(k,E)` (log color). Middle: removal-energy marginal `f(E)=∫4πk²P dk`.
Right: momentum marginal `n(k)=∫4πk²P dE`.*

## File format (verified against `SpectralFunc.cxx:273-330`)

| Header line | Meaning |
|-------------|---------|
| `80 40`     | 80 removal-energy bins, 40 momentum bins |
| `0 0`       | `E_min`, `p_min` (MeV) |
| `400 800`   | `E_max` (MeV), `p_max` (MeV) |

Body = 40 momentum blocks; each is a momentum value `k` followed by 80 `(E, P)` pairs.
`P` is the density `P(k,E)` in **MeV⁻⁴**, tabulated as `N·P` (file folds in the nucleon
count; GENIE divides by `N`). The physically sampled weight per bin is `4π k² P(k,E) dk dE`.

## What it shows

| Quantity | Value / feature |
|----------|-----------------|
| Normalization `∫4πk²P dk dE` | **1.0000** (clean parse) |
| `f(E)` peak | **17.5 MeV** — C12 p-shell removal energy |
| `f(E)` shape | p-shell peak → s-shell/continuum step (~25–40 MeV) → tail past 100 MeV; `<E> = 40.9 MeV` |
| `n(k)` peak | **150 MeV/c**, with the correlated short-range high-k tail |
| `(E,k)` ridge | most-probable removal energy rises with `k` — the `P(k,E)` correlation |

## Why it matters

`f(E)` here is the *bare* removal-energy spectrum. **SF + Rosenbluth** (`22a`) carries it
through to reconstructed `E_m` almost unchanged (broad, ~30–50 MeV) because Rosenbluth has
**zero removal-energy dependence**. **SF + UnifiedQEL** (`22b`) starts from the *same* `f(E)`
but its De Forest off-shell weighting — energy transfer shifted to `q̃₀ = q₀ − ε_B` with a
hard `q̃₀ > 0` cut and form factors at `Q̃²` — **down-weights the high-E part**, pulling the
reconstructed `E_m` peak lower (~15–20 MeV). The `(E,k)` ridge is also what the event-level
[2D `E_m` vs `p_m`](README.md#3-2d-missing-energy-vs-momentum-stage--model) SF column reproduces.

- **Figure:** [`spectral_function_c12.png`](spectral_function_c12.png)
- **Generator:** [`plot_spectral_function.py`](plot_spectral_function.py) — `pixi run python results/prd-analyzer-v0/plot_spectral_function.py`
