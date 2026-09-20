# TESS Hidden Architect

### Infer the planet you cannot see.

**TESS Hidden Architect** is a TESS-inspired exoplanet simulation that turns planetary detection into a scientific investigation.

A transiting planet appears to follow an apparently regular orbit. But its transit times contain subtle deviations.

Those deviations can be the gravitational fingerprint of another planet.

The hidden companion is deliberately withheld from the initial observation. Instead of simply being shown the answer, the user must investigate the observations, infer the presence of an unseen body, make a prediction, and finally compare that prediction with the underlying simulated system.

---

## The Core Idea

```text
OBSERVE → INFER → PREDICT → REVEAL
```

The simulation demonstrates a fundamental idea in astronomy:

> **A planet does not always have to be directly observed to leave evidence of its existence.**

A hidden companion gravitationally perturbs the orbit of an observable transiting planet.

That perturbation changes the timing of its transits.

The timing changes become an observable signal known as a **Transit Timing Variation (TTV)**.

The investigation therefore follows:

```text
Hidden Planet
     ↓
Gravitational Perturbation
     ↓
Observed Planet's Orbital Motion Changes
     ↓
Transit Times Shift
     ↓
TTV Signal
     ↓
Inference
     ↓
Prediction
     ↓
Reveal & Validation
```

---

# What You Do

You are not given the complete planetary system at the beginning.

Instead, you:

### 1. OBSERVE

Examine the available observations of the transiting planet.

The hidden companion is intentionally withheld.

### 2. INFER

Investigate the transit timing behaviour and look for evidence that the observed planet is being gravitationally perturbed.

### 3. PREDICT

Use the inferred timing structure to form a prediction about the hidden system.

### 4. REVEAL

The hidden companion is finally exposed.

The inferred behaviour can then be compared against the underlying simulated system.

This separation between **observation, inference, and ground truth** is central to the project.

---

# Why This Matters

Exoplanet discovery is not always about directly seeing a planet.

Astronomers frequently infer the existence and properties of astronomical objects from their effects on other observable systems.

TESS Hidden Architect uses this idea to demonstrate how:

**an invisible cause can produce a measurable consequence.**

The project therefore focuses not only on orbital simulation, but on the reasoning process that connects:

**physics → observation → signal → inference → validation.**

---

# Scientific Foundations

## 1. Newtonian Gravity

The planetary system is evolved using Newtonian gravitational interactions.

For two bodies \(i\) and \(j\):

`F_ij = G m_i m_j (r_j - r_i) / |r_j - r_i|^3`

where:

* `G` = gravitational constant
* `m_i`, `m_j` = masses of the bodies
* `r_i`, `r_j` = position vectors

The acceleration of body `i` is:

`a_i = G Σ[j ≠ i] m_j (r_j - r_i) / |r_j - r_i|^3`

This gravitational interaction is what allows the hidden companion to influence the observable planet.

---

## 2. Equations of Motion

The numerical system evolves according to:

`dr_i/dt = v_i`

and:

`dv_i/dt = a_i`

or:

`d²r_i/dt² = a_i`

The resulting motion is numerically integrated to evolve the planetary system through time.

---

## 3. Keplerian Orbital Period

For a planet orbiting a dominant stellar mass:

`P = 2π √(a³ / [G(M_star + m)])`

For a planet whose mass is much smaller than its host star:

`P ≈ 2π √(a³ / GM_star)`

where:

* `P` = orbital period
* `a` = semi-major axis
* `M_star` = stellar mass
* `m` = planetary mass

This provides the characteristic orbital timescale of the system.

---

## 4. Eccentric Orbital Geometry

For an orbit with eccentricity `e`:

`r = a(1 - e²) / (1 + e cos ν)`

where:

* `a` = semi-major axis
* `e` = eccentricity
* `ν` = true anomaly

The orbital-plane position is represented by:

`r_peri = [r cos ν, r sin ν, 0]`

---

## 5. Orbital Coordinate Transformation

The orbital-plane coordinates are transformed into the inertial reference frame using the standard orbital rotations:

`r = R_z(Ω) R_x(i) R_z(ω) r_peri`

where:

* `i` = orbital inclination
* `Ω` = longitude of ascending node
* `ω` = argument of periapsis

The implementation uses the conventional astronomical inclination:

```text
i = 0°    → face-on
i = 90°   → edge-on
```

This convention is important because an approximately edge-on orbit is required for a transit to be observable from the chosen viewing geometry.

---

# Transit Detection

The observer sees the planetary system projected onto the plane of the sky.

