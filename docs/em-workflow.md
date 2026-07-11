# Electron (EM) simulation & analysis workflow

End-to-end pipeline for electron–nucleus quasi-elastic (`EMQE`) studies with GENIE: tune →
spline → events → pull → analysis/plots. Built around the worked example in this repo
(GEM26 Rosenbluth tunes, SF vs LFG on C12, JLab E91-013 kinematics). Everything runs through
**`pixi run python …`**.

> **The common loop** (change a tune, regenerate, replot) is in §8 — start there if you already
> have the machinery published.

---

## 0. Environment / prerequisites
- **Active installation** = `genie_inclxx` (`genie-agent/config/genie_env.json` → `active_installation`).
  Switch with that field or `--installation` / `$GENIE_AGENT_INSTALLATION` (must agree).
- **Local runs**: pixi env (Python 3.14). No setup needed beyond `pixi run`.
- **Grid**: a grid node with `jobsub_lite` + a valid token (`htgettoken -a htvaultprod.fnal.gov -i dune`).
- **Pulling /pnfs**: `ifdh` from the larsoft spack env (see §7 / the `pnfs-fetch` skill).

## 1. Tune configuration — `genie-agent/tunes/` (GXMLPATH overlay)
EM tunes are overlays passed with `--gxmlpath genie-agent/tunes`. Two kinds of change:

- **New model / ground state = new CMC family** (own dir, resolves as `_00_000`). Copy stock
  `$GENIE/config/GEM21_11a`, edit `ModelConfiguration.xml`:
  - QEL-EM model: `XSecModel@…/QEL-EM` → e.g. `genie::RosenbluthPXSec/Default`.
  - Ground state: default `NuclearModel` and/or per-nucleus
    `NuclearModel@Pdg=1000060120` → `genie::SpectralFunc/Default` (SF) or `genie::LocalFGM/Default` (LFG).
  - **Drop `EventGenerator.xml`** so Rosenbluth uses the global standard QEL-EM chain
    (`QELEventGenerator/EM-Default` + `PauliBlocker`), not GEM21's SuSAv2 chain.
  - Examples: `GEM26_11a` (Rosenbluth+LFG), `GEM26_22a` (Rosenbluth+SF/C12).
- **New parameter value = PP-variant subdir** `<CMC>/<CMC>_<PP>_000/CommonParam.xml` (PP ≥ 01).
  Used for the EM Q²-cut: `EM-MinQ2Limit` in `[Lepton]` (t04=0.54 … t08=3.15). See the
  `genie-tune` skill (Recipe A/B).

Tune id = `<CMC>_<PP>_000`. Never edit `$GENIE/config`.

## 2. Local verification (genie-agent) — before any grid
```
pixi run python genie-agent/scripts/run_gmkspl.py \
  --probes eminus --targets C12 --genlist EMQE -n 30 -e 10 \
  --tune <TUNE> --gxmlpath genie-agent/tunes --foreground
```
Check: exit 0, non-empty spline (`jq '.outputs.spline_count'` on the run log > 0),
and stdout shows the intended model
(`RosenbluthPXSec`, `SpectralFunc` loading the C12 table, the `EM-MinQ2Limit` value, etc.).
Optionally a small `run_gevgen.py … -n 1000 -e 2.445 --cross-sections <spline>` + `run_gntpc.py -f gst`.

## 3. Publish grid tarballs (`jobsub-tarball`)  — needs a token
- **Install tarball** (once per install; rarely changes):
  ```
  pixi run python jobsub-agent/scripts/tarball.py build \
    --build-dir /exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX \
    --toplevel Generator --toplevel inclxx_genie/install --toplevel setup_env.sh \
    --exclude-component src --exclude-component .git --exclude-suffix .o --exclude-suffix .d
  pixi run python jobsub-agent/scripts/tarball.py publish --tarball <built.tar> --label genie_inclxx
  ```
- **Tune overlay tarball** — **rebuild + republish whenever tunes change**:
  ```
  pixi run python -c "import sys; sys.path.insert(0,'jobsub-agent'); from lib import tarball; \
    print(tarball.build_overlay_tarball(source_dir='genie-agent/tunes', \
    subdirs=['GEM26_11a','GEM26_22a'], label='gem26_emq2lim'))"
  pixi run python jobsub-agent/scripts/tarball.py publish --tarball <overlay.tar> --label gem26_emq2lim --overwrite
  ```
  Verify freshness later: `tarball.py verify --label <label>` (RCDS GCs ~30 days; republish `--overwrite`).

## 4. Splines on the grid (`gmkspl`, `genie-grid`)
One submission per tune (dry-run first):
```
pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py \
  --probes eminus --targets C12 --tune <TUNE> --genlist EMQE -e 10 -n 30 \
  --tarball-label genie_inclxx --tune-tarball-label gem26_emq2lim -N 1 [--dry-run]
```
Splines land at `/pnfs/…/genie_inclxx/<TUNE>/…_spl/…/0000/*.xml`. Cheap — also validates the tarballs.

