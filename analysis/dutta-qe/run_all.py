"""Run the whole analysis: cache (seed/build if missing) -> all figures -> summary.

Missing caches are seeded from v0.3 where available; tunes with a local_gst
source (config TARGETS) are built from the local gst chunks instead. Figure
and summary loops cover the tunes that have a cache per target.

Usage:
  pixi run python analysis/dutta-qe/run_all.py
"""
from config import CACHE_DIR, TARGETS, TUNES

if __name__ == "__main__":
    def missing():
        return [(t, tu) for t in TARGETS for tu in TUNES
                if not (CACHE_DIR / t.lower() / f"{tu}.npz").exists()]

    if missing():
        print(f"{len(missing())} cache file(s) missing — seeding from v0.3")
        from build_cache import local, seed_from_v03
        seed_from_v03()
        for t, tu in missing():
            if tu in TARGETS[t].get("local_gst", {}):
                local(t, tu)

    import plot_emiss
    import plot_pmiss
    import summarize
    from events import tunes_with_cache
    for target in TARGETS:
        plot_emiss.main(target, tunes_with_cache(target))
        plot_pmiss.main(target, tunes_with_cache(target))
    summarize.main()
