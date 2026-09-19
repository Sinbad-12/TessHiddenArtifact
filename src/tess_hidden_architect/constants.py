"""Physical constants and astronomical unit conversions.

All internal calculations use SI units (meters, kilograms, seconds).
There is one canonical gravitational constant: G_SI.

Conversion helpers translate between common astronomical units and SI.
"""

import math

# ---------------------------------------------------------------------------
# Fundamental physical constants (SI)
# ---------------------------------------------------------------------------

G_SI: float = 6.67430e-11
"""Newtonian gravitational constant in m^3 kg^-1 s^-2.

Source: CODATA 2018 recommended value (6.67430 +/- 0.00015) * 10^-11.
"""

STEFAN_BOLTZMANN: float = 5.670374419e-8
"""Stefan-Boltzmann constant in W m^-2 K^-4."""

SPEED_OF_LIGHT: float = 2.99792458e8
"""Speed of light in vacuum in m/s (exact)."""

# ---------------------------------------------------------------------------
# Astronomical reference values (SI)
# ---------------------------------------------------------------------------

AU_IN_METERS: float = 1.495978707e11
"""One astronomical unit in meters (IAU 2012 exact definition)."""

SOLAR_MASS_KG: float = 1.98892e30
"""Solar mass in kilograms."""

SOLAR_RADIUS_M: float = 6.9634e8
"""Solar radius in meters (nominal IAU value)."""

SOLAR_LUMINOSITY_W: float = 3.828e26
"""Solar luminosity in watts (IAU 2015 nominal value)."""

SOLAR_EFFECTIVE_TEMPERATURE_K: float = 5778.0
"""Solar effective temperature in kelvin."""

EARTH_MASS_KG: float = 5.9722e24
"""Earth mass in kilograms."""

EARTH_RADIUS_M: float = 6.3710e6
"""Earth mean radius in meters."""

JUPITER_MASS_KG: float = 1.8982e27
"""Jupiter mass in kilograms."""

JUPITER_RADIUS_M: float = 6.9911e7
"""Jupiter mean radius in meters."""

YEAR_IN_SECONDS: float = 365.25 * 86400.0
"""Julian year in seconds (365.25 days * 86400 s/day)."""

DAY_IN_SECONDS: float = 86400.0
"""One day in seconds."""


# ---------------------------------------------------------------------------
# Unit conversion functions
# ---------------------------------------------------------------------------

def au_to_m(au: float) -> float:
    """Convert astronomical units to meters."""
    return au * AU_IN_METERS


def m_to_au(m: float) -> float:
    """Convert meters to astronomical units."""
    return m / AU_IN_METERS


def solar_mass_to_kg(solar_masses: float) -> float:
    """Convert solar masses to kilograms."""
    return solar_masses * SOLAR_MASS_KG


def kg_to_solar_mass(kg: float) -> float:
    """Convert kilograms to solar masses."""
    return kg / SOLAR_MASS_KG


def solar_radius_to_m(solar_radii: float) -> float:
    """Convert solar radii to meters."""
    return solar_radii * SOLAR_RADIUS_M


def m_to_solar_radius(m: float) -> float:
    """Convert meters to solar radii."""
    return m / SOLAR_RADIUS_M


def solar_luminosity_to_w(solar_luminosities: float) -> float:
    """Convert solar luminosities to watts."""
    return solar_luminosities * SOLAR_LUMINOSITY_W


def w_to_solar_luminosity(w: float) -> float:
    """Convert watts to solar luminosities."""
    return w / SOLAR_LUMINOSITY_W


def year_to_seconds(years: float) -> float:
    """Convert Julian years to seconds."""
    return years * YEAR_IN_SECONDS


def seconds_to_year(seconds: float) -> float:
    """Convert seconds to Julian years."""
    return seconds / YEAR_IN_SECONDS
