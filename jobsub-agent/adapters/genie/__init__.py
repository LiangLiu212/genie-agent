"""GENIE adapter for jobsub-agent — the only GENIE-aware code.

Wraps the generic `lib/` core to submit gmkspl/gevgen grid jobs: resolves
PDGs (via its own thin loader of the repo-shared `shared/pdg.json`), validates
grid-specific rules, builds the GENIE worker args + PNFS paths, and hands a
finished `jobsub_submit` argv to `lib.submit`.

Modules added in build-order step 7:
    pdg.py  pnfs.py  run_gmkspl_grid.py  run_gevgen_grid.py
    templates/{gmkspl_grid.sh,gevgen_grid.sh}
"""
