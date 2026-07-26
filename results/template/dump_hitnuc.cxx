// Dump struck-nucleon kinematics + the SAMPLED removal energy + the in-nucleus
// position from GHEP files.
//
// gst does not carry the nuclear-model removal energy (FermiMover's default
// branch encodes En = M_A - sqrt(p^2 + M_rem_gs^2), a pure function of p), but
// GHepParticle::RemovalEnergy() stores the sampled w for every event; likewise
// gst has no in-nucleus vertex, but the hit nucleon's X4() carries the radial
// position r [fm] set by VertexGenerator. This dumper writes one CSV line per
// single-nucleon event:
//     pdg,px,py,pz,E,w,scattering_type,r
// Usage: dump_hitnuc <out.csv> <ghep1.root> [ghep2.root ...]
#include <cstdio>
#include <TFile.h>
#include <TTree.h>
#include "Framework/EventGen/EventRecord.h"
#include "Framework/GHEP/GHepParticle.h"
#include "Framework/Ntuple/NtpMCEventRecord.h"
#include "Framework/Interaction/Interaction.h"

int main(int argc, char** argv) {
  if (argc < 3) { fprintf(stderr, "usage: %s out.csv ghep...\n", argv[0]); return 1; }
  FILE* out = fopen(argv[1], "w");
  fprintf(out, "pdg,px,py,pz,E,w,scat,r\n");
  long n_tot = 0, n_kept = 0;
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
      genie::GHepParticle* nuc = event->HitNucleon();
      if (nuc && (nuc->Pdg() == 2212 || nuc->Pdg() == 2112)) {
        int scat = event->Summary()->ProcInfo().ScatteringTypeId();
        fprintf(out, "%d,%.6g,%.6g,%.6g,%.6g,%.6g,%d,%.6g\n",
                nuc->Pdg(), nuc->Px(), nuc->Py(), nuc->Pz(), nuc->E(),
                nuc->RemovalEnergy(), scat, nuc->X4()->Vect().Mag());
        ++n_kept;
      }
      mcrec->Clear();
    }
    f->Close();
    fprintf(stderr, "done %s (running totals: %ld read, %ld kept)\n",
            argv[i], n_tot, n_kept);
  }
  fclose(out);
  fprintf(stderr, "TOTAL %ld events, %ld single-nucleon kept\n", n_tot, n_kept);
  return 0;
}
// Build (spack env from the install's setup_env.sh, NOT pixi):
//   source /exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/setup_env.sh
//   g++ -O2 -o dump_hitnuc dump_hitnuc.cxx -I$GENIE/src $(root-config --cflags) \
//       $($GENIE/bin/genie-config --libs) -L$LHAPDF_PKG_DIR/lib -lLHAPDF \
//       -L$LOG4CPP_PKG_DIR/lib -llog4cpp -L$PYTHIA6_LIB_DIR -lPythia6 -lxml2 \
//       -L$GSL_PKG_DIR/lib -lgsl -lgslcblas $(root-config --libs) -lEG -lGeom
// Reads .ghep.root directly over XRootD (root://...) with BEARER_TOKEN_FILE set.
