# TESS: THE HIDDEN ARCHITECT

> **A TESS-inspired exoplanet simulation where you infer a hidden planetary companion from noisy transit-timing variations.**

---

## Overview

**TESS Hidden Architect** turns exoplanet detection into an investigation.

You begin with observations of a transiting planet whose light curve looks deceptively regular. The simulation deliberately withholds the hidden companion, so its existence cannot simply be read from the visualization. Instead, you must examine and figure out the hidden celestial body.

The simulation combines a physically motivated orbital system, numerical N-body dynamics, synthetic observations, transit detection, inference, and a final reveal. After a prediction is made, withheld information exposes the hidden companion and allows the inferred timing structure to be compared with the underlying system.

The goal is to capture the scientific reasoning behind exoplanet discovery: the most interesting worlds may not be directly visible, but their gravitational influence can leave measurable fingerprints in the data.

---

# Scientific Agenda

The central scientific idea is:

> **A celestial body does not always need to be directly observed for its gravitational influence to be measurable.**

A transiting planet can act as an observational probe of another planet.

If a second planet gravitationally perturbs the orbit of the observed planet, the times at which the observed planet crosses the stellar disk can shift slightly.

These changes are known as **Transit Timing Variations (TTVs)**.

The simulation turns this principle into an interactive investigation:

```text
OBSERVE → INFER → PREDICT → REVEAL
```

The user initially sees the consequences of the planetary system rather than the complete system itself.

---

# Scientific Workflow

The simulation separates four important layers:

### 1. Physical system

The underlying planetary system contains the star, the observed transiting planet, and a hidden companion.

### 2. Observation

The physical state is converted into observable quantities such as projected positions, transit events, transit times, and stellar brightness changes.

### 3. Inference

The observer uses the available timing information to investigate the possibility of a hidden gravitational companion.

### 4. Validation

The hidden system is eventually revealed, allowing the inferred properties and timing behaviour to be compared with the underlying simulated system.

This separation is important because the simulation is intended to demonstrate **scientific inference**, rather than simply displaying an already-known answer.

---

# Physics & Mathematical Model

## 1. Newtonian Gravitational Dynamics

The planetary system is evolved using Newtonian gravitational interactions.

The force between two bodies is:

$$
\mathbf{F}_{ij}
=
G
\frac{m_i m_j}
{|\mathbf{r}_j-\mathbf{r}_i|^3}
(\mathbf{r}_j-\mathbf{r}_i)
$$

where:

* \(G\) is the gravitational constant
* \(m_i,m_j\) are the masses of the interacting bodies
* \(\mathbf r_i,\mathbf r_j\) are their position vectors

The acceleration of body \(i\) is therefore:

$$
\mathbf{a}_i
=
G
\sum_{j\ne i}
m_j
\frac{\mathbf r_j-\mathbf r_i}
{|\mathbf r_j-\mathbf r_i|^3}
$$

This interaction is what allows the hidden companion to gravitationally perturb the observed planet.

---

## 2. Equations of Motion

The numerical evolution follows:

$$
\frac{d\mathbf r_i}{dt}
=
\mathbf v_i
$$

and:

$$
\frac{d\mathbf v_i}{dt}
=
\mathbf a_i
$$

or equivalently:

$$
\frac{d^2\mathbf r_i}{dt^2}
=
G
\sum_{j\ne i}
m_j
\frac{\mathbf r_j-\mathbf r_i}
{|\mathbf r_j-\mathbf r_i|^3}
$$

These equations are numerically integrated to evolve the system through time.

---

# 3. Keplerian Orbital Period

For a planet orbiting a dominant stellar mass, the characteristic orbital period is:

$$
P
=
2\pi
\sqrt{
\frac{a^3}
{G(M_\star+m)}
}
$$

For \(m\ll M_\star\):

$$
P
\approx
2\pi
\sqrt{
\frac{a^3}{GM_\star}
}
$$

where:

* \(P\) = orbital period
* \(a\) = semi-major axis
* \(M_\star\) = stellar mass
* \(m\) = planetary mass

