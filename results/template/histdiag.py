#!/usr/bin/env python3
"""
histdiag.py: text readouts of 1D and 2D histograms
==================================================

A PNG hides the bin by bin structure. A text report does not. Every function
here prints a report (and optionally saves it) and returns the same numbers
in a dict, so the interpretation happens on numbers rather than on a
rendered picture.

Inputs are plain numpy histograms (numpy.histogram / numpy.histogram2d
conventions, H[ix, iy] for 2D):

    import numpy as np, histdiag as hd

    edges = np.linspace(0, 3, 31)
    c1, _ = np.histogram(a, edges)
    c2, _ = np.histogram(b, edges)
    hd.compare1d(c1, c2, edges, labels=("data", "MC"))

    H, xe, ye = np.histogram2d(x, y, bins=[40, 40])
    hd.describe2d(H, xe, ye, xname="E_true", yname="E_reco", diagonal=True)
    hd.compare2d(H1, H2, xe, ye, labels=("GENIE", "INCL++"))

ROOT histograms through uproot:

    counts, edges = f["h1"].to_numpy()       # TH1
    errors = f["h1"].errors()
    H, xe, ye = f["h2"].to_numpy()           # TH2, same H[ix, iy] convention

Weighted histograms: pass errors = sqrt(sum of w^2) per bin. Without errors,
Poisson errors sqrt(N) are assumed. Use save="report.txt" (or an open file
object) to keep the report next to the PNG.

What each report contains
-------------------------
describe1d : integral, sparkline of the shape, mean/std/skew/kurtosis, peak
             and FWHM, quantiles, occupied range, edge bin fractions, stat
             precision per bin, optional bin table.
compare1d  : integral ratio; shape descriptors of both and their differences;
             chi2 and KS tests, raw and after scaling to equal integrals; a
             per bin pattern of significant pulls; contiguous runs of same
             sign deviations (a shift shows as ---+++, a bump as one run, a
             width change as + in the core and - in the tails or the reverse);
             tail/core/tail summary; the full bin table; heuristic hints.
describe2d : marginals; Pearson, Spearman and mutual information; densest
             cell and containment; coarse density map; column and row
             normalized maps (the ridge); profile <y> vs x with a straight
             line fit, curvature test, monotonicity pattern, spread vs x and
             asymmetry; the reverse profile; optional diagonal view (bias and
             resolution vs x when y measures x).
compare2d  : integral ratio; marginal comparisons; correlations; profile
             comparison slice by slice with trend slopes; coarse ratio map
             and pull map; chi2; most significant cells; trend of the ratio
             along x and along y (is the difference a flat normalization or
             does it grow with x or y); hints.
"""
from __future__ import annotations

import math

import numpy as np

__all__ = ["describe1d", "compare1d", "describe2d", "compare2d", "rebin1d", "rebin2d"]

SPARK = " .:-=+*#%@"  # 10 levels, empty to max


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _emit(lines, quiet, save):
    text = "\n".join(lines) + "\n"
    if not quiet:
        print(text, end="")
    if save is not None:
        if hasattr(save, "write"):
            save.write(text)
        else:
            with open(save, "w") as fh:
                fh.write(text)
    return text


def _g(v, p=4):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if not np.isfinite(v):
        return "inf" if v > 0 else ("-inf" if v < 0 else "nan")
    return f"{v:.{p}g}"


def _centers(edges):
    edges = np.asarray(edges, float)
    return 0.5 * (edges[1:] + edges[:-1])


def _errs(counts, errors):
    counts = np.asarray(counts, float)
    if errors is None:
        return np.sqrt(np.clip(counts, 0, None))
    errors = np.asarray(errors, float)
    if errors.shape != counts.shape:
        raise ValueError("errors must have the same shape as counts")
    return errors


def _spark(values, width=100):
    v = np.asarray(values, float)
    if v.size > width:
        f = int(math.ceil(v.size / width))
        v = np.add.reduceat(v, np.arange(0, v.size, f))
    if v.size == 0 or not np.isfinite(v).any() or np.nanmax(v) <= 0:
        return " " * v.size
    lv = np.clip(np.nan_to_num(v) / np.nanmax(v), 0, 1)
    idx = np.ceil(lv * (len(SPARK) - 1)).astype(int)
    return "".join(SPARK[i] for i in idx)


def _wmoments(x, w):
    x, w = np.asarray(x, float), np.asarray(w, float)
    s = w.sum()
    out = dict(mean=np.nan, std=np.nan, skew=np.nan, kurt=np.nan)
    if s <= 0:
        return out
    m = (w * x).sum() / s
    d = x - m
    var = (w * d ** 2).sum() / s
    sd = math.sqrt(max(var, 0.0))
    out["mean"], out["std"] = float(m), sd
    if sd > 0:
        out["skew"] = float((w * d ** 3).sum() / s / sd ** 3)
        out["kurt"] = float((w * d ** 4).sum() / s / sd ** 4 - 3.0)
    return out


def _quantiles(counts, edges, qs):
    c = np.clip(np.asarray(counts, float), 0, None)
    tot = c.sum()
    if tot <= 0:
        return [np.nan] * len(qs)
    cdf = np.concatenate([[0.0], np.cumsum(c)]) / tot
    cdf = cdf + np.arange(cdf.size) * 1e-12  # strictly increasing for interp
    return [float(v) for v in np.interp(qs, cdf, edges)]


def _fwhm(counts, edges):
    c = np.asarray(counts, float)
    x = _centers(edges)
    if c.size == 0 or np.nanmax(c) <= 0:
        return np.nan, np.nan, np.nan
    ip = int(np.nanargmax(c))
    half = 0.5 * c[ip]
    i = ip
    while i > 0 and c[i - 1] >= half:
        i -= 1
    xl = float(edges[0]) if i == 0 else x[i - 1] + (half - c[i - 1]) * (x[i] - x[i - 1]) / (c[i] - c[i - 1])
    j = ip
    while j < c.size - 1 and c[j + 1] >= half:
        j += 1
    xr = float(edges[-1]) if j == c.size - 1 else x[j] + (c[j] - half) * (x[j + 1] - x[j]) / (c[j] - c[j + 1])
    return float(xr - xl), float(xl), float(xr)


def _runs(sign):
    """Maximal runs of consecutive nonzero entries of equal sign: (sign, i, j)."""
    sign = np.asarray(sign, int)
    runs, i, n = [], 0, sign.size
    while i < n:
        if sign[i] == 0:
            i += 1
            continue
        j = i
        while j + 1 < n and sign[j + 1] == sign[i]:
            j += 1
        runs.append((int(sign[i]), i, j))
        i = j + 1
    return runs


def _merge_runs(runs, maxgap):
    """Merge runs of equal sign separated by at most maxgap insignificant bins."""
    out = []
    for r in runs:
        if out and out[-1][0] == r[0] and r[1] - out[-1][2] - 1 <= maxgap:
            out[-1] = (r[0], out[-1][1], r[2])
        else:
            out.append(r)
    return out


