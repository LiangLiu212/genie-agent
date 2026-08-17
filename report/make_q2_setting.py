"""Q2 map of one QES-archive (e,e') setting: fixed target, beam energy, angle.

At fixed beam and angle each omega point has Q2 = 4 E (E - omega) sin^2(theta/2).
Left panel: the omega -> Q2 map; right panel: the measured cross section
replotted against Q2. Output: report/<target>_e<E>_th<theta>_q2.png.

Run: pixi run python report/make_q2_setting.py --target 56Fe -e 2.7 --theta 15
(defaults reproduce the original 12C 2.5 GeV / 15 deg figure)
"""

import argparse
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "results" / "template"))
from plot_style import apply_style, new_panels, style_axis, FS_SUPTITLE, DPI

NUC_TEX = {"12C": "$^{12}$C", "56Fe": "$^{56}$Fe"}

ap = argparse.ArgumentParser()
ap.add_argument("--target", choices=sorted(NUC_TEX), default="12C")
ap.add_argument("-e", "--energy", type=float, default=2.5, help="beam energy (GeV)")
ap.add_argument("--theta", type=float, default=15.0, help="scattering angle (deg)")
args = ap.parse_args()
E, THETA = args.energy, args.theta

pts, cites = [], set()
for line in (REPO / "data" / "qes-archive" / f"{args.target}.dat").read_text().splitlines():
    t = line.split()
    if len(t) >= 8 and float(t[2]) == E and float(t[3]) == THETA:
        pts.append((float(t[4]), float(t[5]), float(t[6])))
        cites.add(t[-1])
if not pts:
    sys.exit(f"no {args.target} points at E={E} theta={THETA} in the archive")

s2 = math.sin(math.radians(THETA) / 2) ** 2
om = [p[0] for p in pts]
q2 = [4 * E * (E - o) * s2 for o in om]
sig = [p[1] for p in pts]
err = [p[2] for p in pts]

apply_style()
fig, (axq, axs) = new_panels(ncols=2, sharey=False)
axq.plot(om, q2, "-o", ms=3, color="C0")
style_axis(axq, title="$Q^2$ of each data point",
           xlabel="$\\omega$  [GeV]", ylabel="$Q^2$  [(GeV/c)$^2$]")
axs.errorbar(q2, sig, yerr=err, fmt="o", ms=3, capsize=2, color="C0")
style_axis(axs, title="cross section vs $Q^2$",
           xlabel="$Q^2$  [(GeV/c)$^2$]",
           ylabel="$d\\sigma/d\\Omega\\,d\\omega$  [nb/sr/GeV]")
fig.suptitle(f"{NUC_TEX[args.target]}(e,e')  E = {E:g} GeV, "
             f"$\\theta$ = {THETA:g}°  ({', '.join(sorted(cites))}) — "
             "$Q^2 = 4E(E-\\omega)\\sin^2(\\theta/2)$", fontsize=FS_SUPTITLE)
fig.tight_layout()
prefix = {"12C": "c12", "56Fe": "fe56"}[args.target]
stem = f"{prefix}_e{E:g}_th{THETA:g}_q2".replace(".", "p")
out = REPO / "report" / f"{stem}.png"
fig.savefig(out, dpi=DPI)
print(f"{out}: {len(pts)} points, Q2 {min(q2):.4f}-{max(q2):.4f} (GeV/c)^2, "
      f"peak sigma at omega={om[sig.index(max(sig))]:g} GeV "
      f"-> Q2={q2[sig.index(max(sig))]:.4f}")