For the implemented observer geometry:

`x_sky = x`

`y_sky = y`

The projected separation between the planet and star is:

`d_sky = √(x² + y²)`

A transit is identified when:

`d_sky ≤ R_star + R_planet`

where:

* `R_star` = stellar radius
* `R_planet` = planetary radius

Thus, transit detection is based on orbital geometry rather than simply displaying a planet visually near the star.

---

# Transit Timing

The simulation records the times of transit events:

`T_1, T_2, T_3, ... , T_N`

For an approximately periodic planet, a reference ephemeris can be represented as:

`T_calc(n) = T_0 + nP`

where:

* `T_0` = reference transit time
* `P` = reference orbital period
* `n` = transit number

The difference between an observed and calculated transit time is:

`ΔT_n = T_obs,n - T_calc,n`

These deviations form the basis of the TTV signal.

---

# Transit Timing Variations

**Transit Timing Variations (TTVs)** are deviations in the measured transit times from a reference periodic prediction.

In an idealized isolated periodic orbit, transit times follow the reference ephemeris closely.

When another planet gravitationally perturbs the orbit, the transit times can shift.

The resulting sequence:

```text
ΔT_1, ΔT_2, ΔT_3, ... , ΔT_N
```

contains information about the underlying gravitational dynamics.

This is the key observational fingerprint used by the simulation.

---

# O-C Residuals

The timing deviation can also be expressed as an **Observed minus Calculated (O-C)** value:

`O-C = T_obs - T_calc`

An O-C sequence makes departures from a simple periodic ephemeris easier to inspect.

The important scientific point is not merely that the timing changes, but that the changes can contain **structure produced by gravitational interactions**.

---

# Transit Photometry

A planetary transit causes the observed stellar flux to decrease.

The normalized flux is:

`F_norm = F(t) / F_0`

where:

* `F(t)` = observed stellar flux
* `F_0` = reference out-of-transit flux

During a transit:

`F_norm < 1`

For a simplified uniform stellar disk, the approximate fractional transit depth is:

`δ ≈ (R_planet / R_star)²`

The project uses transit photometry as part of the observational picture, while the hidden-companion investigation focuses primarily on timing behaviour.

---

# The Planetary System

The demonstration system contains two planets around a host star.

## Planet A — Observable Planet

Planet A is the transiting planet.

Its repeated transits provide the observable timing sequence.

The investigator does not initially receive direct information about the complete planetary system.

## Planet B — Hidden Companion

Planet B is initially withheld from the observational presentation.

Its gravitational influence perturbs Planet A.

That perturbation can produce changes in Planet A's transit timing.

The hidden planet is revealed only during the final validation stage.

---

# Simulation Architecture

```text
                 PHYSICAL SYSTEM
                       │
                       ▼
              Orbital Initialization
                       │
                       ▼
                N-Body Dynamics
                       │
                       ▼
                 Planet Positions
                       │
                       ▼
              Observer Projection
                       │
              ┌────────┴────────┐
              ▼                 ▼
       Transit Detection    Visualization
              │
              ▼
         Transit Times
              │
              ▼
        Timing Analysis
              │
              ▼
      Hidden Companion
          Inference
              │
              ▼
          Prediction
              │
              ▼
            REVEAL
              │
              ▼
       Validation / Comparison
```

---

# Software Structure

The repository separates the major components of the simulation:

```text
src/
└── tess_hidden_architect/
    ├── physics/
    │   ├── orbital dynamics
    │   ├── coordinates
    │   └── gravitational system
    │
    ├── observation/
    │   ├── transit detection
    │   └── synthetic observations
    │
    └── app/
        └── interactive mission interface
```

The exact implementation is contained in the source tree of this repository.

---

# Mission Design

The project deliberately separates:

### Physical truth

The complete simulated planetary system.

### Observation

What the investigator is allowed to see.

### Inference

What can be deduced from the available observations.

### Validation

Comparison of the inferred result with the hidden simulated system.

This prevents the simulation from becoming simply a visualization of a planetary system that the user already knows.

---

# Scientific Design Principles

### Correct orbital convention

The implementation uses the standard astronomical inclination convention:

`0° = face-on`

`90° = edge-on`

### Physical transit geometry

Transit detection uses projected planet-star separation and stellar/planetary radii.

### Numerical gravitational dynamics

The planetary system is evolved using gravitational interactions rather than relying exclusively on a pre-scripted visual animation.

### Hidden information

The companion planet is withheld during the investigation stage.

### Observable consequences