def _chi2_pvalue(chi2, ndf):
    if not np.isfinite(chi2) or ndf <= 0:
        return np.nan
    try:
        from scipy.stats import chi2 as _c2

        return float(_c2.sf(chi2, ndf))
    except Exception:  # Wilson-Hilferty approximation
        k = float(ndf)
        z = ((chi2 / k) ** (1.0 / 3.0) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
        return 0.5 * math.erfc(z / math.sqrt(2))


def _ks_pvalue(lam):
    if not np.isfinite(lam) or lam <= 0:
        return 1.0
    s = 0.0
    for k in range(1, 200):
        term = 2.0 * (-1) ** (k - 1) * math.exp(-2.0 * k * k * lam * lam)
        s += term
        if abs(term) < 1e-14:
            break
    return float(min(max(s, 0.0), 1.0))


def _wlinfit(x, y, sigma):
    """Weighted straight line y = a + b x (plus a quadratic for curvature)."""
    x, y, sigma = (np.asarray(v, float) for v in (x, y, sigma))
    m = np.isfinite(x) & np.isfinite(y) & np.isfinite(sigma) & (sigma > 0)
    if m.sum() < 3:
        return None
    x, y, w = x[m], y[m], 1.0 / sigma[m] ** 2
    S, Sx, Sy = w.sum(), (w * x).sum(), (w * y).sum()
    Sxx, Sxy = (w * x * x).sum(), (w * x * y).sum()
    D = S * Sxx - Sx * Sx
    if D <= 0:
        return None
    b = (S * Sxy - Sx * Sy) / D
    a = (Sxx * Sy - Sx * Sxy) / D
    chi2 = float((w * (y - a - b * x) ** 2).sum())
    quad = None
    if m.sum() >= 4:
        try:
            coef = np.polyfit(x, y, 2, w=np.sqrt(w))
            quad = dict(c2=float(coef[0]), chi2=float((w * (y - np.polyval(coef, x)) ** 2).sum()))
        except Exception:
            quad = None
    return dict(a=float(a), b=float(b), ea=math.sqrt(Sxx / D), eb=math.sqrt(S / D),
                chi2=chi2, ndf=int(m.sum() - 2), quad=quad, n=int(m.sum()))


def _wcorr(H, xv, yv):
    """Weighted correlation of the x value of each column and y value of each row."""
    W = H.sum()
    if W <= 0:
        return np.nan
    mx_, my_ = H.sum(1), H.sum(0)
    mx = (mx_ * xv).sum() / W
    my = (my_ * yv).sum() / W
    dx, dy = xv - mx, yv - my
    cov = (H * np.outer(dx, dy)).sum() / W
    vx, vy = (mx_ * dx ** 2).sum() / W, (my_ * dy ** 2).sum() / W
    return float(cov / math.sqrt(vx * vy)) if vx > 0 and vy > 0 else np.nan


def _mutual_info(H):
    P = H / H.sum()
    px, py = P.sum(1, keepdims=True), P.sum(0, keepdims=True)
    m = P > 0
    mi = float((P[m] * np.log(P[m] / (px @ py)[m])).sum())
    hx = -float((px[px > 0] * np.log(px[px > 0])).sum())
    hy = -float((py[py > 0] * np.log(py[py > 0])).sum())
    nmi = mi / min(hx, hy) if min(hx, hy) > 0 else np.nan
    return mi, nmi


# --------------------------------------------------------------------------- #
# rebinning
# --------------------------------------------------------------------------- #
def rebin1d(counts, edges, f, errors=None):
    counts, edges = np.asarray(counts, float), np.asarray(edges, float)
    n = counts.size
    if f <= 1:
        return counts, edges, (None if errors is None else np.asarray(errors, float))
    idx = np.arange(0, n, f)
    c = np.add.reduceat(counts, idx)
    e = None if errors is None else np.sqrt(np.add.reduceat(np.asarray(errors, float) ** 2, idx))
    ne = edges[::f]
    if n % f:
        ne = np.append(ne, edges[-1])
    return c, ne, e


def rebin2d(H, xedges, yedges, fx, fy, errors=None):
    H = np.asarray(H, float)
    xe, ye = np.asarray(xedges, float), np.asarray(yedges, float)
    nx, ny = H.shape
    ix, iy = np.arange(0, nx, fx), np.arange(0, ny, fy)
    Hc = np.add.reduceat(np.add.reduceat(H, ix, axis=0), iy, axis=1)
    xec = np.append(xe[::fx], xe[-1]) if nx % fx else xe[::fx]
    yec = np.append(ye[::fy], ye[-1]) if ny % fy else ye[::fy]
    Ec = None
    if errors is not None:
        E2 = np.asarray(errors, float) ** 2
        Ec = np.sqrt(np.add.reduceat(np.add.reduceat(E2, ix, axis=0), iy, axis=1))
    return Hc, xec, yec, Ec


# --------------------------------------------------------------------------- #
# 1D
# --------------------------------------------------------------------------- #
def describe1d(counts, edges, errors=None, name="h", table=False, quiet=False, save=None):
    """Numerical description of one 1D histogram."""
    counts, edges = np.asarray(counts, float), np.asarray(edges, float)
    if counts.ndim != 1 or counts.size != edges.size - 1:
        raise ValueError("counts must be 1D with len(edges) = len(counts) + 1")
    err = _errs(counts, errors)
    x, n = _centers(edges), counts.size
    tot = float(counts.sum())
    L = [f"== 1D  {name}: {n} bins on [{_g(edges[0])}, {_g(edges[-1])}], integral {_g(tot, 6)}"]
    if tot <= 0:
        L.append("   (empty)")
        _emit(L, quiet, save)
        return dict(name=name, integral=tot)
    mom = _wmoments(x, counts)
    qs = (0.05, 0.16, 0.25, 0.50, 0.75, 0.84, 0.95)
    qv = _quantiles(counts, edges, qs)
    fw, fl, fr = _fwhm(counts, edges)
    ip = int(np.argmax(counts))
    nz = np.flatnonzero(counts > 0)
    lo, hi = int(nz[0]), int(nz[-1])
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.where(counts > 0, err / counts, np.nan)
    L.append(f"   shape   |{_spark(counts)}|   (one char per bin, low x -> high x, scaled to the max bin)")
    L.append(f"   mean {_g(mom['mean'])}   std {_g(mom['std'])}   skew {_g(mom['skew'], 3)}   excess kurtosis {_g(mom['kurt'], 3)}")
    L.append(f"   peak    bin {ip}, x = {_g(x[ip])} ({_g(counts[ip], 6)} entries)   FWHM {_g(fw)} on [{_g(fl)}, {_g(fr)}]")
    L.append("   quantiles  " + "  ".join(f"{int(q * 100)}%: {_g(v)}" for q, v in zip(qs, qv)))
    L.append(f"   nonempty bins {lo}..{hi} (x in [{_g(edges[lo])}, {_g(edges[hi + 1])}]);"
             f"  first bin {100 * counts[0] / tot:.2f}%, last bin {100 * counts[-1] / tot:.2f}% of the integral;"
             f"  {int((counts == 0).sum())} empty bins")
    L.append(f"   per bin relative error: median {100 * np.nanmedian(rel):.1f}%, worst nonempty bin {100 * np.nanmax(rel):.1f}%")
    if table:
        L.append("   bin  [lo, hi)                 count       err    frac")
        for i in range(n):
            L.append(f"   {i:3d}  [{_g(edges[i]):>9}, {_g(edges[i + 1]):>9})  {counts[i]:10.5g} {err[i]:9.3g}  {100 * counts[i] / tot:6.2f}%")
    _emit(L, quiet, save)
    return dict(name=name, nbins=n, integral=tot, mean=mom["mean"], std=mom["std"], skew=mom["skew"],
                kurt=mom["kurt"], peak_bin=ip, peak_x=float(x[ip]), peak_count=float(counts[ip]),
                fwhm=fw, fwhm_lo=fl, fwhm_hi=fr, quantiles=dict(zip(qs, qv)), nonempty=(lo, hi),
                counts=counts, errors=err, edges=edges)


def _cmp_arrays(a, b, ea, eb, s):
    """Bin by bin ratio and pulls, raw and after scaling b by s."""
    bs, ebs = b * s, eb * s
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(b > 0, a / b, np.where(a > 0, np.inf, np.nan))
        ratio_err = np.where(b > 0, np.sqrt((ea / b) ** 2 + (a * eb / b ** 2) ** 2), np.nan)
        rshape = np.where(bs > 0, a / bs, np.where(a > 0, np.inf, np.nan))
        v_raw, v_shp = ea ** 2 + eb ** 2, ea ** 2 + ebs ** 2
        pull_raw = np.where(v_raw > 0, (a - b) / np.sqrt(v_raw), np.nan)
        pull_shp = np.where(v_shp > 0, (a - bs) / np.sqrt(v_shp), np.nan)
    return dict(bs=bs, ebs=ebs, ratio=ratio, ratio_err=ratio_err, rshape=rshape,
                v_raw=v_raw, v_shp=v_shp, pull_raw=pull_raw, pull_shp=pull_shp)


def _pull_pattern(p, thr):
    return "".join(" " if not np.isfinite(v) else ("+" if v > thr else ("-" if v < -thr else ".")) for v in p)


def _ratio_pattern(r):
    out = []
    for v in r:
        if not np.isfinite(v):
            out.append("!" if v == np.inf else " ")
        elif v > 1.5:
            out.append("^")
        elif v > 1.1:
            out.append("+")
        elif v >= 0.9:
            out.append("=")
        elif v >= 0.67:
            out.append("-")
        else:
            out.append("v")
    return "".join(out)


def _table_lines(edges, a, b, ea, eb, arr, la, lb):
    L = [f"   bin  [lo, hi)               {la:>10} {lb:>10}    {la}/{lb} ± err     pull raw  pull shape"]
    for i in range(a.size):
        r, re = arr["ratio"][i], arr["ratio_err"][i]
        if np.isfinite(r) and np.isfinite(re):
            rs = f"{r:8.3f} ± {re:6.3f}"
        else:
            rs = f"{('inf' if r == np.inf else 'n/a'):>17}"
        pr = f"{arr['pull_raw'][i]:+8.2f}" if np.isfinite(arr["pull_raw"][i]) else f"{'':>8}"
        ps = f"{arr['pull_shp'][i]:+8.2f}" if np.isfinite(arr["pull_shp"][i]) else f"{'':>8}"
        L.append(f"   {i:3d}  [{_g(edges[i]):>9}, {_g(edges[i + 1]):>9})  {a[i]:10.5g} {b[i]:10.5g}   {rs}    {pr}    {ps}")
    return L


def compare1d(c1, c2, edges, e1=None, e2=None, labels=("A", "B"), thr=2.0, table=True,
              max_table_bins=80, xname="x", quiet=False, save=None):
    """Compare two 1D histograms with the same binning, bin by bin.

    The second histogram is the reference: ratios are c1/c2, pulls are
    positive where c1 is above c2. "shape" quantities are computed after
    scaling c2 to the integral of c1, so they isolate shape differences from
    a normalization difference.
    """
    a, b = np.asarray(c1, float), np.asarray(c2, float)
    edges = np.asarray(edges, float)
    if a.shape != b.shape or a.ndim != 1 or a.size != edges.size - 1:
        raise ValueError("c1 and c2 must be 1D with the same binning as edges")
    ea, eb = _errs(a, e1), _errs(b, e2)
    la, lb = labels
    vn = xname
    x, n = _centers(edges), a.size
    ta, tb = float(a.sum()), float(b.sum())
    L = [f"== 1D compare  {la} vs {lb}: {n} bins on [{_g(edges[0])}, {_g(edges[-1])}]   ({lb} is the reference)"]
    if ta <= 0 or tb <= 0:
        L.append(f"   integrals {_g(ta)} / {_g(tb)}: one histogram is empty, nothing to compare")
        _emit(L, quiet, save)
        return dict(integral=(ta, tb), hints=["one histogram is empty"])

    # normalization -----------------------------------------------------
    sa2, sb2 = float((ea ** 2).sum()), float((eb ** 2).sum())
    sta, stb = math.sqrt(sa2), math.sqrt(sb2)
    rint = ta / tb
    rint_err = rint * math.sqrt((sta / ta) ** 2 + (stb / tb) ** 2)
    norm_sig = (rint - 1) / rint_err if rint_err > 0 else np.inf
    L.append(f"   integrals  {la} {_g(ta, 6)} ± {_g(sta, 3)}   {lb} {_g(tb, 6)} ± {_g(stb, 3)}"
             f"   ratio {la}/{lb} = {rint:.4f} ± {rint_err:.4f}  ({norm_sig:+.1f} sigma from 1)")

    # shape descriptors ---------------------------------------------------
    da = describe1d(a, edges, ea, la, quiet=True)
    db = describe1d(b, edges, eb, lb, quiet=True)
    bw = float(np.median(np.diff(edges)))
    w = max(len(la), len(lb))
    L.append(f"   shape {la:<{w}} |{_spark(a)}|")
    L.append(f"   shape {lb:<{w}} |{_spark(b)}|   (one char per bin, low x -> high x, each scaled to its own max)")
    neff_a = ta ** 2 / sa2 if sa2 > 0 else np.inf
    neff_b = tb ** 2 / sb2 if sb2 > 0 else np.inf
    dm = da["mean"] - db["mean"]
    dm_err = math.sqrt(da["std"] ** 2 / neff_a + db["std"] ** 2 / neff_b)
    dm_sig = dm / dm_err if dm_err > 0 else np.inf
    sr = da["std"] / db["std"] if db["std"] > 0 else np.nan
    fwr = da["fwhm"] / db["fwhm"] if db["fwhm"] > 0 else np.nan
    pk_shift = da["peak_bin"] - db["peak_bin"]
    flat = any(d["fwhm"] > 0.8 * (edges[d["nonempty"][1] + 1] - edges[d["nonempty"][0]]) for d in (da, db))
    L.append(f"   mean   {_g(da['mean'])} vs {_g(db['mean'])}   diff {dm:+.4g} ± {dm_err:.2g}"
             f"  ({dm / bw:+.2f} median bin widths, {dm_sig:+.1f} sigma)")
    L.append(f"   std    {_g(da['std'])} vs {_g(db['std'])}   ratio {sr:.3f}     skew {da['skew']:+.2f} vs {db['skew']:+.2f}")
    L.append(f"   peak   {vn} = {_g(da['peak_x'])} (bin {da['peak_bin']}) vs {vn} = {_g(db['peak_x'])} (bin {db['peak_bin']})"
             f"   shift {pk_shift:+d} bins     FWHM {_g(da['fwhm'])} vs {_g(db['fwhm'])} (ratio {fwr:.3f})"
             + ("   [flat topped: the peak position is not meaningful]" if flat else ""))
    qa, qb = da["quantiles"], db["quantiles"]
    L.append(f"   quantiles {la} minus {lb}:  " + "   ".join(f"{int(q * 100)}%: {qa[q] - qb[q]:+.3g}" for q in (0.05, 0.16, 0.5, 0.84, 0.95)))

    # bin by bin ------------------------------------------------------------
    s = ta / tb
    arr = _cmp_arrays(a, b, ea, eb, s)
    pull_raw, pull_shp, bs = arr["pull_raw"], arr["pull_shp"], arr["bs"]
    ok_raw, ok_shp = np.isfinite(pull_raw), np.isfinite(pull_shp)
    chi2_raw, ndf_raw = float((pull_raw[ok_raw] ** 2).sum()), int(ok_raw.sum())
    chi2_shp, ndf_shp = float((pull_shp[ok_shp] ** 2).sum()), max(int(ok_shp.sum()) - 1, 1)
    p_raw, p_shp = _chi2_pvalue(chi2_raw, ndf_raw), _chi2_pvalue(chi2_shp, ndf_shp)
    cdfa, cdfb = np.cumsum(a) / ta, np.cumsum(b) / tb
    d = cdfa - cdfb
    iks = int(np.argmax(np.abs(d)))
    ks = float(abs(d[iks]))
    if np.isfinite(neff_a) and np.isfinite(neff_b):
        ne = neff_a * neff_b / (neff_a + neff_b)
    else:
        ne = min(neff_a, neff_b)
    lam = (math.sqrt(ne) + 0.12 + 0.11 / math.sqrt(ne)) * ks if np.isfinite(ne) and ne > 0 else np.nan
    p_ks = _ks_pvalue(lam)
    L.append(f"   chi2/ndf   raw {chi2_raw:.1f}/{ndf_raw} (p = {p_raw:.3g})"
             f"   shape, after scaling {lb} by {s:.4f}: {chi2_shp:.1f}/{ndf_shp} (p = {p_shp:.3g})")
    side = "below" if d[iks] > 0 else "above"
    L.append(f"   KS   max |CDF diff| = {ks:.4f} at {vn} = {_g(edges[iks + 1])}"
             f"  ({la} has relatively more entries {side} that x)   p = {p_ks:.3g}")
    L.append(f"   per bin, low x -> high x   (|pull| > {thr:g}:  + {la} above {lb},  - below,  . within,  blank both empty)")
    L.append(f"     pull raw    |{_pull_pattern(pull_raw, thr)}|")
    L.append(f"     pull shape  |{_pull_pattern(pull_shp, thr)}|")
    L.append(f"     ratio shape |{_ratio_pattern(arr['rshape'])}|   (^ >1.5   + 1.1..1.5   = 0.9..1.1   - 0.67..0.9   v <0.67   ! {lb} empty)")

    # runs ------------------------------------------------------------------
    # With many bins the run analysis is done on a rebinned copy (about 40 bins), like the eye does,
    # so that single bin fluctuations do not fragment the pattern.
    fr = int(math.ceil(n / 40)) if n > 60 else 1
    if fr > 1:
        ar, edr, ear = rebin1d(a, edges, fr, ea)
        br, _, ebr = rebin1d(b, edges, fr, eb)
        arr_r = _cmp_arrays(ar, br, ear, ebr, s)
        bsr, vr_, pull_r = arr_r["bs"], arr_r["v_shp"], arr_r["pull_shp"]
        pk = int(np.argmax(br))
    else:
        ar, edr, bsr, vr_, pull_r = a, edges, bs, arr["v_shp"], pull_shp
        pk = db["peak_bin"]
    xr_ = _centers(edr)
    ok_r = np.isfinite(pull_r)
    pabs = np.abs(np.nan_to_num(pull_r))
    sign = np.where(ok_r, np.sign(np.nan_to_num(pull_r)) * (pabs > thr), 0).astype(int)
    raw_runs = _runs(sign)
    kept = [r for r in raw_runs if not (r[1] == r[2] and pabs[r[1]] < 3.0)]  # drop lone bins under 3 sigma
    runs = _merge_runs(kept, maxgap=2)
    run_info = []
    for sg, i, j in runs:
        diff = float((ar[i:j + 1] - bsr[i:j + 1]).sum())
        var = float(vr_[i:j + 1].sum())
        sig = diff / math.sqrt(var) if var > 0 else np.nan
        ref = float(bsr[i:j + 1].sum())
        rel = 100 * diff / ref if ref > 0 else np.nan
        lowstat = (float(ar[i:j + 1].sum()) + ref) < 10
        run_info.append(dict(sign=sg, bins=(i, j), x=(float(edr[i]), float(edr[j + 1])), diff=diff, sigma=sig, rel=rel,
                             lowstat=lowstat, significant=bool(np.isfinite(sig) and abs(sig) >= 3.0 and not lowstat)))
    if run_info:
        L.append(f"   runs of same sign shape deviations ({'rebinned by ' + str(fr) + ' to ' + str(ar.size) + ' bins; ' if fr > 1 else ''}bins beyond {thr:g} sigma,"
                 f" merged across gaps of <= 2 bins, lone bins under 3 sigma dropped; * = combined |sigma| >= 3):")
        for r in run_info:
            i, j = r["bins"]
            L.append(f"     {'*' if r['significant'] else ' '} {'+' if r['sign'] > 0 else '-'}  bins {i}..{j}, {vn} in [{_g(edr[i])}, {_g(edr[j + 1])})"
                     f"   {la} minus scaled {lb} = {r['diff']:+.4g}  ({r['sigma']:+.1f} sigma combined, {r['rel']:+.1f}% of {lb} there)"
                     + ("  [fewer than 10 entries in total: Gaussian pull not reliable]" if r["lowstat"] else ""))
    else:
        L.append(f"   no run of bins deviates by more than {thr:g} sigma after scaling to equal integrals")

    # regions ---------------------------------------------------------------
    q16, q84 = qb[0.16], qb[0.84]
    regions = [(f"left tail  ({vn} < {_g(q16, 3)})", x < q16),
               (f"core       ({vn} in {_g(q16, 3)} .. {_g(q84, 3)})", (x >= q16) & (x <= q84)),
               (f"right tail ({vn} > {_g(q84, 3)})", x > q84)]
    L.append(f"   regions from the 16% and 84% quantiles of {lb}:")
    reg_out = {}
    for name, m in regions:
        if not m.any():
            continue
        sa_, sb_, sbs_ = float(a[m].sum()), float(b[m].sum()), float(bs[m].sum())
        vr, vs = float(arr["v_raw"][m].sum()), float(arr["v_shp"][m].sum())
        pr = (sa_ - sb_) / math.sqrt(vr) if vr > 0 else np.nan
        ps = (sa_ - sbs_) / math.sqrt(vs) if vs > 0 else np.nan
        rr = sa_ / sb_ if sb_ > 0 else np.nan
        rs_ = sa_ / sbs_ if sbs_ > 0 else np.nan
        reg_out[name] = dict(a=sa_, b=sb_, ratio=rr, pull=pr, shape_ratio=rs_, shape_pull=ps)
        L.append(f"     {name:<30} {la} {sa_:10.5g}   {lb} {sb_:10.5g}   raw ratio {rr:.3f} ({pr:+.1f} sigma)"
                 f"   shape ratio {rs_:.3f} ({ps:+.1f} sigma)")

    # hints -----------------------------------------------------------------
    hints = []
    shape_ok = (chi2_shp / ndf_shp < 1.5) and (not np.isfinite(p_shp) or p_shp > 0.01)
    if abs(norm_sig) > 3:
        hints.append(f"normalization: {la} is {100 * (rint - 1):+.1f}% relative to {lb} ({norm_sig:+.1f} sigma)")
    if shape_ok:
        hints.append("after scaling to equal integrals the shapes agree within statistics"
                     + (": a normalization only difference" if abs(norm_sig) > 3 else ""))
    else:
        dq = {q: qa[q] - qb[q] for q in (0.05, 0.16, 0.5, 0.84, 0.95)}
        w68a, w68b = qa[0.84] - qa[0.16], qb[0.84] - qb[0.16]
        w68r = w68a / w68b if w68b > 0 else np.nan
        # location
        if np.isfinite(dm_sig) and abs(dm_sig) > 3:
            same_dir = dq[0.5] != 0 and all(np.sign(v) == np.sign(dq[0.5]) for v in dq.values())
            rigid = same_dir and all(abs(v - dq[0.5]) <= 0.5 * abs(dq[0.5]) for v in dq.values())
            if rigid:
                hints.append(f"rigid shift: every quantile of {la} sits about {dq[0.5]:+.3g} ({dq[0.5] / bw:+.2f} bin widths) from {lb}"
                             f" while the width is unchanged (std ratio {sr:.3f}); {la} is at {'higher' if dq[0.5] > 0 else 'lower'} {vn}")
            else:
                scale_hint = None
                if edges[0] >= 0 and qb[0.16] > 0 and qa[0.16] > 0:
                    qr = [qa[q] / qb[q] for q in (0.16, 0.5, 0.84)]
                    if all(np.isfinite(qr)) and max(qr) - min(qr) <= 0.3 * abs(np.mean(qr) - 1) + 0.02 and abs(np.mean(qr) - 1) > 0.03:
                        scale_hint = (f"multiplicative scale: the 16/50/84% quantiles of {la} are {qr[0]:.3f}, {qr[1]:.3f}, {qr[2]:.3f} times those of {lb},"
                                      f" i.e. {la} ~ {np.mean(qr):.3f} x {lb} (a {100 * (np.mean(qr) - 1):+.1f}% scale difference)")
                if scale_hint:
                    hints.append(scale_hint)
                elif abs(dm / bw) >= 0.25:
                    hints.append(f"location: the mean of {la} is {dm:+.3g} ({dm_sig:+.1f} sigma, {dm / bw:+.2f} bin widths) from {lb};"
                                 f" quantile shifts 16%: {dq[0.16]:+.3g}, 50%: {dq[0.5]:+.3g}, 84%: {dq[0.84]:+.3g} (not a rigid shift)")
        # width
        if np.isfinite(sr) and np.isfinite(w68r) and abs(sr - 1) > 0.05 and abs(w68r - 1) > 0.05 and np.sign(sr - 1) == np.sign(w68r - 1):
            hints.append(f"width: {la} is {'broader' if sr > 1 else 'narrower'} than {lb} (std ratio {sr:.3f}, 68% interval ratio {w68r:.3f}, FWHM ratio {fwr:.3f})")
        # patterns of significant runs
        sig_runs = [r for r in run_info if r["significant"]]
        signs = [r["sign"] for r in sig_runs]
        if flat and sig_runs:
            for r in sig_runs:
                i, j = r["bins"]
                hints.append(f"{'excess' if r['sign'] > 0 else 'deficit'} of {la} for {vn} in [{_g(edr[i])}, {_g(edr[j + 1])}): {r['rel']:+.1f}% ({r['sigma']:+.1f} sigma)"
                             + (" (flat topped distributions: no shift/width reading attempted)" if r is sig_runs[0] else ""))
        elif len(sig_runs) == 1:
            r = sig_runs[0]
            i, j = r["bins"]
            where = "left tail" if xr_[j] < q16 else ("right tail" if xr_[i] > q84 else "core")
            rest = np.ones(ar.size, bool)
            rest[i:j + 1] = False
            rest &= ok_r
            c2r = float((pull_r[rest] ** 2).sum())
            nr = max(int(rest.sum()) - 1, 1)
            tail_txt = "elsewhere the shapes agree" if c2r / nr < 1.5 else f"plus smaller deviations elsewhere (chi2/ndf {c2r:.1f}/{nr} outside the run)"
            hints.append(f"one localized {'excess' if r['sign'] > 0 else 'deficit'} of {la} for {vn} in [{_g(edr[i])}, {_g(edr[j + 1])}) ({where},"
                         f" {r['rel']:+.1f}%, {r['sigma']:+.1f} sigma); {tail_txt}")
        elif len(sig_runs) == 2 and signs[0] == -signs[1] and sig_runs[0]["bins"][1] <= pk <= sig_runs[1]["bins"][0] + 1:
            hints.append(f"pull pattern {'- then +' if signs[0] < 0 else '+ then -'} across the peak: {la} is displaced to"
                         f" {'higher' if signs[0] < 0 else 'lower'} {vn} relative to {lb}")
        elif len(sig_runs) == 3 and signs[0] == signs[2] == -signs[1] and sig_runs[0]["bins"][1] < pk < sig_runs[2]["bins"][0]:
            hints.append(f"pull pattern {'- + -' if signs[1] > 0 else '+ - +'} (core vs both tails): {la} is {'narrower' if signs[1] > 0 else 'broader'} than {lb}")
        elif len(sig_runs) == 2 and signs[0] == signs[1] and sig_runs[0]["bins"][1] < pk < sig_runs[1]["bins"][0]:
            hints.append(f"both tails {'above' if signs[0] > 0 else 'below'} {lb}: {la} is {'broader' if signs[0] > 0 else 'narrower'}")
        elif len(sig_runs) >= 4:
            hints.append(f"{len(sig_runs)} significant runs (pattern {' '.join('+' if s_ > 0 else '-' for s_ in signs)} along {vn}): structured difference, listed below")
        for r in sig_runs:
            if not flat and (len(sig_runs) >= 4 or (len(sig_runs) in (2, 3) and not any("pattern" in h or "tails" in h for h in hints))):
                i, j = r["bins"]
                hints.append(f"  {'excess' if r['sign'] > 0 else 'deficit'} of {la} for {vn} in [{_g(edr[i])}, {_g(edr[j + 1])}): {r['rel']:+.1f}% ({r['sigma']:+.1f} sigma)")
        for name, r in reg_out.items():
            if "tail" in name and np.isfinite(r["shape_pull"]) and abs(r["shape_pull"]) > 3 and abs(r["shape_ratio"] - 1) > 0.1:
                hints.append(f"{name.split('(')[0].strip()}: {la} has {100 * (r['shape_ratio'] - 1):+.0f}% relative to {lb} after normalization ({r['shape_pull']:+.1f} sigma)")
    if not hints:
        hints.append("no clear pattern identified; read the runs and the table")
    L.append("   hints (heuristic; check them against the numbers above):")
    for h in hints:
        L.append(f"     * {h}")

    # table -------------------------------------------------------------------
    if table:
        if n <= max_table_bins:
            L += _table_lines(edges, a, b, ea, eb, arr, la, lb)
        else:
            f = int(math.ceil(n / 40))
            ac, ec_, eac = rebin1d(a, edges, f, ea)
            bc, _, ebc = rebin1d(b, edges, f, eb)
            L.append(f"   ({n} bins: table rebinned by {f}; fine bins with |shape pull| > {thr:g} listed after it)")
            L += _table_lines(ec_, ac, bc, eac, ebc, _cmp_arrays(ac, bc, eac, ebc, s), la, lb)
            flag = np.flatnonzero(ok_shp & (np.abs(np.nan_to_num(pull_shp)) > thr))
            for i in flag:
                L.append(f"     fine bin {i:4d}  [{_g(edges[i])}, {_g(edges[i + 1])})  {la} {a[i]:.5g}  {lb} {b[i]:.5g}"
                         f"  shape ratio {arr['rshape'][i]:.3f}  pull {pull_shp[i]:+.2f}")
    _emit(L, quiet, save)
    return dict(labels=labels, edges=edges, a=a, b=b, integral=(ta, tb), integral_ratio=rint, integral_ratio_err=rint_err,
                norm_sigma=norm_sig, scale=s, mean=(da["mean"], db["mean"]), mean_diff=dm, mean_diff_sig=dm_sig,
                std=(da["std"], db["std"]), std_ratio=sr, fwhm_ratio=fwr, peak_shift_bins=pk_shift, flat_topped=flat,
                quantiles=(qa, qb), ratio=arr["ratio"], ratio_err=arr["ratio_err"], shape_ratio=arr["rshape"],
                pull_raw=pull_raw, pull_shape=pull_shp, chi2_raw=chi2_raw, ndf_raw=ndf_raw, p_raw=p_raw,
                chi2_shape=chi2_shp, ndf_shape=ndf_shp, p_shape=p_shp, ks=ks, ks_x=float(edges[iks + 1]), p_ks=p_ks,
                pattern_raw=_pull_pattern(pull_raw, thr), pattern_shape=_pull_pattern(pull_shp, thr),
                runs=run_info, regions=reg_out, hints=hints)


# --------------------------------------------------------------------------- #
# 2D
# --------------------------------------------------------------------------- #
def _map_lines(M, xec, yec, mode, title, tot=None, thr=2.0):
    """Text map of a coarse 2D array M[ix, iy]: rows y high -> low, columns x low -> high."""
    cx, cy = M.shape
    L = [f"   {title}"]
    if mode == "percent":
        cw = 6

        def cell(v, j, i):
            if not np.isfinite(v) or v <= 0:
                return f"{'.':>{cw}}"
            p = 100 * v / tot
            return f"{'<.1':>{cw}}" if p < 0.05 else f"{p:{cw}.1f}"
    elif mode in ("colnorm", "rownorm"):
        cw = 2
        colmax, rowmax = M.max(axis=1), M.max(axis=0)

        def cell(v, j, i):
            m = colmax[j] if mode == "colnorm" else rowmax[i]
            if not np.isfinite(v) or v <= 0 or m <= 0:
                return f"{'.':>{cw}}"
            return f"{int(math.ceil(9 * v / m)):>{cw}d}"
    elif mode == "ratio":
        cw = 7

        def cell(v, j, i):
            if not np.isfinite(v):
                return f"{('!' if v == np.inf else '.'):>{cw}}"
            return f"{'>99':>{cw}}" if v > 99 else f"{v:{cw}.2f}"
    elif mode == "pull":
        cw = 2

        def cell(v, j, i):
            if not np.isfinite(v):
                return f"{'':>{cw}}"
            if v > 2 * thr:
                c = "#"
            elif v > thr:
                c = "+"
            elif v < -2 * thr:
                c = "="
            elif v < -thr:
                c = "-"
            else:
                c = "."
            return f"{c:>{cw}}"
    else:
        raise ValueError(mode)
    L.append(" " * 25 + "".join(f"{j:>{cw}d}" for j in range(cx)))
    for i in reversed(range(cy)):
        label = f"y{i:<2d} [{_g(yec[i], 3):>7}, {_g(yec[i + 1], 3):>7})"
        L.append(f"   {label:<22}" + "".join(cell(M[j, i], j, i) for j in range(cx)))
    L.append(" " * 25 + "x column index; x edges: " + ", ".join(_g(v, 3) for v in xec))
    return L


def _profile(H, xe, ye, fx):
    """Statistics of y inside slices of x (blocks of fx fine x bins); fine y bins are used."""
    nx, ny = H.shape
    xc, yc = _centers(xe), _centers(ye)
    idx = np.arange(0, nx, fx)
    xec = np.append(xe[::fx], xe[-1]) if nx % fx else xe[::fx]
    rows = []
    for k, i0 in enumerate(idx):
        block = H[i0:i0 + fx]
        col = block.sum(0)
        N = float(col.sum())
        if N > 0:
            xmean = float((block.sum(1) * xc[i0:i0 + fx]).sum() / N)
            mom = _wmoments(yc, col)
            med = _quantiles(col, ye, [0.5])[0]
            mode = float(yc[int(np.argmax(col))])
            err = mom["std"] / math.sqrt(N)
            edge = float((col[0] + col[-1]) / N)
        else:
            xmean, mom, med, mode, err, edge = np.nan, _wmoments(yc, col), np.nan, np.nan, np.nan, np.nan
        rows.append(dict(k=k, i0=int(i0), i1=int(min(i0 + fx, nx)), xlo=float(xec[k]), xhi=float(xec[k + 1]), N=N,
                         xmean=xmean, ymean=mom["mean"], yerr=err, ystd=mom["std"], ymed=med, ymode=mode, edge=edge,
                         spark=_spark(col, width=30)))
    return rows, xec


def _profile_lines(rows, xname, yname, min_n, brief=False):
    L = [f"   profile: <{yname}> inside slices of {xname}   (spark = {yname} distribution in that slice, low -> high, scaled to its own max)"]
    L.append(f"     k  {xname[:10]:<10} slice          N       <{xname[:6]}>        <{yname[:6]}> ± err       std    median      mode  |spark|")
    for r in rows:
        L.append(f"    {r['k']:2d}  [{_g(r['xlo'], 3):>8}, {_g(r['xhi'], 3):>8})  {r['N']:9.5g}  {_g(r['xmean'], 3):>8}   {_g(r['ymean'], 4):>9} ± {_g(r['yerr'], 2):<7}"
                 f" {_g(r['ystd'], 3):>8}  {_g(r['ymed'], 3):>8}  {_g(r['ymode'], 3):>8}  |{r['spark']}|")
    out = dict(fit=None, pattern="", spread=None, asym=np.nan)
    good = [r for r in rows if r["N"] >= min_n and np.isfinite(r["ymean"]) and np.isfinite(r["yerr"]) and r["yerr"] > 0]
    if len(good) >= 3:
        fit = _wlinfit([r["xmean"] for r in good], [r["ymean"] for r in good], [r["yerr"] for r in good])
        out["fit"] = fit
        if fit:
            xr = good[-1]["xmean"] - good[0]["xmean"]
            line = (f"   trend: <{yname}> = {_g(fit['a'], 4)} + ({_g(fit['b'], 4)} ± {_g(fit['eb'], 2)}) * {xname}"
                    f"   ({fit['b'] / fit['eb']:+.1f} sigma from flat; change across the slices {_g(fit['b'] * xr, 3)});"
                    f" straight line chi2/ndf = {fit['chi2']:.1f}/{fit['ndf']}")
            if fit["quad"] and fit["b"] != 0:
                dchi = fit["chi2"] - fit["quad"]["chi2"]
                rel = abs(fit["quad"]["c2"] * xr ** 2 / (fit["b"] * xr)) if xr != 0 else np.nan
                if dchi > 9 and rel > 0.10:
                    verdict = f"clearly curved (quadratic part is {100 * rel:.0f}% of the linear change)"
                elif dchi > 9:
                    verdict = f"mild curvature (quadratic part {100 * rel:.0f}% of the linear change)"
                else:
                    verdict = "no evidence of curvature"
                line += f"; a quadratic term ({_g(fit['quad']['c2'], 3)} {xname}^2) lowers chi2 by {dchi:.1f} -> {verdict}"
            L.append(line)
            cut = [r for r in good if np.isfinite(r["edge"]) and r["edge"] > 0.02]
            if cut:
                L.append(f"   caution: slices {', '.join(str(r['k']) for r in cut)} have > 2% of their entries in the first or last {yname} bin,"
                         f" so the {yname} axis range may be cutting them (biases <{yname}> and the curvature there)")
        pat = []
        for r0, r1 in zip(good[:-1], good[1:]):
            dd = r1["ymean"] - r0["ymean"]
            e = math.hypot(r0["yerr"], r1["yerr"])
            pat.append("+" if dd > 2 * e else ("-" if dd < -2 * e else "."))
        pats = "".join(pat)
        out["pattern"] = pats
        core = [c for c in pat if c != "."]
        nchg = sum(1 for k in range(1, len(core)) if core[k] != core[k - 1])
        L.append(f"   slice to slice change of <{yname}> (+ rises, - falls, . flat within 2 sigma): {pats}"
                 f"   ({'monotonic' if nchg == 0 else str(nchg) + ' direction change(s)'})")
        if not brief:
            s0, s1 = good[0]["ystd"], good[-1]["ystd"]
            sf = _wlinfit([r["xmean"] for r in good], [r["ystd"] for r in good],
                          [r["ystd"] / math.sqrt(2 * r["N"]) if r["ystd"] > 0 else np.nan for r in good])
            out["spread"] = sf
            line = f"   spread: std of {yname} goes from {_g(s0, 3)} (first slice) to {_g(s1, 3)} (last slice)"
            if sf:
                trend = "widening" if sf["b"] > 2 * sf["eb"] else ("narrowing" if sf["b"] < -2 * sf["eb"] else "about constant")
                line += f"; slope {_g(sf['b'], 3)} ± {_g(sf['eb'], 2)} per unit {xname} ({trend} with {xname})"
            L.append(line)
            asym = float(np.mean([(r["ymean"] - r["ymode"]) / r["ystd"] for r in good if r["ystd"] > 0]))
            out["asym"] = asym
            L.append(f"   asymmetry: (<{yname}> minus mode)/std averaged over slices = {asym:+.2f}   (positive = tail towards high {yname})")
    else:
        L.append(f"   (fewer than 3 slices with N >= {min_n}: no trend fit)")
    return L, out


def _diagonal_lines(H, xe, ye, rows, tot, xname, yname):
    xc, yc = _centers(xe), _centers(ye)
    w = max(float(np.diff(xe).max()), float(np.diff(ye).max()))
    XX, YY = np.meshgrid(xc, yc, indexing="ij")
    D = YY - XX
    on = np.abs(D) <= 0.5 * w + 1e-12
    above, below = D > 0.5 * w, D < -0.5 * w
    f_on, f_ab, f_be = H[on].sum() / tot, H[above].sum() / tot, H[below].sum() / tot
    bias = float((H * D).sum() / tot)
    res = float(math.sqrt(max((H * (D - bias) ** 2).sum() / tot, 0.0)))
    L = [f"   diagonal view ({yname} read as a measurement of {xname}; band = |y - x| <= {_g(0.5 * w, 3)}):"
         f" {100 * f_on:.1f}% in the band, {100 * f_ab:.1f}% above (y > x), {100 * f_be:.1f}% below (y < x)"]
    L.append(f"   overall <y - x> = {bias:+.4g}, std(y - x) = {_g(res, 3)}   (bin center approximation)")
    L.append("     k  x slice                  N     <y> - <x>   ± err      std_y   in band")
    out = []
    for r in rows:
        blk = slice(r["i0"], r["i1"])
        Nb = H[blk].sum()
        fb = H[blk][on[blk]].sum() / Nb if Nb > 0 else np.nan
        b_ = r["ymean"] - r["xmean"] if np.isfinite(r["ymean"]) else np.nan
        out.append(dict(k=r["k"], bias=b_, res=r["ystd"], in_band=fb))
        L.append(f"    {r['k']:2d}  [{_g(r['xlo'], 3):>8}, {_g(r['xhi'], 3):>8})  {r['N']:9.5g}   {b_:+10.4g}  ± {_g(r['yerr'], 2):<7} {_g(r['ystd'], 3):>8}  {100 * fb:6.1f}%")
    return L, dict(frac_on=f_on, frac_above=f_ab, frac_below=f_be, bias=bias, resolution=res, slices=out)


def describe2d(H, xedges, yedges, xname="x", yname="y", coarse=(10, 10), diagonal=False,
               profile_min_n=10, quiet=False, save=None):
    """Numerical description of one 2D histogram H[ix, iy]."""
    H = np.asarray(H, float)
    xe, ye = np.asarray(xedges, float), np.asarray(yedges, float)
    if H.ndim != 2 or H.shape != (xe.size - 1, ye.size - 1):
        raise ValueError("H must be H[ix, iy] with shape (len(xedges) - 1, len(yedges) - 1)")
    nx, ny = H.shape
    tot = float(H.sum())
    xc, yc = _centers(xe), _centers(ye)
    L = [f"== 2D  x = {xname} ({nx} bins on [{_g(xe[0])}, {_g(xe[-1])}])   y = {yname} ({ny} bins on [{_g(ye[0])}, {_g(ye[-1])}])   integral {_g(tot, 6)}"]
    if tot <= 0:
        L.append("   (empty)")
        _emit(L, quiet, save)
        return dict(integral=tot)
    mx, my = H.sum(1), H.sum(0)
    dx = describe1d(mx, xe, name=xname, quiet=True)
    dy = describe1d(my, ye, name=yname, quiet=True)
    for nm, dd, mm in ((xname, dx, mx), (yname, dy, my)):
        q = dd["quantiles"]
        L.append(f"   {nm[:12]:<12} marginal |{_spark(mm, 60)}|  mean {_g(dd['mean'])}  std {_g(dd['std'])}  peak {_g(dd['peak_x'])}"
                 f"  16/50/84%: {_g(q[0.16])} / {_g(q[0.5])} / {_g(q[0.84])}")
    r = _wcorr(H, xc, yc)
    rho = _wcorr(H, np.cumsum(mx) - mx / 2, np.cumsum(my) - my / 2)
    mi, nmi = _mutual_info(H)
    L.append(f"   dependence: Pearson r = {r:+.3f}   Spearman rho = {rho:+.3f}   mutual information {mi:.3f} nat, normalized {nmi:.3f} (0 = independent)")
    imax = np.unravel_index(int(np.argmax(H)), H.shape)
    flat = np.sort(H.ravel())[::-1]
    cum = np.cumsum(flat) / tot
    n68, n95 = int(np.searchsorted(cum, 0.68) + 1), int(np.searchsorted(cum, 0.95) + 1)
    order = np.argsort(H.ravel())[::-1][:n95]
    ix95, iy95 = np.unravel_index(order, H.shape)
    L.append(f"   densest cell: x in [{_g(xe[imax[0]])}, {_g(xe[imax[0] + 1])}), y in [{_g(ye[imax[1]])}, {_g(ye[imax[1] + 1])}):"
             f" {_g(H[imax], 5)} entries ({100 * H[imax] / tot:.2f}%)")
    L.append(f"   occupancy: {100 * (H == 0).mean():.0f}% of cells empty; 68% of entries in the {n68} densest cells ({100 * n68 / H.size:.1f}% of cells),"
             f" 95% in {n95} ({100 * n95 / H.size:.1f}%); the 95% set spans x in [{_g(xe[ix95.min()])}, {_g(xe[ix95.max() + 1])}],"
             f" y in [{_g(ye[iy95.min()])}, {_g(ye[iy95.max() + 1])}]")
    fx, fy = int(math.ceil(nx / coarse[0])), int(math.ceil(ny / coarse[1]))
    Hc, xec, yec, _ = rebin2d(H, xe, ye, fx, fy)
    L += _map_lines(Hc, xec, yec, "percent", f"density map ({Hc.shape[0]} x {Hc.shape[1]} coarse cells, cell = % of all entries; rows y high -> low, columns x low -> high)", tot=tot)
    L += _map_lines(Hc, xec, yec, "colnorm", "column normalized (each x column scaled to its own max: 9 = that column's max, . = empty): where y sits at each x, the ridge")
    L += _map_lines(Hc, xec, yec, "rownorm", "row normalized (each y row scaled to its own max): where x sits at each y")
    rows, _ = _profile(H, xe, ye, fx)
    lines, prof = _profile_lines(rows, xname, yname, profile_min_n)
    L += lines
    rowsT, _ = _profile(H.T, ye, xe, fy)
    lines, profT = _profile_lines(rowsT, yname, xname, profile_min_n, brief=True)
    L += lines
    diag = None
    if diagonal:
        lines, diag = _diagonal_lines(H, xe, ye, rows, tot, xname, yname)
        L += lines
    _emit(L, quiet, save)
    return dict(integral=tot, x=dx, y=dy, pearson=r, spearman=rho, mutual_info=mi, normalized_mi=nmi,
                densest=(int(imax[0]), int(imax[1])), n68=n68, n95=n95, coarse=Hc, xedges_coarse=xec, yedges_coarse=yec,
                profile=rows, profile_fit=prof, reverse_profile=rowsT, reverse_profile_fit=profT, diagonal=diag)


def compare2d(H1, H2, xedges, yedges, e1=None, e2=None, labels=("A", "B"), xname="x", yname="y",
              coarse=(10, 10), thr=2.0, profile_min_n=10, quiet=False, save=None):
    """Compare two 2D histograms H[ix, iy] with the same binning. H2 is the reference."""
    A, B = np.asarray(H1, float), np.asarray(H2, float)
    xe, ye = np.asarray(xedges, float), np.asarray(yedges, float)
    if A.shape != B.shape or A.ndim != 2 or A.shape != (xe.size - 1, ye.size - 1):
        raise ValueError("H1 and H2 must be 2D with the same binning as xedges/yedges")
    EA, EB = _errs(A, e1), _errs(B, e2)
    la, lb = labels
    nx, ny = A.shape
    tA, tB = float(A.sum()), float(B.sum())
    L = [f"== 2D compare  {la} vs {lb}   x = {xname} ({nx} bins), y = {yname} ({ny} bins)   ({lb} is the reference)"]
    if tA <= 0 or tB <= 0:
        L.append(f"   integrals {_g(tA)} / {_g(tB)}: one histogram is empty")
        _emit(L, quiet, save)
        return dict(integral=(tA, tB), hints=["one histogram is empty"])
    sA, sB = math.sqrt((EA ** 2).sum()), math.sqrt((EB ** 2).sum())
    rint = tA / tB
    rint_err = rint * math.sqrt((sA / tA) ** 2 + (sB / tB) ** 2)
    norm_sig = (rint - 1) / rint_err if rint_err > 0 else np.inf
    L.append(f"   integrals  {la} {_g(tA, 6)} ± {_g(sA, 3)}   {lb} {_g(tB, 6)} ± {_g(sB, 3)}   ratio {rint:.4f} ± {rint_err:.4f} ({norm_sig:+.1f} sigma from 1)")

    # marginals ---------------------------------------------------------------
    marg = {}
    for nm, ax, ed in ((xname, 1, xe), (yname, 0, ye)):
        c = compare1d(A.sum(ax), B.sum(ax), ed, np.sqrt((EA ** 2).sum(ax)), np.sqrt((EB ** 2).sum(ax)),
                      labels=labels, thr=thr, table=False, xname=nm, quiet=True)
        marg[nm] = c
        pk_txt = "peak shift n/a (flat topped)" if c["flat_topped"] else f"peak shift {c['peak_shift_bins']:+d} bins"
        L.append(f"   {nm} marginal: shape chi2/ndf {c['chi2_shape']:.1f}/{c['ndf_shape']} (p = {c['p_shape']:.2g}),"
                 f" KS D = {c['ks']:.3f} (p = {c['p_ks']:.2g}), mean diff {c['mean_diff']:+.3g} ({c['mean_diff_sig']:+.1f} sigma),"
                 f" std ratio {c['std_ratio']:.3f}, {pk_txt}")
        L.append(f"     shape pull pattern |{c['pattern_shape']}|")
        for h in c["hints"]:
            L.append(f"     * {h}")

    # dependence --------------------------------------------------------------
    xc, yc = _centers(xe), _centers(ye)
    corr = {}
    for nm, M in ((la, A), (lb, B)):
        mx, my = M.sum(1), M.sum(0)
        corr[nm] = (_wcorr(M, xc, yc), _wcorr(M, np.cumsum(mx) - mx / 2, np.cumsum(my) - my / 2), _mutual_info(M)[1])
    L.append(f"   dependence   Pearson r: {la} {corr[la][0]:+.3f}, {lb} {corr[lb][0]:+.3f}"
             f"   Spearman: {la} {corr[la][1]:+.3f}, {lb} {corr[lb][1]:+.3f}   normalized MI: {la} {corr[la][2]:.3f}, {lb} {corr[lb][2]:.3f}")

    # profiles ----------------------------------------------------------------
    fx, fy = int(math.ceil(nx / coarse[0])), int(math.ceil(ny / coarse[1]))
    ra, _ = _profile(A, xe, ye, fx)
    rb, _ = _profile(B, xe, ye, fx)
    L.append(f"   profile <{yname}> inside slices of {xname}:")
    L.append(f"     k  x slice                 N_{la[:6]:<6}    N_{lb[:6]:<6}     <y>_{la[:6]:<6}    <y>_{lb[:6]:<6}   diff (sigma)    std_{la[:6]:<6}  std_{lb[:6]:<6}")
    prof_rows = []
    for p, q in zip(ra, rb):
        dd = p["ymean"] - q["ymean"]
        e = math.hypot(p["yerr"] if np.isfinite(p["yerr"]) else 0.0, q["yerr"] if np.isfinite(q["yerr"]) else 0.0)
        sig = dd / e if (e > 0 and p["N"] >= profile_min_n and q["N"] >= profile_min_n) else np.nan
        prof_rows.append(dict(k=p["k"], x=(p["xlo"], p["xhi"]), ymean=(p["ymean"], q["ymean"]), diff=dd, sigma=sig, std=(p["ystd"], q["ystd"])))
        L.append(f"    {p['k']:2d}  [{_g(p['xlo'], 3):>8}, {_g(p['xhi'], 3):>8})  {p['N']:10.5g}  {q['N']:10.5g}   {_g(p['ymean'], 4):>10}  {_g(q['ymean'], 4):>10}"
                 f"   {dd:+9.3g} ({sig:+5.1f})   {_g(p['ystd'], 3):>9}  {_g(q['ystd'], 3):>9}")
    fits = {}
    for nm, rows in ((la, ra), (lb, rb)):
        good = [r for r in rows if r["N"] >= profile_min_n and np.isfinite(r["ymean"]) and r["yerr"] > 0]
        fits[nm] = _wlinfit([r["xmean"] for r in good], [r["ymean"] for r in good], [r["yerr"] for r in good]) if len(good) >= 3 else None
    if fits[la] and fits[lb]:
        db_ = fits[la]["b"] - fits[lb]["b"]
        eb_ = math.hypot(fits[la]["eb"], fits[lb]["eb"])
        L.append(f"   trend slope d<{yname}>/d{xname}:  {la} {_g(fits[la]['b'], 4)} ± {_g(fits[la]['eb'], 2)}   {lb} {_g(fits[lb]['b'], 4)} ± {_g(fits[lb]['eb'], 2)}"
                 f"   difference {db_ / eb_ if eb_ > 0 else np.nan:+.1f} sigma")
    sig_rows = [r for r in prof_rows if np.isfinite(r["sigma"]) and abs(r["sigma"]) > thr]
    if sig_rows:
        L.append("   slices where <y> differs by more than " + f"{thr:g} sigma: " + ", ".join(f"k={r['k']} ({r['sigma']:+.1f})" for r in sig_rows))
    with np.errstate(divide="ignore", invalid="ignore"):
        std_ratio = [r["std"][0] / r["std"][1] if r["std"][1] > 0 else np.nan for r in prof_rows]
    L.append(f"   std ratio {la}/{lb} per slice: " + " ".join(f"{v:.2f}" if np.isfinite(v) else " n/a" for v in std_ratio)
             + "   (spread of y at each x; values far from 1.00 mean a resolution or width difference there)")

    # coarse maps -------------------------------------------------------------
    Ac, xec, yec, EAc = rebin2d(A, xe, ye, fx, fy, EA)
    Bc, _, _, EBc = rebin2d(B, xe, ye, fx, fy, EB)
    s = tA / tB
    arr = _cmp_arrays(Ac, Bc, EAc, EBc, s)
    Bs = arr["bs"]
    with np.errstate(divide="ignore", invalid="ignore"):
        rerr = np.where(Bs > 0, np.sqrt((EAc / Bs) ** 2 + (Ac * arr["ebs"] / Bs ** 2) ** 2), np.nan)
    rshape, pull = arr["rshape"], arr["pull_shp"]
    L += _map_lines(rshape, xec, yec, "ratio", f"shape ratio map on the coarse grid: {la} / ({lb} scaled by {s:.4f})   (. both empty, ! {lb} empty)")
    L += _map_lines(pull, xec, yec, "pull", f"pull map of the same:  # > {2 * thr:g}   + > {thr:g}   . within   - < -{thr:g}   = < -{2 * thr:g}   (positive = {la} above)", thr=thr)
    ok = np.isfinite(pull)
    chi2c, ndfc = float((pull[ok] ** 2).sum()), max(int(ok.sum()) - 1, 1)
    fine = _cmp_arrays(A, B, EA, EB, s)["pull_shp"]
    okf = np.isfinite(fine)
    chi2f, ndff = float((fine[okf] ** 2).sum()), max(int(okf.sum()) - 1, 1)
    L.append(f"   shape chi2/ndf   coarse cells {chi2c:.1f}/{ndfc} (p = {_chi2_pvalue(chi2c, ndfc):.3g})   fine cells {chi2f:.1f}/{ndff} (p = {_chi2_pvalue(chi2f, ndff):.3g})")
    flat_idx = np.argsort(-np.abs(np.nan_to_num(pull)).ravel())
    top = []
    for f_ in flat_idx[:8]:
        j, i = np.unravel_index(int(f_), pull.shape)
        if not np.isfinite(pull[j, i]) or abs(pull[j, i]) <= thr:
            break
        top.append((j, i))
    if top:
        L.append("   most significant coarse cells:")
        for j, i in top:
            L.append(f"     x in [{_g(xec[j], 3)}, {_g(xec[j + 1], 3)}), y in [{_g(yec[i], 3)}, {_g(yec[i + 1], 3)}):"
                     f"  {la} {Ac[j, i]:.5g}   scaled {lb} {Bs[j, i]:.5g}   ratio {rshape[j, i]:.3f}   pull {pull[j, i]:+.1f}")
    XX, YY = np.meshgrid(_centers(xec), _centers(yec), indexing="ij")
    m = np.isfinite(rshape) & np.isfinite(rerr) & (rerr > 0)
    grad = {}
    for nm, V, span in ((xname, XX, xe[-1] - xe[0]), (yname, YY, ye[-1] - ye[0])):
        gfit = _wlinfit(V[m], rshape[m], rerr[m])
        grad[nm] = gfit
        if gfit:
            L.append(f"   ratio trend along {nm}: slope {_g(gfit['b'], 3)} ± {_g(gfit['eb'], 2)} per unit ({gfit['b'] / gfit['eb']:+.1f} sigma from flat;"
                     f" change of the ratio across the full {nm} range {gfit['b'] * span:+.3f})")

    # hints -------------------------------------------------------------------
    hints = []
    if abs(norm_sig) > 3:
        hints.append(f"normalization: {la} is {100 * (rint - 1):+.1f}% relative to {lb} ({norm_sig:+.1f} sigma)")
    if chi2c / ndfc < 1.5 and chi2f / ndff < 1.5:
        hints.append("after scaling to equal integrals the 2D shapes agree within statistics" + (" (normalization only difference)" if abs(norm_sig) > 3 else ""))
    for nm, gfit in grad.items():
        if gfit and abs(gfit["b"] / gfit["eb"]) > 3:
            hints.append(f"the {la}/{lb} ratio {'rises' if gfit['b'] > 0 else 'falls'} with {nm} ({gfit['b'] / gfit['eb']:+.1f} sigma): not a flat normalization difference")
    n_valid = sum(1 for r in prof_rows if np.isfinite(r["sigma"]))
    if sig_rows and len(sig_rows) <= 3 and n_valid >= 6:
        ks = [r["k"] for r in sig_rows]
        hints.append(f"the <{yname}> profile differs only in slice(s) {', '.join(str(k) for k in ks)}"
                     f" ({xname} in [{_g(min(r['x'][0] for r in sig_rows), 3)}, {_g(max(r['x'][1] for r in sig_rows), 3)})); the other slices agree")
    elif fits[la] and fits[lb]:
        db_ = fits[la]["b"] - fits[lb]["b"]
        eb_ = math.hypot(fits[la]["eb"], fits[lb]["eb"])
        if eb_ > 0 and abs(db_ / eb_) > 3 and fits[lb]["b"] != 0:
            hints.append(f"the <{yname}> vs {xname} trend is {'steeper' if db_ > 0 else 'flatter'} in {la} than in {lb} ({db_ / eb_:+.1f} sigma;"
                         f" slope ratio {fits[la]['b'] / fits[lb]['b']:.3f}, i.e. a {100 * (fits[la]['b'] / fits[lb]['b'] - 1):+.1f}% scale difference in <{yname}>)")
    wide = [r for r in prof_rows if np.isfinite(r["std"][1]) and r["std"][1] > 0 and abs(r["std"][0] / r["std"][1] - 1) > 0.15 and r["ymean"][0] == r["ymean"][0]]
    if wide and len(wide) <= 3:
        hints.append(f"the spread of {yname} differs by more than 15% in slice(s) {', '.join(str(r['k']) for r in wide)} only")
    for nm, c in marg.items():
        for h in c["hints"]:
            if "normalization" not in h and "agree" not in h:
                hints.append(f"{nm} marginal: {h}")
    if ok.any() and chi2c > 0:
        p2 = np.sort(pull[ok] ** 2)[::-1]
        kconc = int(np.searchsorted(np.cumsum(p2), 0.7 * chi2c) + 1)
        if kconc <= 4 and top:
            cells = top[:kconc]
            xs = [xec[j] for j, _ in cells] + [xec[j + 1] for j, _ in cells]
            ys = [yec[i] for _, i in cells] + [yec[i + 1] for _, i in cells]
            hints.append(f"{100 * float(p2[:kconc].sum() / chi2c):.0f}% of the chi2 comes from {kconc} coarse cell(s) with {xname} in [{_g(min(xs), 3)}, {_g(max(xs), 3)})"
                         f" and {yname} in [{_g(min(ys), 3)}, {_g(max(ys), 3)}): a localized {'excess' if pull[cells[0]] > 0 else 'deficit'} of {la}, not a global shape difference")
    if not hints:
        hints.append("no clear pattern identified; read the maps and the profile table")
    L.append("   hints (heuristic; check them against the numbers above):")
    for h in hints:
        L.append(f"     * {h}")
    _emit(L, quiet, save)
    return dict(labels=labels, integral=(tA, tB), integral_ratio=rint, integral_ratio_err=rint_err, norm_sigma=norm_sig, scale=s,
                marginals=marg, correlations=corr, profile=prof_rows, profile_fits=fits, coarse=(Ac, Bc), xedges_coarse=xec,
                yedges_coarse=yec, shape_ratio=rshape, shape_ratio_err=rerr, pull=pull, chi2_coarse=chi2c, ndf_coarse=ndfc,
                chi2_fine=chi2f, ndf_fine=ndff, top_cells=top, ratio_trend=grad, hints=hints)


if __name__ == "__main__":
    rng = np.random.default_rng(1)
    edges = np.linspace(-4, 4, 41)
    a = rng.normal(0.0, 1.0, 20000)
    b = rng.normal(0.15, 1.0, 20000)
    c1, _ = np.histogram(a, edges)
    c2, _ = np.histogram(b, edges)
    compare1d(c1, c2, edges, labels=("A", "B"), table=False)
    x = rng.uniform(0.2, 3.0, 50000)
    y = 0.9 * x + rng.normal(0.0, 0.08 + 0.08 * x)
    H, xe, ye = np.histogram2d(x, y, bins=[30, 30], range=[[0, 3], [0, 3]])
    describe2d(H, xe, ye, xname="E_true", yname="E_reco", diagonal=True)