## 5. Events on the grid (`gevgen`)
After splines complete, per (tune, beam energy):
```
pixi run python jobsub-agent/adapters/genie/run_gevgen_grid.py \
  --probe eminus --target C12 -n 100000 -N 100 -e <BEAM_E> \
  --cross-sections /pnfs/…/<TUNE>/…_spl/…/0000/<spline>.xml \
  --tune <TUNE> --genlist EMQE \
  --tarball-label genie_inclxx --tune-tarball-label gem26_emq2lim [--dry-run]
```
`-N` = processes, `-n` = events **per process** (so `-N 100 -n 100000` = 10M). Rollout:
dry-run all → one **pilot** → confirm a worker writes a full triplet → submit the rest.
The EM Q²-cut per E91-013 point: `EM-MinQ2Limit = Q²_point − 0.10` (t04…t08).

## 6. Track
```
pixi run python jobsub-agent/scripts/job.py list --active
pixi run python jobsub-agent/scripts/job.py status <jobid>
```
Completion = per-process PNFS triplet (`.ghep.root`+`.ghep.status`+`.gst.root`) count == `n_jobs`
(jobsub_q drained + outputs present). See the `jobsub-jobs` skill.

## 7. Pull outputs off /pnfs (`pnfs-fetch`) — NFS reads stall, use `ifdh`
```
export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)
source /cvmfs/larsoft.opensciencegrid.org/setup-env.sh >/dev/null 2>&1
spack load --first ifdhc >/dev/null 2>&1
export IFDH_CP_MAXRETRIES=1
find /pnfs/…/<TUNE>/…_gev/… -name '*.gst.root' > list.txt          # listing is fine
while read F; do ifdh cp "$F" "/exp/dune/data/users/$USER/scratch/$(basename "$F")"; done < list.txt
```
**Stage to `/exp/dune/data` (TBs free), not `/tmp` (~8 GB).** Full 10M ≈ 12 GB per sample.

## 8. Analysis & plots — `results/`
- **Style**: import `results/template/plot_style.py` (`apply_style`, `new_panels`, `style_axis`);
  see the `plot-style` skill.
- **Cross section**: parse the spline XML → σ(E) (`make_spline_gem26_q2cut.py`).
- **Event kinematics**: read gst with `uproot` → Q², struck-nucleon `pn`, removal energy
  `M_N − En`, etc. (`make_q2_gem26_sf_lfg.py`, `make_groundstate_gem26_sf_lfg.py`).
- **(e,e′p) point analysis**: `results/prd-analyzer-v0.1/` (active convergence iteration;
  the exploratory phase is frozen in `results/prd-analyzer-v0/`) — `selection.py`
  (spectrometer `CUTS`, leading-proton + `E_m`/`p_m`, staged selectors) reused by
  `plot_missing.py` / `plot_dists.py` / `plot_2d.py`.
- Generators emit both **log and linear** views; add a page under `results/pages/` (or a sub-dir
  README) and a row in `results/README.md`.

## 9. The change-tune → regenerate → replot loop (the usual case)
1. Edit/add the tune in `genie-agent/tunes/` (§1).
2. Verify locally (§2).
3. **Rebuild + republish the tune overlay tarball** (§3, `--overwrite`) — easy to forget; the grid
   won't see the change otherwise.
4. gmkspl grid → new splines (§4).
5. gevgen grid → new samples (§5); track (§6).
6. Pull gst with `ifdh` to `/exp` scratch (§7).
7. Replot: point an existing generator / `prd-analyzer-v0.1` at the new sample paths (§8).
8. Commit figures + scripts under `results/`.

## Gotchas (learned this session)
- **QE-EM spline is ground-state independent** — SF and LFG give identical `gmkspl` splines.
  Compare **events** (struck-nucleon momentum, missing E/p), not splines.
- **Rosenbluth ⇒ drop `EventGenerator.xml`** (else it runs SuSAv2 kinematics).
- **Republish the overlay after any tune edit** (§3) — most common grid mistake.
- `genie_inclxx` tarball = `Generator` + `inclxx_genie/install` + `setup_env.sh` (data lives under
  `Generator/data`; top-level `data/` is empty).
- Grid workers spack-load deps **by version with `--first`** (never `/hash`).
- Stage pulled gst to `/exp`, not `/tmp`.

## Worked example (this branch, `results-em-qes-q2cut`)
Tunes `GEM26_{11a,22a}` + cut variants t04–t08 → tarballs `genie_inclxx` + `gem26_emq2lim` →
10 grid splines + 12 gevgen submissions (120M events, the 6 E91-013 points, SF & LFG) →
pulled & plotted: spline σ(E), Q², ground-state momentum/removal-energy, and the
`prd-analyzer` (e,e′p) missing-E/p study at Q²=1.28 (now archived as `results/prd-analyzer-v0/`).
