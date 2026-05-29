"""Build (and cache) tarballs for jobsub_lite `--tar_file_name dropbox://`.

Generic: `build_tarball` takes the build dir, the top-level trees to include, and
the exclude rules as **parameters** (GENIE's specific lists live in the adapter
and are passed in). The cache key is sha1(build_dir + sorted mtimes of the
selected top-level trees); a cache hit skips the rebuild. `build_overlay_tarball`
is the generic form of genie-mcp's tune tarball (bundle suffix-filtered files
from several subdirs at the archive top level, for a GXMLPATH-style overlay).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Iterable, Optional

_AGENT_ROOT = Path(__file__).resolve().parents[1]
TARBALL_DIR = _AGENT_ROOT / "tarballs"

_GB = 1024 ** 3


# ── cache key ──────────────────────────────────────────────────────────────────

def _walk_mtimes(build_dir: Path, toplevel: Iterable[str], max_depth: int = 2) -> list[float]:
    mtimes: list[float] = []
    for rel in toplevel:
        p = build_dir / rel
        if not p.exists():
            continue
        if p.is_file():
            mtimes.append(p.stat().st_mtime)
            continue
        for child in p.rglob("*"):
            try:
                if len(child.relative_to(p).parts) > max_depth:
                    continue
                mtimes.append(child.stat().st_mtime)
            except (OSError, ValueError):
                pass
    return mtimes


def compute_sha(build_dir: Path, toplevel: Iterable[str]) -> str:
    payload = f"{build_dir.resolve()}|{sorted(_walk_mtimes(build_dir, toplevel))}"
    return hashlib.sha1(payload.encode()).hexdigest()[:12]


# ── exclude filter ──────────────────────────────────────────────────────────────

def make_exclude_filter(components=(), prefixes=(), suffixes=()):
    components, prefixes, suffixes = tuple(components), tuple(prefixes), tuple(suffixes)

    def _filter(tarinfo: tarfile.TarInfo) -> Optional[tarfile.TarInfo]:
        name = tarinfo.name
        if any(c in name.split("/") for c in components):
            return None
        if any(name.startswith(p) for p in prefixes):
            return None
        if suffixes and name.endswith(suffixes):
            return None
        return tarinfo

    return _filter


# ── build ────────────────────────────────────────────────────────────────────

def build_tarball(
    *,
    build_dir: str | Path,
    toplevel_candidates: Iterable[str],
    exclude_components: Iterable[str] = (),
    exclude_prefixes: Iterable[str] = (),
    exclude_suffixes: Iterable[str] = (),
    name_prefix: str = "tarball",
    output_path: Optional[str] = None,
    force: bool = False,
    background: bool = False,
) -> dict:
    build_dir = Path(build_dir)
    if not build_dir.is_dir():
        return {"error": f"build_dir not found: {build_dir}"}

    toplevel = list(toplevel_candidates)
    sha = compute_sha(build_dir, toplevel)
    TARBALL_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(output_path) if output_path else TARBALL_DIR / f"{name_prefix}_{sha}.tar"
    files_included = [rel for rel in toplevel if (build_dir / rel).exists()]

    if out.exists() and not force:
        size_mb = round(out.stat().st_size / 1e6, 1)
        return {"tarball_path": str(out), "sha": sha, "size_mb": size_mb, "cached": True,
                "build_dir": str(build_dir), "files_included": files_included,
                "message": f"Cached tarball reused ({size_mb} MB)."}

    out.parent.mkdir(parents=True, exist_ok=True)

    if background:
        spec = {"build_dir": str(build_dir), "toplevel_candidates": toplevel,
                "exclude_components": list(exclude_components),
                "exclude_prefixes": list(exclude_prefixes),
                "exclude_suffixes": list(exclude_suffixes),
                "name_prefix": name_prefix, "output_path": str(out)}
        fd, spec_path = tempfile.mkstemp(prefix=".tarball-spec.", suffix=".json", dir=str(TARBALL_DIR))
        Path(spec_path).write_text(json.dumps(spec))
        import os
        os.close(fd)
        log_file = out.with_suffix(out.suffix + ".log")
        code = (f"import sys; sys.path.insert(0, {str(_AGENT_ROOT)!r}); "
                f"from lib.tarball import _build_from_spec; _build_from_spec({spec_path!r})")
        proc = subprocess.Popen([sys.executable, "-c", code],
                                stdout=open(log_file, "w"), stderr=subprocess.STDOUT,
                                start_new_session=True, close_fds=True)
        return {"tarball_path": str(out), "sha": sha, "cached": False, "build_dir": str(build_dir),
                "files_included": files_included, "status": "running", "pid": proc.pid,
                "log_file": str(log_file),
                "message": f"Tarball build running in background (PID {proc.pid}); watch {out}"}

    flt = make_exclude_filter(exclude_components, exclude_prefixes, exclude_suffixes)
    with tarfile.open(out, mode="w") as tar:
        for rel in files_included:
            tar.add(build_dir / rel, arcname=rel, filter=flt)

    size_bytes = out.stat().st_size
    size_mb = round(size_bytes / 1e6, 1)
    warnings = []
    if size_bytes > 8 * _GB:
        warnings.append(f"tarball is {size_mb} MB; jobsub_submit may reject files > ~10 GB")
    msg = f"Tarball built: {size_mb} MB, sha={sha}."
    if warnings:
        msg += " WARNING: " + "; ".join(warnings)
    return {"tarball_path": str(out), "sha": sha, "size_mb": size_mb, "cached": False,
            "build_dir": str(build_dir), "files_included": files_included,
            "warnings": warnings, "message": msg}


def _build_from_spec(spec_path: str) -> None:
    """Background entry point: rebuild from a JSON params file (force=True)."""
    spec = json.loads(Path(spec_path).read_text())
    build_tarball(force=True, background=False, **spec)
    try:
        Path(spec_path).unlink()
    except OSError:
        pass


# ── overlay tarball (e.g. GXMLPATH tunes) ──────────────────────────────────────

def _overlay_files(source_dir: Path, subdirs: Iterable[str], include_suffixes) -> list[Path]:
    out: list[Path] = []
    for sub in subdirs:
        d = source_dir / sub
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() in include_suffixes:
                out.append(p)
    return out


def build_overlay_tarball(
    *,
    source_dir: str | Path,
    subdirs: Iterable[str],
    label: str,
    include_suffixes: Iterable[str] = (".xml", ".md"),
    name_prefix: str = "overlay",
    force: bool = False,
) -> dict:
    source_dir = Path(source_dir)
    subdirs = list(subdirs)
    include_suffixes = tuple(s.lower() for s in include_suffixes)
    if not source_dir.is_dir():
        return {"error": f"source_dir not found: {source_dir}"}

    missing = [s for s in subdirs if not (source_dir / s).is_dir()]
    if missing:
        return {"error": f"subdir(s) not found under {source_dir}: {missing}"}
    files = _overlay_files(source_dir, subdirs, include_suffixes)
    if not files:
        return {"error": f"no {include_suffixes} files under {subdirs} in {source_dir}"}

    h = hashlib.sha1("|".join(sorted(subdirs)).encode())
    for f in files:
        st = f.stat()
        h.update(f"\n{f.relative_to(source_dir).as_posix()}|{st.st_size}|{st.st_mtime}".encode())
    sha = h.hexdigest()[:12]

    TARBALL_DIR.mkdir(parents=True, exist_ok=True)
    out = TARBALL_DIR / f"{name_prefix}_{label}_{sha}.tar"
    files_included = [f.relative_to(source_dir).as_posix() for f in files]

    if out.exists() and not force:
        size_mb = round(out.stat().st_size / 1e6, 3)
        return {"tarball_path": str(out), "sha": sha, "size_mb": size_mb, "cached": True,
                "subdirs": sorted(subdirs), "files_included": files_included,
                "message": f"Cached overlay tarball reused ({size_mb} MB)."}

    with tarfile.open(out, mode="w") as tar:
        for f in files:
            tar.add(f, arcname=f.relative_to(source_dir).as_posix())
    size_mb = round(out.stat().st_size / 1e6, 3)
    return {"tarball_path": str(out), "sha": sha, "size_mb": size_mb, "cached": False,
            "subdirs": sorted(subdirs), "files_included": files_included,
            "message": f"Overlay tarball built: {size_mb} MB, sha={sha}, {len(files_included)} file(s)."}