This provides the characteristic orbital timescale of the system.

---

# 4. Eccentric Orbital Geometry

For an orbit with eccentricity \(e\), the instantaneous distance from the focus is:

$$
r
=
\frac{a(1-e^2)}
{1+e\cos\nu}
$$

where:

* \(a\) = semi-major axis
* \(e\) = eccentricity
* \(\nu\) = true anomaly

The position in the orbital plane can then be represented as:

$$
\mathbf r_{\mathrm{peri}}
=
\begin{bmatrix}
r\cos\nu\\
r\sin\nu\\
0
\end{bmatrix}
$$

---

# 5. Orbital-Element Coordinate Transformation

The orbital-plane position is transformed into the inertial reference frame using the standard orbital rotations:

$$
\mathbf r
=
R_z(\Omega)
R_x(i)
R_z(\omega)
\mathbf r_{\mathrm{peri}}
$$

where:

* \(i\) = inclination
* \(\Omega\) = longitude of ascending node
* \(\omega\) = argument of periapsis

The rotation about the \(z\)-axis is:

$$
R_z(\theta)
=
\begin{bmatrix}
\cos\theta&-\sin\theta&0\\
\sin\theta&\cos\theta&0\\
0&0&1
\end{bmatrix}
$$

The rotation about the \(x\)-axis is:

$$
R_x(\theta)
=
\begin{bmatrix}
1&0&0\\
0&\cos\theta&-\sin\theta\\
0&\sin\theta&\cos\theta
\end{bmatrix}
$$

### Inclination convention

The implementation follows the conventional astronomical definition:

$$
i=0^\circ
\quad\Rightarrow\quad
\text{face-on}
$$

$$
i=90^\circ
\quad\Rightarrow\quad
\text{edge-on}
$$

An approximately edge-on orbit is required for a planetary transit to be observable from the chosen viewing geometry.

---

# 6. Observer-Plane Projection

The observer looks along the selected line of sight.

For the implemented observer geometry, the position is projected onto the plane of the sky.

The projected coordinates are:

$$
x_{\mathrm{sky}}=x
$$

$$
y_{\mathrm{sky}}=y
$$

The projected planet-star separation is:

$$
d_{\mathrm{sky}}
=
\sqrt{
x_{\mathrm{sky}}^2+y_{\mathrm{sky}}^2
}
$$

or:

$$
d_{\mathrm{sky}}
=
\sqrt{x^2+y^2}
$$

---

# 7. Transit Detection

A transit occurs when the projected planetary position passes across the stellar disk.

The geometric transit condition is:

$$
d_{\mathrm{sky}}
\le
R_\star+R_p
$$

where:

* \(R_\star\) = stellar radius
* \(R_p\) = planetary radius

The simulation uses the projected separation to identify transit events.

---

# 8. Transit Times

The simulation records the times at which transit events occur:

$$
T_1,T_2,T_3,\ldots,T_N
$$

For an approximately periodic planet, a reference linear ephemeris can be represented by:

$$
T_{\mathrm{calc}}(n)
=
T_0+nP
$$

where:

* \(T_0\) = reference transit time
* \(P\) = reference orbital period
* \(n\) = transit number

---

# 9. Transit Timing Variations

The difference between the observed and calculated transit time is:

$$
\Delta T_n
=
T_{\mathrm{obs},n}
-
T_{\mathrm{calc},n}
$$

These deviations are the **Transit Timing Variations (TTVs)**.

For an ideal isolated periodic orbit, the timing sequence would remain close to the reference ephemeris.

When another planet gravitationally perturbs the orbit, the timing can deviate from this simple model.

The resulting sequence:

$$
\Delta T_1,\Delta T_2,\ldots,\Delta T_N
$$

contains information about the perturbing dynamics.

---

# 10. O-C Timing Residual

The same timing difference can be described as an **Observed minus Calculated (O-C)** residual:

$$
O-C
=
T_{\mathrm{obs}}
-
T_{\mathrm{calc}}
$$

The O-C representation is useful for identifying structured departures from a simple periodic timing model.

