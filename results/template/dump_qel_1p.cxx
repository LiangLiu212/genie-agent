// Dump QEL events with EXACTLY ONE final-state (status 1) proton -- that
// proton is the leading proton by construction. No momentum threshold on the
// proton count, no Q^2 window, no hit-nucleon requirement (the hit-nucleon
// pdg is recorded, not cut on).
//
// Selection at dump time: Summary()->ProcInfo().IsQuasiElastic() and
// n(status-1 protons) == 1. Events with zero final-state protons are dropped,
// never emitted (the v0.1 has-proton fix: no unguarded leading-index sentinel).
// One CSV line per selected event:
//   entry,hitnuc,q2,omega,le,lpx,lpy,lpz,pe,ppx,ppy,ppz,pke
// (q2 = -(p_probe - p_fsl)^2 gst-like; omega = E_probe - E_fsl; pke = proton
// E - M with M from the particle's own 4-vector, not hardcoded.)
// Usage: dump_qel_1p <out.csv> <ghep1.root> [ghep2.root ...]
#include <cstdio>
#include <TFile.h>
#include <TTree.h>
#include "Framework/EventGen/EventRecord.h"
#include "Framework/GHEP/GHepParticle.h"
#include "Framework/GHEP/GHepStatus.h"
#include "Framework/Ntuple/NtpMCEventRecord.h"
#include "Framework/Interaction/Interaction.h"

int main(int argc, char** argv) {
  if (argc < 3) { fprintf(stderr, "usage: %s out.csv ghep...\n", argv[0]); return 1; }
  FILE* out = fopen(argv[1], "w");
  fprintf(out, "entry,hitnuc,q2,omega,le,lpx,lpy,lpz,pe,ppx,ppy,ppz,pke\n");
  long n_tot = 0, n_qel = 0, n_kept = 0;
  for (int i = 2; i < argc; ++i) {
    TFile* f = TFile::Open(argv[i], "READ");
    if (!f || f->IsZombie()) { fprintf(stderr, "cannot open %s\n", argv[i]); return 2; }
    TTree* tree = dynamic_cast<TTree*>(f->Get("gtree"));
    genie::NtpMCEventRecord* mcrec = nullptr;
    tree->SetBranchAddress("gmcrec", &mcrec);
    Long64_t n = tree->GetEntries();
    for (Long64_t ev = 0; ev < n; ++ev) {
      tree->GetEntry(ev);
      genie::EventRecord* event = mcrec->event;
      ++n_tot;
      if (!event->Summary()->ProcInfo().IsQuasiElastic()) { mcrec->Clear(); continue; }
      ++n_qel;

      int npart = event->GetEntries();
      int the_p = -1, n_p = 0;
      for (int ip = 0; ip < npart; ++ip) {
        genie::GHepParticle* p = event->Particle(ip);
        if (p->Status() != genie::kIStStableFinalState || p->Pdg() != 2212) continue;
        ++n_p;
        the_p = ip;
      }
      if (n_p != 1) { mcrec->Clear(); continue; }

      genie::GHepParticle* probe = event->Probe();
      genie::GHepParticle* fsl   = event->FinalStatePrimaryLepton();
      TLorentzVector qv = *(probe->P4()) - *(fsl->P4());
      genie::GHepParticle* nuc = event->HitNucleon();
      genie::GHepParticle* prot = event->Particle(the_p);

      fprintf(out, "%lld,%d,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g\n",
              ev, nuc ? nuc->Pdg() : 0, -qv.M2(), probe->E() - fsl->E(),
              fsl->E(), fsl->Px(), fsl->Py(), fsl->Pz(),
              prot->E(), prot->Px(), prot->Py(), prot->Pz(),
              prot->E() - prot->P4()->M());
      ++n_kept;
      mcrec->Clear();
    }
    f->Close();
    fprintf(stderr, "done %s (running totals: %ld read, %ld qel, %ld qel-1p kept)\n",
            argv[i], n_tot, n_qel, n_kept);
  }
  fclose(out);
  fprintf(stderr, "TOTAL %ld events, %ld qel, %ld qel with exactly one FS proton\n",
          n_tot, n_qel, n_kept);
  return 0;
}
// Build (spack env from the install's setup_env.sh, NOT pixi):
//   source /exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/setup_env.sh
//   g++ -O2 -o dump_qel_1p dump_qel_1p.cxx -I$GENIE/src $(root-config --cflags) \
//       $($GENIE/bin/genie-config --libs) -L$LHAPDF_PKG_DIR/lib -lLHAPDF \
//       -L$LOG4CPP_PKG_DIR/lib -llog4cpp -L$PYTHIA6_LIB_DIR -lPythia6 -lxml2 \
//       -L$GSL_PKG_DIR/lib -lgsl -lgslcblas $(root-config --libs) -lEG -lGeom
// Reads .ghep.root over XRootD (root://...) with BEARER_TOKEN_FILE set.
