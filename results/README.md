# Results

## GEM21_11a EM-QES spline vs EM-MinQ2Limit cut

Total electromagnetic quasi-elastic (EM-QES) cross-section splines for `e-`
on C12 / Fe56 / Au197, generated on the grid for four `GEM21_11a` custom tunes
that differ only in the `EM-MinQ2Limit` (minimum-Q2) parameter.

![EM-QES spline vs Q2 cut](spline_q2cut.png)

| Tune            | EM-MinQ2Limit (GeV²) |
|-----------------|----------------------|
| GEM21_11a_04_000 | 0.54 |
| GEM21_11a_05_000 | 1.18 |
| GEM21_11a_06_000 | 1.70 |
| GEM21_11a_08_000 | 3.15 |

Raising the Q2 floor strips low-Q2 phase space: the cross-section turn-on shifts
to higher energy and the plateau drops by roughly an order of magnitude per step.
The 3.15 GeV² tune sits on the plot's 1e-12 floor (effectively no surviving
EM-QES). Curves are clamped at 1e-12 so the log axis renders zeros.

Tune `GEM21_11a_07_000` (Q2 = 1.73 GeV²) is not yet included — its grid job was
still running when this figure was made.
