"""Q2 map of the 12C(e,e') Zeller:1973ge setting, E = 2.5 GeV, theta = 15 deg.

At fixed beam and angle each omega point has Q2 = 4 E (E - omega) sin^2(theta/2).
Left panel: the omega -> Q2 map; right panel: the measured cross section
replotted against Q2 (QE peak at omega = 0.230 GeV -> Q2 ~ 0.387 (GeV/c)^2).

Run: pixi run python report/make_q2_c12_e2p5_th15.py
"""

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "results" / "template"))
from plot_style import apply_style, new_panels, style_axis, FS_SUPTITLE, DPI

E, THETA = 2.5, 15.0

pts = []
for line in (REPO / "data" / "qes-archive" / "12C.dat").read_text().splitlines():
    t = line.split()
    if len(t) >= 8 and float(t[2]) == E and float(t[3]) == THETA:
        pts.append((float(t[4]), float(t[5]), float(t[6])))

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
fig.suptitle("$^{12}$C(e,e')  E = 2.5 GeV, $\\theta$ = 15°  (Zeller:1973ge) — "
             "$Q^2 = 4E(E-\\omega)\\sin^2(\\theta/2)$", fontsize=FS_SUPTITLE)
fig.tight_layout()
out = REPO / "report" / "c12_e2p5_th15_q2.png"
fig.savefig(out, dpi=DPI)
print(f"{out}: {len(pts)} points, Q2 {min(q2):.4f}-{max(q2):.4f} (GeV/c)^2")
