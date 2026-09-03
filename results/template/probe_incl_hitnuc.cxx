// Probe the GENIE<->INCL hit-nucleon chain at runtime: for N C12 nuclei,
// reset (INCL ground state, pick a proton), print the local energy of the
// ORIGINAL nucleon, resample (uniform p_F ball, KE > locE), then print the
// local energy of the RESAMPLED nucleon and the (E, |p|) the record receives
// via getHitNucleonEnergy/Momentum.  One CSV line per nucleus:
//   r,p_orig,T_orig,vloc_orig,p_ball,T_ball,vloc_after,E_rec,p_rec,univR,maxR
// Build (spack env, NOT pixi):
//   source /exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/setup_env.sh
//   g++ -O2 -o probe_incl_hitnuc probe_incl_hitnuc.cxx -I$GENIE/src \
//     -I$INCLXX_DIR/include $(root-config --cflags) $($GENIE/bin/genie-config --libs) \
//     -L$INCLXX_DIR/lib <INCL libs> ... $(root-config --libs) -lEG -lGeom
// Run with GXMLPATH pointing at genie-agent/tunes:  probe_incl_hitnuc <N> <out.csv>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include "Framework/Algorithm/AlgFactory.h"
#include "Framework/Interaction/Target.h"
#include "Framework/Utils/RunOpt.h"
#include "Physics/NuclearState/INCLNucleus.h"
#include "Physics/NuclearState/NucleusGenINCL.h"
#include "G4INCLKinematicsUtils.hh"
#include "G4INCLNucleus.hh"
#include "G4INCLParticle.hh"

int main(int argc, char** argv) {
  int N = argc > 1 ? atoi(argv[1]) : 2000;
  const char* out = argc > 2 ? argv[2] : "probe_incl_hitnuc.csv";
  genie::RunOpt::Instance()->SetTuneName("GEM26_44b_05_000");
  genie::RunOpt::Instance()->BuildTune();
  // instantiating NucleusGenINCL runs LoadConfig -> INCLNucleus::configure()
  const genie::Algorithm* alg = genie::AlgFactory::Instance()->GetAlgorithm("genie::NucleusGenINCL", "Default");
  if (!alg) { fprintf(stderr, "no NucleusGenINCL\n"); return 1; }
  genie::INCLNucleus* incl = genie::INCLNucleus::Instance();
  genie::Target tgt(1000060120);
  tgt.SetHitNucPdg(2212);
  FILE* f = fopen(out, "w");
  fprintf(f, "r,p_orig,T_orig,vloc_orig,p_ball,T_ball,vloc_after,E_rec,p_rec,univR,maxR\n");
  fprintf(f, "# per nucleus: r, then for throw k=1..3: p_ball,T_ball,vloc_pre, [after getHitNucleonMomentum] T_now,p_now,prefl,V,vloc_mid, X_E=E_ball-E_rec, p_rec\n");
  for (int i = 0; i < N; ++i) {
    incl->reset(&tgt);
    G4INCL::Nucleus* nuc = incl->getNuclues();
    G4INCL::Particle* hit = incl->getHitParticle();
    const double r = hit->getPosition().mag();
    const double m = hit->getMass();
    fprintf(f, "%.4f", r);
    for (int k = 0; k < 3; ++k) {
      incl->ResamplingHitNucleon();
      const double pb = hit->getMomentum().mag(), Tb = hit->getEnergy() - m;
      const double vpre = G4INCL::KinematicsUtils::getLocalEnergy(nuc, hit);
      TVector3 prec = incl->getHitNucleonMomentum();
      const double Tnow = hit->getEnergy() - m, pnow = hit->getMomentum().mag();
      const double prefl = hit->getReflectionMomentum(), V = hit->getPotentialEnergy();
      const double vmid = G4INCL::KinematicsUtils::getLocalEnergy(nuc, hit);
      const double Erec = incl->getHitNucleonEnergy();
      fprintf(f, ",%.3f,%.3f,%.4f,%.3f,%.3f,%.3f,%.3f,%.4f,%.4f,%.3f",
              pb, Tb, vpre, Tnow, pnow, prefl, V, vmid, (hit->getEnergy() - Erec), prec.Mag());
    }
    fprintf(f, "\n");
  }
  fclose(f);
  fprintf(stderr, "wrote %s (%d nuclei)\n", out, N);
  return 0;
}
