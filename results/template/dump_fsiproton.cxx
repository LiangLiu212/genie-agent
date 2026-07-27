// Dump, for QEL hit-proton events in the Dutta Q^2 window, the protons of
// the v0.2 section-5 comparison:
//   - PRIMARY  : the pre-FSI primary QEL proton itself (the status-14
//                hadron-in-the-nucleus whose mother is the hit nucleon) --
//                the vertex proton BEFORE INTRANUKE
//   - LEADING  : the highest-|p| final-state (status 1) proton, any ancestry
//                (the spectrometer-like post-FSI choice of the ladder/signed)
//   - VERTEX   : the leading status-1 proton DESCENDED from the primary,
//                traced through the GHEP daughter links (provenance check)
// plus the event lepton kinematics needed to reconstruct T_p, p_m and the
// restored axis omega - T_p offline.
//
// Selection at dump time: ScatteringTypeId == kScQuasiElastic, hit nucleon =
// proton, |Q^2/1.28 - 1| <= 5 % (Q^2 = -(p_probe - p_fsl)^2, gst-like).
// One CSV line per selected event:
//   q2,omega,qx,qy,qz,le,lpx,lpy,lpz,ve,vpx,vpy,vpz,pe,ppx,ppy,ppz,same,np
// (np = number of status-1 final-state protons, for the v0.3 N_p=1 selection)
// (v* = 0 when the primary proton has no final-state proton descendant --
// absorption or charge exchange; p* = the pre-FSI primary, 0 if not found;
// same = 1 when LEADING and VERTEX are the same GHEP particle.)
// Usage: dump_fsiproton <out.csv> <ghep1.root> [ghep2.root ...]
#include <cstdio>
#include <vector>
#include <TFile.h>
#include <TTree.h>
#include "Framework/EventGen/EventRecord.h"
#include "Framework/GHEP/GHepParticle.h"
#include "Framework/GHEP/GHepStatus.h"
#include "Framework/Ntuple/NtpMCEventRecord.h"
#include "Framework/Interaction/Interaction.h"

static const double Q2_CENTER = 1.28, Q2_FRAC = 0.05;

int main(int argc, char** argv) {
  if (argc < 3) { fprintf(stderr, "usage: %s out.csv ghep...\n", argv[0]); return 1; }
  FILE* out = fopen(argv[1], "w");
  fprintf(out, "q2,omega,qx,qy,qz,le,lpx,lpy,lpz,ve,vpx,vpy,vpz,pe,ppx,ppy,ppz,same,np\n");
  long n_tot = 0, n_kept = 0, n_novtx = 0;
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
      bool qel = event->Summary()->ProcInfo().IsQuasiElastic();
      if (!(qel && nuc && nuc->Pdg() == 2212)) { mcrec->Clear(); continue; }

      genie::GHepParticle* probe = event->Probe();
      genie::GHepParticle* fsl   = event->FinalStatePrimaryLepton();
      TLorentzVector qv = *(probe->P4()) - *(fsl->P4());
      double q2 = -qv.M2();
      if (std::abs(q2 / Q2_CENTER - 1.0) > Q2_FRAC) { mcrec->Clear(); continue; }

      int npart = event->GetEntries();
      int hitpos = event->HitNucleonPosition();

      // the primary QEL proton: status 14, mother = the hit nucleon
      int primary = -1;
      for (int ip = 0; ip < npart; ++ip) {
        genie::GHepParticle* p = event->Particle(ip);
        if (p->Status() == genie::kIStHadronInTheNucleus &&
            p->Pdg() == 2212 && p->FirstMother() == hitpos) { primary = ip; break; }
      }

      // descendants of the primary (BFS over daughter ranges)
      std::vector<bool> desc(npart, false);
      if (primary >= 0) {
        desc[primary] = true;
        for (int ip = primary; ip < npart; ++ip) {   // GHEP daughters come after mothers
          if (!desc[ip]) continue;
          genie::GHepParticle* p = event->Particle(ip);
          int d1 = p->FirstDaughter(), d2 = p->LastDaughter();
          if (d1 >= 0) for (int id = d1; id <= (d2 >= d1 ? d2 : d1); ++id)
            if (id < npart) desc[id] = true;
        }
      }

      int lead = -1, vtx = -1, n_p = 0;
      double plead = -1.0, pvtx = -1.0;
      for (int ip = 0; ip < npart; ++ip) {
        genie::GHepParticle* p = event->Particle(ip);
        if (p->Status() != genie::kIStStableFinalState || p->Pdg() != 2212) continue;
        ++n_p;
        double pm = p->P4()->Vect().Mag();
        if (pm > plead) { plead = pm; lead = ip; }
        if (desc[ip] && pm > pvtx) { pvtx = pm; vtx = ip; }
      }

      double le = 0, lx = 0, ly = 0, lz = 0, ve = 0, vx = 0, vy = 0, vz = 0;
      double pe = 0, px = 0, py = 0, pz = 0;
      if (lead >= 0) {
        genie::GHepParticle* p = event->Particle(lead);
        le = p->E(); lx = p->Px(); ly = p->Py(); lz = p->Pz();
      }
      if (vtx >= 0) {
        genie::GHepParticle* p = event->Particle(vtx);
        ve = p->E(); vx = p->Px(); vy = p->Py(); vz = p->Pz();
      } else { ++n_novtx; }
      if (primary >= 0) {
        genie::GHepParticle* p = event->Particle(primary);
        pe = p->E(); px = p->Px(); py = p->Py(); pz = p->Pz();
      }

      fprintf(out, "%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,"
              "%.6g,%.6g,%.6g,%.6g,%d,%d\n",
              q2, probe->E() - fsl->E(), qv.Px(), qv.Py(), qv.Pz(),
              le, lx, ly, lz, ve, vx, vy, vz, pe, px, py, pz,
              (lead >= 0 && lead == vtx) ? 1 : 0, n_p);
      ++n_kept;
      mcrec->Clear();
    }
    f->Close();
    fprintf(stderr, "done %s (running totals: %ld read, %ld kept, %ld no-vertex-descendant)\n",
            argv[i], n_tot, n_kept, n_novtx);
  }
  fclose(out);
  fprintf(stderr, "TOTAL %ld events, %ld qel-hitp-window kept, %ld without vertex-proton descendant\n",
          n_tot, n_kept, n_novtx);
  return 0;
}
// Build (spack env from the install's setup_env.sh, NOT pixi):
//   source /exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/setup_env.sh
//   g++ -O2 -o dump_fsiproton dump_fsiproton.cxx -I$GENIE/src $(root-config --cflags) \
//       $($GENIE/bin/genie-config --libs) -L$LHAPDF_PKG_DIR/lib -lLHAPDF \
//       -L$LOG4CPP_PKG_DIR/lib -llog4cpp -L$PYTHIA6_LIB_DIR -lPythia6 -lxml2 \
//       -L$GSL_PKG_DIR/lib -lgsl -lgslcblas $(root-config --libs) -lEG -lGeom
// Reads .ghep.root over XRootD (root://...) with BEARER_TOKEN_FILE set.
