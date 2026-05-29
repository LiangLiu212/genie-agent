"""PNFS scratch output path scheme for GENIE grid jobs.

    {scratch_base}/{user}/jobsub-agent/{project}/{channel}/{installation}/{tune}/
        {stem}_{kind}/{probe}_{target}_{tune}

`channel` is derived from the generator list (CC/NC/EM); `kind` is `spl` (gmkspl)
or `gev` (gevgen). The worker writes per-process subdirs under this dir.
"""
from __future__ import annotations


def channel_from_genlist(gl: str) -> str:
    up = gl.upper()
    if up.startswith("EM"):
        return "EM"
    if up.startswith("CC") or up == "RES":
        return "CC"
    if up.startswith("NC"):
        return "NC"
    return gl


def output_dir(
    *,
    scratch_base: str,
    user: str,
    project: str,
    installation: str,
    tune: str,
    genlist: str,
    stem: str,
    kind: str,            # "spl" | "gev"
    probe: str,
    target: str,
) -> str:
    channel = channel_from_genlist(genlist)
    return (
        f"{scratch_base.rstrip('/')}/{user}/jobsub-agent/{project}/{channel}/"
        f"{installation}/{tune}/{stem}_{kind}/{probe}_{target}_{tune}"
    )
