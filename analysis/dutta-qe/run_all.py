"""Run the whole analysis: cache (seed if missing) -> all figures -> summary.

Usage:
  pixi run python analysis/dutta-qe/run_all.py
"""
from config import CACHE_DIR, TARGETS, TUNES

if __name__ == "__main__":
    missing = [(t, tu) for t in TARGETS for tu in TUNES
               if not (CACHE_DIR / t.lower() / f"{tu}.npz").exists()]
    if missing:
        print(f"{len(missing)} cache file(s) missing — seeding from v0.3")
        from build_cache import seed_from_v03
        seed_from_v03()

    import plot_emiss
    import plot_pmiss
    import summarize
    for target in TARGETS:
        plot_emiss.main(target, sorted(TUNES))
        plot_pmiss.main(target, sorted(TUNES))
    summarize.main()
