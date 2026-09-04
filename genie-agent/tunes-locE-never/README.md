# tunes-locE-never — GXMLPATH override: INCL local energy OFF at the QE vertex

A one-file overlay for the `genie_inclxx` install (branch
`feature/incl-vertex-local-energy`): `NucleusGenINCL.xml` is the install's file
with the `Default` param_set's `local-energy-BB` / `local-energy-pi` set to
`never`. Put it FIRST in `GXMLPATH` so it shadows `$GENIE/config/NucleusGenINCL.xml`:

    --gxmlpath genie-agent/tunes-locE-never --gxmlpath genie-agent/tunes

Effect (see `docs/incl-vertex-local-energy-option-plan.md`, convention of
2026-09-04): the scattering (cross section + lepton/proton kinematics) is
computed with INCL's ball nucleon as it is, `(p_ball, E_ball)` on-shell with
the p_min(r) floor, instead of the local-energy-frame nucleon
`(p_red, E_ball − T_loc(r))`; no local-energy transform at the vertex and none
in the cascade. The energy balance (`E_ball − V₀`, products rescaled by INCL)
and the record nucleon `(p_ball, E_ball − V₀)` are the same in both settings. Runs made with it carry this directory in `inputs.gxmlpath` of their
run log; label them (`--label locE-never`) — the tune id stays `GEM26_44b_*`.
The proper replacement is a dedicated tune/sub-tune selecting
`NucleusGenINCL/NoLocalEnergy` (plan step E8).