In the context of this simulation, the timing deviations provide the observational fingerprint used during the inference stage.

---

# 11. RMS Timing Residual

A sequence of timing deviations can be summarized by its root-mean-square value:

$$
\mathrm{RMS}
=
\sqrt{
\frac{1}{N}
\sum_{n=1}^{N}
(\Delta T_n)^2
}
$$

This gives a measure of the overall scale of the timing deviations.

---

# 12. Transit Photometry

A planetary transit causes a reduction in observed stellar flux.

The normalized flux is:

$$
F_{\mathrm{norm}}
=
\frac{F(t)}{F_0}
$$

where:

* \(F(t)\) = stellar flux at time \(t\)
* \(F_0\) = reference out-of-transit flux

During a transit:

$$
F_{\mathrm{norm}}<1
$$

---

# 13. Approximate Transit Depth

For a simplified uniform stellar disk, the approximate fractional transit depth is:

$$
\delta
\approx
\left(
\frac{R_p}{R_\star}
\right)^2
$$

where:

* \(\delta\) = fractional transit depth
* \(R_p\) = planetary radius
* \(R_\star\) = stellar radius

This illustrates why a larger planet produces a deeper photometric signal.

This relationship is included as the physical interpretation of transit photometry; the simulation's primary hidden-companion signal is the **timing behaviour**, not precision stellar photometry.

---

# 14. The Hidden Companion Mechanism

The central physical chain of the simulation is:

$$
\boxed{
\text{Planet B}
\rightarrow
\text{Gravitational Perturbation}
\rightarrow
\text{Planet A Orbital Perturbation}
\rightarrow
\text{Transit-Time Shift}
\rightarrow
\text{TTV Signal}
}
$$

Planet B does not need to produce an obvious transit itself in order to influence the timing of Planet A.

This is the fundamental physical idea behind the **Hidden Architect**.

---

# Inference Concept

The simulation demonstrates the following reasoning process:

```text
Measured transit times
        ↓
Reference timing model
        ↓
Timing deviations
        ↓
Structured TTV signal
        ↓
Hypothesis: additional gravitational body
        ↓
Estimate / prediction
        ↓
Reveal
        ↓
Compare prediction with simulated truth
```

The hidden companion is therefore treated as an **inference problem** rather than a directly displayed object.

---

# Planetary System

The demonstration system contains:

### Planet A — Observed Planet

Planet A is the transiting planet.

Its repeated transits provide the observable timing sequence used by the investigator.

### Planet B — Hidden Companion

Planet B is initially withheld from the observational presentation.

Its gravitational interaction with Planet A modifies Planet A's orbital motion and therefore contributes to the observed timing structure.

After inference, Planet B is revealed as the underlying source of the perturbation.

---

# Reveal & Validation

The final reveal serves as a validation checkpoint.

The hidden companion is exposed only after the investigator has worked through the observational/inference stage.

This creates a distinction between:

**inference**

and

**ground truth**.

The reveal allows the user to visually connect the inferred gravitational structure with the underlying simulated planetary system.

---

# Scientific Accuracy Principles

The project follows several principles intended to keep the simulation scientifically grounded.

### Correct orbital inclination

The simulation uses:

* \(0^\circ\) = face-on
* \(90^\circ\) = edge-on

rather than reversing the conventional astronomical definition.

### Physical transit geometry

Transit detection is based on projected planet-star separation rather than simply placing a planet visually near the star.

### Numerical dynamics

The underlying planetary motion is generated from gravitational dynamics rather than being solely a pre-scripted visual animation.

### Observation is separated from truth

The hidden companion is not exposed to the observer at the beginning.

The observable signal is generated first, and the underlying system is revealed later.

### Visualization is a presentation layer

The cinematic frontend is used to communicate the physical experiment. The visualization should not be interpreted as a replacement for the underlying dynamical calculations.

---

# Simulation Architecture

The conceptual architecture is:

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
             ┌─────────┴─────────┐
             ▼                   ▼
      Transit Detection     Visualization
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

# Mission Flow

