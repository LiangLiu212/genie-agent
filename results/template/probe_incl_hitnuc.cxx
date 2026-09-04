// Probe the GENIE<->INCL struck-nucleon chain at runtime, for N C12 nuclei:
// reset (INCL ground state, pick a proton), resample (uniform p_F ball; with
// local energy on: accept KE > T_loc(r) of the resampled state), then print the
// local energy the vertex applies and the 4-vector handed to the interaction by
// INCLNucleus::getHitNucleonP4() (momentum in the local frame, E = E_loc - V).
// One CSV line per nucleus:
//   r,p_ball,T_ball,vloc,p_i,E_i_minus_m,Em,pmax_isRPValid,useLocE
// where Em = getRemovalEnergy() = m - E_i and pmax_isRPValid = the momentum bound
// of isRPValid at this nucleus (sqrt((E_F - vloc)^2 - m^2)).
// Usage:  probe_incl_hitnuc <N> <out.csv> [NucleusGenINCL param_set: Default|NoLocalEnergy]
// Build (spack env, NOT pixi): source .../GENIE_INCLXX/setup_env.sh, then
//   g++ -O2 -std=c++17 <GENIE's -D flags for INCL> -o probe_incl_hitnuc probe_incl_hitnuc.cxx \
//     -I$GENIE/src -I$INCLXX_DIR/include -I$LOG4CPP_PKG_DIR/include -I$LHAPDF_PKG_DIR/include \
//     -I$GSL_PKG_DIR/include -I/usr/include/libxml2 -I$BOOST_PKG_DIR/include $(root-config --cflags) \
//     $($GENIE/bin/genie-config --libs) -L$INCLXX_DIR/lib <-l each INCL lib> -L$LHAPDF_PKG_DIR/lib \
//     -lLHAPDF -L$LOG4CPP_PKG_DIR/lib -llog4cpp -L$PYTHIA6_LIB_DIR -lPythia6 -lxml2 \
//     -L$GSL_PKG_DIR/lib -lgsl -lgslcblas $(root-config --libs) -lEG -lGeom
// Run with GXMLPATH pointing at genie-agent/tunes.
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
  const char* pset = argc > 3 ? argv[3] : "Default";
  genie::RunOpt::Instance()->SetTuneName("GEM26_44b_05_000");
  genie::RunOpt::Instance()->BuildTune();
  // instantiating NucleusGenINCL runs LoadConfig -> INCLNucleus::configure()
  const genie::Algorithm* alg = genie::AlgFactory::Instance()->GetAlgorithm("genie::NucleusGenINCL", pset);
  if (!alg) { fprintf(stderr, "no NucleusGenINCL/%s\n", pset); return 1; }
  genie::INCLNucleus* incl = genie::INCLNucleus::Instance();
  const bool useLocE = incl->useVertexLocalEnergy();
  fprintf(stderr, "NucleusGenINCL/%s: vertex local energy %s\n", pset, useLocE ? "ON" : "OFF");
  genie::Target tgt(1000060120);
  tgt.SetHitNucPdg(2212);
  FILE* f = fopen(out, "w");
  fprintf(f, "r,p_ball,T_ball,vloc,p_i,E_i_minus_m,Em,pmax_isRPValid,useLocE\n");
  for (int i = 0; i < N; ++i) {
    incl->reset(&tgt);
    incl->ResamplingHitNucleon();
    G4INCL::Particle* hit = incl->getHitParticle();
    const double r  = hit->getPosition().mag();
    const double m  = hit->getMass();
    const double pb = hit->getMomentum().mag();
    const double Tb = hit->getEnergy() - m;
    const double v  = incl->vertexLocE();
    const TLorentzVector p4 = incl->getHitNucleonP4();
    const double Em = incl->getRemovalEnergy();
    // isRPValid bound: largest |p| it accepts here
    double pmax = 0.;
    { double lo = 0., hi = 400.;
      for (int k = 0; k < 40; ++k) { double mid = 0.5*(lo+hi); if (incl->isRPValid(r, mid)) lo = mid; else hi = mid; }
      pmax = lo; }
    fprintf(f, "%.4f,%.3f,%.3f,%.4f,%.3f,%.4f,%.4f,%.2f,%d\n",
            r, pb, Tb, v, p4.Vect().Mag(), p4.E() - m, Em, pmax, useLocE ? 1 : 0);
  }
  fclose(f);
  fprintf(stderr, "wrote %s (%d nuclei)\n", out, N);
  return 0;
}