The inference is based on measurable timing behaviour generated by the simulated system.

### Ground-truth validation

The final reveal allows the inferred behaviour to be compared with the underlying simulated system.

---

# TESS Connection

The project is inspired by the observational principles of NASA's **Transiting Exoplanet Survey Satellite (TESS)**.

TESS uses the transit method to search for planets by measuring small changes in stellar brightness when a planet passes between its host star and the observer.

TESS Hidden Architect builds an educational simulation around a related idea:

> What can the behaviour of an observed planet tell us about another planet that is not directly visible?

The project therefore connects:

```text
Transit Observation
        ↓
Orbital Timing
        ↓
Gravitational Perturbation
        ↓
Indirect Evidence
        ↓
Planetary Inference
```

---

# What This Project Demonstrates

The project combines:

* Newtonian gravitational dynamics
* Numerical orbital evolution
* Orbital-coordinate transformations
* Observer-plane projection
* Transit geometry
* Transit-event detection
* Synthetic observational data
* Transit timing analysis
* TTV / O-C analysis
* Scientific inference
* Hidden-system validation
* Interactive scientific visualization

---

# What This Project Is Not

This project is a **scientifically motivated educational simulation**, not a professional exoplanet-analysis pipeline.

It is not intended to be:

* a replacement for professional TESS data-analysis software
* a complete Bayesian parameter-estimation framework
* a precision fit to a specific confirmed exoplanetary system
* a complete model of stellar activity and instrumental systematics
* a claim that the simulated planetary system corresponds to a real observed star system

The goal is to demonstrate the physical reasoning connecting gravitational dynamics with observable timing signatures.

---

# Limitations

The simulation intentionally uses a controlled environment.

Possible simplifications include:

* synthetic rather than archival observational data
* simplified observational noise
* simplified stellar properties
* simplified photometric modelling
* limited planetary-system complexity
* simplified inference compared with professional statistical analyses
* idealized observer geometry

These limitations allow the core scientific relationship between dynamics, observations, and inference to remain understandable and interactive.

---

# Technology

The project uses:

* **Python**
* Numerical gravitational dynamics
* Orbital mechanics
* Transit detection
* Timing analysis
* HTML
* CSS
* JavaScript
* Canvas-based visualization
* Local mission server

---

# Running the Simulation

## Requirements

A Python installation capable of running the project's dependencies is required.

From the project directory:

```cmd
cd F:\Simathon\My_Final_Submission
```

Set the source directory on the Python path:

```cmd
set PYTHONPATH=src
```

Launch the mission server:

```cmd
python -m tess_hidden_architect.app.main
```

The local mission interface is served at:

```text
http://127.0.0.1:8000/
```

Open that address in a browser.

To stop the server:

```text
Ctrl + C
```

---

# Repository Structure

```text
TessHiddenArtifact/
│
├── src/
│   └── tess_hidden_architect/
│       ├── physics/
│       ├── observation/
│       └── app/
│
├── tests/
│
├── README.md
├── pyproject.toml
└── .gitignore
```

---

# Educational Objective

The simulation illustrates an important principle of scientific investigation:

> **Observation is not the same as explanation.**

A measurement can reveal an effect without directly revealing its cause.

The scientific workflow is therefore:

```text
MEASURE
   ↓
IDENTIFY A PATTERN
   ↓
BUILD A MODEL
   ↓
MAKE A PREDICTION
   ↓
TEST THE PREDICTION
```

TESS Hidden Architect turns that workflow into an interactive astronomical investigation.

---

# The Central Message

The entire project can be reduced to one physical idea:

```text
The planet is hidden.
Its gravity is not.
```

A hidden companion can influence an observable planet.

That influence can modify the observable planet's motion.

The modified motion can change transit times.

Those timing changes can provide evidence for the hidden body.

The simulation then lets the investigator test that inference against the underlying system.

---

# Project Philosophy

TESS Hidden Architect is designed around three principles:

### Physics creates the signal.

The observable behaviour originates from the simulated gravitational system.

### Data hides the cause.

The investigator initially sees observations rather than the complete planetary architecture.

### Inference reveals the structure.

The hidden companion is discovered conceptually through its observable gravitational fingerprint and validated during the final reveal.

---

# Final Mission

```text
OBSERVE
   ↓
INFER
   ↓
PREDICT
   ↓
REVEAL
```

**TESS Hidden Architect** transforms orbital mechanics into an investigation of an unseen world.

The goal is not simply to show that a planet exists.

It is to demonstrate **how we can know that something is there even when we cannot see it directly.**