The interactive mission is structured around four stages:

## OBSERVE

The user examines the available stellar/transit observations.

The hidden companion is not directly disclosed.

## INFER

The user analyses the timing behaviour and investigates the possibility of a perturbing body.

## PREDICT

The inferred properties are used to form a prediction about the hidden system.

## REVEAL

The hidden companion and underlying system are exposed, allowing the prediction to be compared with the simulated truth.

---

# TESS Connection

The project is inspired by the observational strategy of the **Transiting Exoplanet Survey Satellite (TESS)**.

TESS detects exoplanets primarily through the transit method: when a planet passes between its host star and the observer, it can cause a small reduction in observed stellar brightness.

TESS Hidden Architect extends this idea conceptually.

Instead of asking only:

> **Can we observe a planet transit?**

the simulation asks:

> **What can the timing behaviour of an observed planet tell us about another planet that is not directly visible?**

This creates an educational model of **indirect exoplanet detection**.

---

# What This Simulation Is

* A scientifically motivated exoplanet simulation
* A numerical planetary-dynamics experiment
* A TESS-inspired observational model
* An interactive investigation of transit timing
* An illustration of indirect detection
* An example of inference followed by validation
* An educational visualization of gravitational perturbations

---

# What This Simulation Is Not

The project is not intended to be:

* a replacement for professional TESS data-analysis pipelines
* a complete Bayesian exoplanet parameter-estimation framework
* a complete treatment of stellar activity and instrumental systematics
* a precision fit to a particular confirmed exoplanetary system
* a claim that the simulated planetary system represents a real observed star system

The purpose is to demonstrate the physical reasoning and computational workflow behind indirect detection in an accessible interactive environment.

---

# Technology

The project combines:

* **Python**
* Numerical gravitational dynamics
* Orbital-coordinate transformations
* Synthetic transit detection
* Transit timing analysis
* Local mission server
* **HTML / CSS / JavaScript**
* Canvas-based visualization
* Interactive scientific presentation

The backend provides the physical and observational simulation while the frontend presents the experiment as an interactive mission.

---

# Educational Objective

The project demonstrates a fundamental principle of scientific investigation:

> **Observation is not the same as explanation.**

A measurement may reveal an effect without directly revealing its cause.

The scientific workflow is therefore:

$$
\boxed{
\text{Measure}
\rightarrow
\text{Identify Pattern}
\rightarrow
\text{Build Model}
\rightarrow
\text{Make Prediction}
\rightarrow
\text{Test}
}
$$

TESS Hidden Architect turns this process into an interactive experience.

---

# Limitations & Scope

The simulation is intentionally designed as a scientifically motivated educational model rather than a professional exoplanet-analysis package.

Important simplifications may include:

* simplified stellar and planetary properties
* synthetic rather than archival observational data
* simplified observational noise
* simplified inference compared with professional statistical fitting
* limited planetary-system complexity
* idealized observer geometry
* simplified photometric modelling

These limitations are deliberate: the project prioritizes demonstrating the connection between **gravitational dynamics, observable timing signatures, and scientific inference**.

---

# Core Scientific Idea

The entire project can be summarized as:

$$
\boxed{
\text{Invisible Companion}
\rightarrow
\text{Gravitational Influence}
\rightarrow
\text{Observable Timing Signal}
\rightarrow
\text{Inference}
\rightarrow
\text{Validation}
}
$$

The hidden planet does not have to announce itself directly.

It can reveal itself through the motion of another world.

---

# Final Summary

**TESS Hidden Architect** is a TESS-inspired computational experiment about indirect exoplanet detection.

A visible transiting planet acts as the observational probe.

A hidden companion gravitationally perturbs the system.

Those perturbations can influence the measured transit timings.

The investigator uses those timing signatures to infer the presence of the hidden companion.

The final reveal then exposes the underlying simulated system and provides a validation step.

The central mission is therefore:

```text
OBSERVE
   ↓
INFER
   ↓
PREDICT
   ↓
REVEAL
```

**The planet is hidden.
Its gravity is not.**

