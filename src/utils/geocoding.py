"""
Geocoding utility for coordinate-to-country resolution.
Uses coordinates2country for fast, offline reverse geocoding.
"""
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Initialize the geocoder once (singleton pattern)
_geocoder = None

def _get_geocoder():
    global _geocoder
    if _geocoder is None:
        try:
            from coordinates2country.coordinates2country import Coordinates2Country
            _geocoder = Coordinates2Country()
        except ImportError:
            logger.warning("coordinates2country not installed. Run: pip install coordinates2country")
    return _geocoder

try:
    import pycountry
    PYCOUNTRY_AVAILABLE = True
except ImportError:
    PYCOUNTRY_AVAILABLE = False


# Mapping for common countries (Alpha-2 -> Alpha-3)
ISO_2_TO_3 = {
    'BR': 'BRA', 'ID': 'IDN', 'IN': 'IND', 'US': 'USA', 'CN': 'CHN', 
    'RU': 'RUS', 'JP': 'JPN', 'DE': 'DEU', 'GB': 'GBR', 'CD': 'COD',
    'MY': 'MYS', 'AU': 'AUS', 'CA': 'CAN', 'FR': 'FRA',
    'HT': 'HTI', 'CU': 'CUB', 'DO': 'DOM', 'MX': 'MEX', 'AR': 'ARG',
    'CO': 'COL', 'PE': 'PER', 'VE': 'VEN', 'BO': 'BOL', 'PY': 'PRY',
    'NG': 'NGA', 'TZ': 'TZA', 'KE': 'KEN', 'ZA': 'ZAF', 'EG': 'EGY',
    'TH': 'THA', 'VN': 'VNM', 'PH': 'PHL', 'PK': 'PAK', 'BD': 'BGD',
    'IT': 'ITA', 'ES': 'ESP', 'PL': 'POL', 'NL': 'NLD', 'BE': 'BEL',
    'GR': 'GRC', 'CZ': 'CZE', 'PT': 'PRT', 'SE': 'SWE', 'HU': 'HUN',
    'AT': 'AUT', 'BG': 'BGR', 'DK': 'DNK', 'FI': 'FIN', 'SK': 'SVK',
    'IE': 'IRL', 'HR': 'HRV', 'LT': 'LTU', 'SI': 'SVN', 'LV': 'LVA',
    'EE': 'EST', 'CY': 'CYP', 'LU': 'LUX', 'MT': 'MLT', 'CL': 'CHL',
    'EC': 'ECU', 'UY': 'URY', 'CR': 'CRI', 'PA': 'PAN', 'GT': 'GTM',
    'HN': 'HND', 'SV': 'SLV', 'NI': 'NIC', 'JM': 'JAM', 'TT': 'TTO'
}


@lru_cache(maxsize=500)
def get_country_code(latitude: float, longitude: float) -> Optional[str]:
    """
    Get the ISO 3166-1 alpha-2 country code from latitude and longitude.
    Uses coordinates2country for fast, offline lookup.
    Returns None if the coordinates are in the ocean or unmapped.
    """
    geocoder = _get_geocoder()
    if geocoder is None:
        logger.error("coordinates2country not available")
        return None
    
    try:
        # coordinates2country.country_code() returns ISO alpha-2 code or None
        alpha2 = geocoder.country_code(latitude, longitude)
        return alpha2
    except Exception as e:
        logger.warning(f"Geocoding failed for ({latitude}, {longitude}): {e}")
        return None


def alpha2_to_alpha3(alpha2: str) -> Optional[str]:
    """Convert ISO alpha-2 to alpha-3 country code."""
    if not alpha2:
        return None
    
    alpha2 = alpha2.upper()
    
    # Try pycountry first for comprehensive lookup
    if PYCOUNTRY_AVAILABLE:
        try:
            c = pycountry.countries.get(alpha_2=alpha2)
            if c:
                return c.alpha_3
        except Exception:
            pass
    
    # Fallback to static mapping
    return ISO_2_TO_3.get(alpha2)


def get_country_code_alpha3(latitude: float, longitude: float) -> str:
    """
    Get the ISO 3166-1 alpha-3 country code from latitude and longitude.
    Returns 'Unknown' if the country cannot be determined.
    """
    alpha2 = get_country_code(latitude, longitude)
    
    if not alpha2:
        return "Unknown"
    
    alpha3 = alpha2_to_alpha3(alpha2)
    
    if alpha3:
        return alpha3
    
    # If conversion failed, return alpha-2 as a fallback
    return alpha2

try:
    from langchain_core.tools import tool
    
    @tool
    def get_country_from_coords(latitude: float, longitude: float) -> str:
        """Identify the country code (ISO 3-letter) for a given coordinate."""
        return get_country_code_alpha3(latitude, longitude)
except ImportError:
    pass
