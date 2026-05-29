"""jobsub-agent core — a generic jobsub_lite submission toolkit.

This package knows nothing about GENIE. It builds + runs `jobsub_submit`,
tracks jobs as registry-free per-job JSON records under `jobsub-runs/`, polls
`jobsub_q`, cancels/fetches logs, pulls outputs via `ifdh`, and builds/publishes
CVMFS tarballs. The GENIE-specific layer lives in `adapters/genie/`.

Modules are added per the build order in
`.claude/plans/jobsub-agent.md`:
    config.py  submit_env.py  records.py  submit.py  monitor.py
    control.py outputs.py     tarball.py  publish.py
"""
