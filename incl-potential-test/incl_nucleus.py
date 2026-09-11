#!/usr/bin/env python3
"""
incl_nucleus.py: INCL++-style nuclear ground state in numpy
============================================================

One class, `INCLNucleus`, ported function by function from the INCL++ sources
vendored in the genie_inclxx install
(/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/inclxx_genie/inclxx/, file:line
references below are into that tree) and from the GENIE fork's vertex code
(/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator, branch
feature/incl-vertex-local-energy @ 6bd7803d6). Units: MeV, fm.

What it provides
----------------
r-p correlated sampling   sample(n, rng)         ParticleSampler::sampleOneParticleWith[Fuzzy]RPCorrelation
                                                 (incl_physics/src/G4INCLParticleSampler.cc:107-140)
reflection tables         max_r_from_p(p/pF)     NuclearDensity::getMaxRFromP  (G4INCLNuclearDensity.cc:156)
                          min_p_from_r(r)        NuclearDensity::getMinPFromR  (:161), the inverse table
potential energy          potential_energy(T)    NuclearPotentialEnergyIsospin::computePotentialEnergy
                                                 (G4INCLNuclearPotentialEnergyIsospin.cc:28-44), V0 = T_F + S
local energy              local_energy(r, p)     KinematicsUtils::getLocalEnergy (G4INCLKinematicsUtils.cc:44-77)
local frame               local_frame(r, p_vec)  transformToLocalEnergyFrame (:36-42) as the fork's
                                                 INCLNucleus::getHitNucleonP4 (no mutation): E_loc = E - v_loc,
                                                 momentum rescaled on-shell along p_hat
truncated-ball redraw     resample_at_r(r, rng)  the fork's INCLNucleus::ResamplingHitNucleon: |p|^3 uniform on
                                                 [p_min(r)^3, p_F^3] at fixed r (what GENIE's event loop does)

The model (C12 defaults, 6 < A <= 19 only -- the modified harmonic oscillator branch)
------------------------------------------------------------------------------------
* density rho(r) ~ (1 + alpha x^2) exp(-x^2), x = r/a. Parameters: with the default
  fuzzy r-p correlation (coefficient < 1) INCL takes the HFB table
  data/table_radius_hfb.dat (row "6 12": a_p 1.72905, a_n 1.71874, alpha_p 0.849882,
  alpha_n 0.83426; the accessor names are swapped on purpose, ParticleTable.cc:1204-1215,
  1254-1260); with a strict correlation (coefficient >= 1) the mediumDiffuseness /
  mediumRadius[A-1] tables (ParticleTable.cc:137-146: a = 1.72, alpha = 0.84 for A = 12).
  R_max = 5.5 + 0.3 (A - 6)/12 fm (:1226-1227).
* r-p correlation: INCL does not draw r from rho. It integrates the "RP function"
  g(r) = -r^3 drho/dr (NDFModifiedHarmonicOscillator.hh: ModifiedHarmonicOscillatorRP)
  into a CDF F(R), stores the inverse table R(u) with u = F^(1/3) at 60 equidistant
  R nodes (IFunction1D::inverseCDFTable(Math::pow13), InvFInterpolationTable, linear
  interpolation clamped at both ends), and gives each nucleon of momentum p the
  reflection radius R(p/p_F) and a position uniform inside that sphere. Uniformly
  filled nested spheres with dN/dR ~ -R^3 rho' on [0, R_max] reproduce
  rho(r) - rho(R_max): the MHO tail is cut sharply at R_max (6.6 % low at 4.8 fm,
  80 % low in the last 0.1 fm for C12) -- the "deficit beyond 4.5 fm" of
  docs/incl-ground-state-review.md section 1. Checked by the self-test below.
* Fermi momentum p_F = 1.37 hbar c = 270.34 MeV/c (G4INCLGlobals.hh:14,20) times
  (2Z/A)^(1/3) for protons, (2(1 - Z/A))^(1/3) for neutrons
  (G4INCLNuclearPotentialIsospin.cc:38,46); INCL nucleon mass 938.2796 MeV
  (ParticleTable.cc:26); separation energy S = 6.83 MeV (:306);
  V0 = T_F + S = 45.00 MeV for C12.
* energy-dependent potential: V(T) = V0 for T < T_F, else
  max(0, V0 - 0.223 (T - T_F)/(1 - 0.223)).
* local energy v_loc(r, p): the effective Fermi momentum pfl0 is p_F for T <= T_F,
  else sqrt(tf0 (tf0 + 2m)) with tf0 = V(T) - S (0 if tf0 < 0); the local Fermi
  momentum is pfl0 * min_p_from_r(r * R(p/pfl0) / R(p_refl/pfl0)) where p_refl is the
  particle's "reflection momentum" (the uncorrelated momentum x p_F of the fuzzy draw,
  or |p| once rpCorrelate() was called); v_loc = sqrt(p_l^2 + m^2) - m. Zero outside
  R_max.
* fuzzy correlation (default coefficient 0.5 for protons, 0.73 for neutrons,
  G4INCLConfig.cc:60-61): two correlated standard Gaussians turned into uniforms
  (Random::correlatedUniform, G4INCLRandom.cc:146-165), x = u1^(1/3), y = u2^(1/3),
  |p| = y p_F, reflection sphere R(x), uncorrelated momentum x p_F.

Self-test:  pixi run python incl-potential-test/incl_nucleus.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.special import ndtr  # standard normal CDF = INCL Math::gaussianCDF

# ---- INCL constants (file:line into the vendored inclxx tree) -----------------
HC = 197.328                     # utils/include/G4INCLGlobals.hh:14
PF_CONSTANT = 1.37 * HC          # :20, ConstantFermiMomentum (default fermiMomentumType)
INCL_NUCLEON_MASS = 938.2796     # utils/src/G4INCLParticleTable.cc:26 (protons and neutrons)
INCL_SEPARATION_ENERGY = 6.83    # :306, INCLSeparationEnergy (default), target independent
POTENTIAL_ALPHA = 0.223          # incl_physics/src/G4INCLNuclearPotentialEnergyIsospin.cc:18
RP_COEFFICIENT_DEFAULT = {"proton": 0.5, "neutron": 0.73}   # utils/src/G4INCLConfig.cc:60-61
RP_TABLE_NODES = 60              # utils/include/G4INCLIFunction1D.hh:63 (inverseCDFTable nNodes)
# MHO parameters (a, alpha) [fm, 1]
HFB_MHO = {  # data/table_radius_hfb.dat row "Z A a_p a_n alpha_p alpha_n"
    (12, 6): {"proton": (1.72905, 0.849882), "neutron": (1.71874, 0.83426)},
}
MEDIUM_MHO = {  # (mediumDiffuseness[A-1], mediumRadius[A-1]), ParticleTable.cc:137-146
    12: (1.72, 0.84),
}
LOCE_ACCURACY = 1e-4   # InteractionAvatar::locEAccuracy (MeV) -- fixed-point tolerance
LOCE_MAX_ITER = 50     # InteractionAvatar::maxIterLocE


# ---- INCL Random helpers, vectorised ------------------------------------------
def norm_vector(norm, rng):
    """Random::normVector: isotropic direction with the given length(s)."""
    norm = np.asarray(norm, float)
    n = norm.size
    ctheta = 1.0 - 2.0 * rng.random(n)
    stheta = np.sqrt(1.0 - ctheta**2)
    phi = 2.0 * np.pi * rng.random(n)
    return norm[:, None] * np.stack([stheta * np.cos(phi), stheta * np.sin(phi), ctheta], axis=1)


def sphere_vector(rmax, rng):
    """Random::sphereVector: uniform inside the sphere(s) of radius rmax."""
    rmax = np.asarray(rmax, float)
    return norm_vector(rmax * np.cbrt(rng.random(rmax.size)), rng)


def correlated_uniform(coeff, n, rng):
    """Random::correlatedUniform(c): (Phi(x), Phi(y)) with x ~ N(0,1), y = c x + N(0, 1-c^2)."""
    factor = max(0.0, 1.0 - coeff * coeff)
    x = rng.standard_normal(n)
    y = coeff * x + rng.standard_normal(n) * np.sqrt(factor)
    return ndtr(x), ndtr(y)


class Nucleons:
    """A batch of sampled nucleons: positions r_vec (n,3) [fm], momenta p_vec (n,3)
    [MeV/c], and the reflection ("uncorrelated") momentum p_refl (n,) [MeV/c]."""

    def __init__(self, r_vec, p_vec, p_refl, mass):
        self.r_vec, self.p_vec, self.p_refl, self.mass = r_vec, p_vec, p_refl, mass

    @property
    def r(self):
        return np.linalg.norm(self.r_vec, axis=1)

    @property
    def p(self):
        return np.linalg.norm(self.p_vec, axis=1)

    @property
    def E(self):
        return np.sqrt(self.p**2 + self.mass**2)

    @property
    def T(self):
        return self.E - self.mass

    def __len__(self):
        return self.r_vec.shape[0]


class INCLNucleus:
    """INCL++ ground state for one nucleon species of nucleus (A, Z), 6 < A <= 19."""

    def __init__(self, A=12, Z=6, species="proton", rp_coefficient=None, mho=None,
                 n_nodes=RP_TABLE_NODES):
        if not (6 < A <= 19):
            raise NotImplementedError("only the modified-harmonic-oscillator branch (6 < A <= 19) is ported")
        if species not in ("proton", "neutron"):
            raise ValueError("species must be 'proton' or 'neutron'")
        self.A, self.Z, self.species = A, Z, species
        self.rp_coefficient = (RP_COEFFICIENT_DEFAULT[species] if rp_coefficient is None
                               else float(rp_coefficient))
        self.m = INCL_NUCLEON_MASS
        self.S = INCL_SEPARATION_ENERGY
        frac = 2.0 * Z / A if species == "proton" else 2.0 * (1.0 - Z / A)
        self.pF = PF_CONSTANT * np.cbrt(frac)            # NuclearPotentialIsospin::initialize
        self.TF = np.sqrt(self.pF**2 + self.m**2) - self.m
        self.V0 = self.TF + self.S                        # vProton / vNeutron
        # MHO parameters: HFB table when the correlation is fuzzy, medium tables when strict
        if mho is not None:
            self.a, self.alpha = mho
            self.mho_source = "user"
        elif self.rp_coefficient < 1.0:
            try:
                self.a, self.alpha = HFB_MHO[(A, Z)][species]
            except KeyError as e:
                raise NotImplementedError(f"no HFB MHO parameters stored for A={A} Z={Z}; pass mho=(a, alpha)") from e
            self.mho_source = "HFB table_radius_hfb.dat"
        else:
            try:
                self.a, self.alpha = MEDIUM_MHO[A]
            except KeyError as e:
                raise NotImplementedError(f"no medium-table MHO parameters stored for A={A}; pass mho=(a, alpha)") from e
            self.mho_source = "ParticleTable mediumDiffuseness/mediumRadius"
        self.r_max = 5.5 + 0.3 * (A - 6.0) / 12.0        # getMaximumNuclearRadius, 6 <= A <= 19
        self._build_rp_table(n_nodes)

    # ---- density and the r-p correlation table ---------------------------------
    def density(self, r):
        """rho(r) up to normalisation: (1 + alpha x^2) exp(-x^2), x = r/a; 0 beyond R_max."""
        r = np.asarray(r, float)
        x2 = (r / self.a) ** 2
        return np.where(r <= self.r_max, (1.0 + self.alpha * x2) * np.exp(-x2), 0.0)

    def rp_function(self, r):
        """NuclearDensityFunctions::ModifiedHarmonicOscillatorRP::operator(): -r^3 drho/dr up to a
        constant, clipped at 0 -- the density of reflection radii."""
        r = np.asarray(r, float)
        x2 = (r / self.a) ** 2
        return np.maximum(0.0, -2.0 * r * r * x2 * (self.alpha - 1.0 - self.alpha * x2) * np.exp(-x2))

    def _build_rp_table(self, n_nodes):
        # F(R) = int_0^R g / int_0^Rmax g on a fine grid, then INCL's 60 equidistant nodes with
        # values u = F^(1/3), skipping non-increasing nodes (InvFInterpolationTable)
        rf = np.linspace(0.0, self.r_max, 20001)
        g = self.rp_function(rf)
        cdf = np.concatenate([[0.0], np.cumsum(0.5 * (g[1:] + g[:-1]) * np.diff(rf))])
        cdf /= cdf[-1]
        r_nodes = np.linspace(0.0, self.r_max, n_nodes)
        u_nodes = np.cbrt(np.minimum(1.0, np.interp(r_nodes, rf, cdf)))
        keep = [0]
        for i in range(1, n_nodes):
            if u_nodes[i] > u_nodes[keep[-1]]:
                keep.append(i)
        self._r_nodes, self._u_nodes = r_nodes[keep], u_nodes[keep]

    def max_r_from_p(self, x):
        """NuclearDensity::getMaxRFromP(t, p/pF): reflection radius R for momentum ratio x."""
        return np.interp(np.asarray(x, float), self._u_nodes, self._r_nodes)

    def min_p_from_r(self, r):
        """NuclearDensity::getMinPFromR(t, r): p_min(r)/pF, the inverse table."""
        return np.interp(np.asarray(r, float), self._r_nodes, self._u_nodes)

    # ---- sampling ----------------------------------------------------------------
    def sample(self, n, rng):
        """INCL ground-state nucleons: strict (coefficient > 0.99999) or fuzzy r-p correlation,
        exactly as ParticleSampler::updateSampleOneParticleMethods chooses."""
        if self.rp_coefficient > 0.99999:
            return self._sample_strict(n, rng)
        return self._sample_fuzzy(n, rng)

    def _sample_strict(self, n, rng):
        # sampleOneParticleWithRPCorrelation (G4INCLParticleSampler.cc:107-118)
        p_vec = sphere_vector(np.full(n, self.pF), rng)
        p = np.linalg.norm(p_vec, axis=1)
        R = self.max_r_from_p(p / self.pF)
        r_vec = sphere_vector(R, rng)
        return Nucleons(r_vec, p_vec, p, self.m)

    def _sample_fuzzy(self, n, rng):
        # sampleOneParticleWithFuzzyRPCorrelation (:128-140)
        u1, u2 = correlated_uniform(self.rp_coefficient, n, rng)
        x, y = np.cbrt(u1), np.cbrt(u2)
        p_vec = norm_vector(y * self.pF, rng)
        R = self.max_r_from_p(x)
        r_vec = sphere_vector(R, rng)
        return Nucleons(r_vec, p_vec, x * self.pF, self.m)

    def resample_at_r(self, r_vec, rng):
        """The fork's INCLNucleus::ResamplingHitNucleon: at the sampled position, redraw |p|^3
        uniformly on [p_min(r)^3, p_F^3] with an isotropic direction (the truncated p_F ball
        with INCL's ground-state floor); reflection momentum = |p|."""
        r = np.linalg.norm(r_vec, axis=1)
        u = np.clip(self.min_p_from_r(r), 0.0, 1.0)
        pmin3 = u**3 * self.pF**3
        pmag = np.cbrt(pmin3 + rng.random(r.size) * (self.pF**3 - pmin3))
        return Nucleons(r_vec, norm_vector(pmag, rng), pmag, self.m)

    # ---- potential and local energy ------------------------------------------------
    def potential_energy(self, T):
        """NuclearPotentialEnergyIsospin::computePotentialEnergy for a nucleon of kinetic energy T:
        V0 below T_F, then V0 - alpha (T - T_F)/(1 - alpha), clipped at 0."""
        T = np.asarray(T, float)
        v = self.V0 - POTENTIAL_ALPHA * (T - self.TF) / (1.0 - POTENTIAL_ALPHA)
        return np.where(T < self.TF, self.V0, np.maximum(v, 0.0))

    def local_energy(self, r, p, p_refl=None):
        """KinematicsUtils::getLocalEnergy for a nucleon at radius r [fm] with momentum |p| and
        reflection momentum p_refl (default |p|, i.e. an rpCorrelated particle)."""
        r = np.asarray(r, float)
        p = np.asarray(p, float)
        p_refl = p if p_refl is None else np.asarray(p_refl, float)
        m = self.m
        T = np.sqrt(p**2 + m**2) - m
        below = T <= self.TF
        tf0 = self.potential_energy(T) - self.S
        tf0c = np.maximum(tf0, 0.0)
        pfl0 = np.where(below, self.pF, np.sqrt(tf0c * (tf0c + 2.0 * m)))
        ok = (below | (tf0 >= 0.0)) & (r <= self.r_max) & (pfl0 > 0.0)
        pfl0s = np.where(ok, pfl0, 1.0)
        R_refl = self.max_r_from_p(p_refl / pfl0s)
        R_nom = self.max_r_from_p(p / pfl0s)
        ratio = np.where(R_refl > 0.0, R_nom / np.where(R_refl > 0.0, R_refl, 1.0), 1.0)
        pl = pfl0s * self.min_p_from_r(r * ratio)
        vloc = np.sqrt(pl**2 + m**2) - m
        return np.where(ok, vloc, 0.0)

    def local_frame(self, r, p_vec, p_refl=None):
        """The struck nucleon in INCL's local-energy frame, as the fork's getHitNucleonP4:
        E_loc = max(E - v_loc, m), |p_red| = sqrt(E_loc^2 - m^2) along p_hat (on-shell).
        Returns (E_loc, p_red_vec, v_loc)."""
        p = np.linalg.norm(p_vec, axis=1)
        E = np.sqrt(p**2 + self.m**2)
        vloc = self.local_energy(r, p, p_refl)
        Eloc = np.maximum(E - vloc, self.m)
        pred = np.sqrt(np.maximum(Eloc**2 - self.m**2, 0.0))
        scale = np.where(p > 0.0, pred / np.where(p > 0.0, p, 1.0), 1.0)
        return Eloc, p_vec * scale[:, None], vloc

    def describe(self):
        return (f"INCLNucleus A={self.A} Z={self.Z} {self.species}: pF = {self.pF:.3f} MeV/c, "
                f"m = {self.m} MeV, T_F = {self.TF:.3f} MeV, S = {self.S} MeV, V0 = {self.V0:.3f} MeV; "
                f"MHO a = {self.a} fm, alpha = {self.alpha} ({self.mho_source}), R_max = {self.r_max:.3f} fm; "
                f"r-p coefficient = {self.rp_coefficient} ({'strict' if self.rp_coefficient > 0.99999 else 'fuzzy'}); "
                f"table nodes = {self._r_nodes.size}")


# ---- self-test: the strict sampler must reproduce r^2 rho(r) ------------------------
def _self_test(n=400_000, seed=3):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "results" / "template"))
    import histdiag as hd
    rng = np.random.default_rng(seed)
    # (coefficient, table nodes): INCL's 60-node linear table distorts the radial density at the
    # few-% level per 0.14 fm bin; a fine table shows the scheme itself is exact
    for coeff, nodes in ((1.0, 60), (1.0, 3000), (None, 60), (None, 3000)):
        nuc = INCLNucleus(rp_coefficient=coeff, n_nodes=nodes)
        print(nuc.describe())
        nucs = nuc.sample(n, rng)
        edges = np.linspace(0.0, nuc.r_max, 41)
        cnt, _ = np.histogram(nucs.r, edges)
        # what the scheme generates: r^2 [rho(r) - rho(R_max)], integrated over each bin
        rf = np.linspace(0.0, nuc.r_max, 40001)
        f = rf**2 * (nuc.density(rf) - nuc.density(nuc.r_max))
        F = np.concatenate([[0.0], np.cumsum(0.5 * (f[1:] + f[:-1]) * np.diff(rf))])
        model = np.diff(np.interp(edges, rf, F / F[-1])) * cnt.sum()
        r, p = nucs.r, nucs.p
        print(f"  <r> = {r.mean():.3f} fm, rms r = {np.sqrt((r**2).mean()):.3f} fm, <p> = {p.mean():.2f} MeV/c, "
              f"max p = {p.max():.2f}, corr(p, r) = {np.corrcoef(p, r)[0, 1]:+.3f}")
        floor = nuc.pF * nuc.min_p_from_r(r)
        print(f"  fraction below the strict floor p_min(r): {(p < floor).mean():.4f}")
        pull = (cnt - model) / np.sqrt(model)
        print(f"  sampled r vs r^2 [rho(r) - rho(R_max)] (Poisson pulls, {cnt.size} bins): "
              f"chi2/ndf = {(pull**2).sum() / cnt.size:.2f}, max |pull| = {np.abs(pull).max():.2f}")
        hd.describe1d(cnt, edges, name="sampled r [fm]", quiet=True)
    return 0


if __name__ == "__main__":
    sys.exit(_self_test())
