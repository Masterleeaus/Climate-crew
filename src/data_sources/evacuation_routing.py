from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
import logging
import os
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvacuationRouter:
    """
    Provides evacuation route planning and shelter/safe zone finding.
    """
    
    def __init__(self, openroute_api_key: Optional[str] = None):
        self.api_key = openroute_api_key or os.getenv("OPENROUTE_API_KEY")
        self.base_url = "https://api.openrouteservice.org"
        
        # Emergency contacts by country (sample data)
        self.emergency_contacts = {
            "US": {"police": "911", "fire": "911", "ambulance": "911", "fema": "1-800-621-3362"},
            "IN": {"police": "100", "fire": "101", "ambulance": "102", "disaster": "108"},
            "UK": {"police": "999", "fire": "999", "ambulance": "999"},
            "AU": {"police": "000", "fire": "000", "ambulance": "000", "ses": "132-500"},
            "DEFAULT": {"emergency": "112"}
        }
    
    def get_evacuation_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        avoid_zones: Optional[List[Dict]] = None,
        profile: str = "driving-car"
    ) -> Dict:
        """
        Calculate evacuation route from start to destination.
        
        Args:
            start_lat, start_lon: Starting coordinates
            end_lat, end_lon: Destination coordinates
            avoid_zones: List of danger zones to avoid (each with lat, lon, radius_km)
            profile: Transportation mode (driving-car, foot-walking, cycling-regular)
        
        Returns:
            Route information with directions, distance, and estimated time
        """
        if self.api_key:
            return self._get_route_from_api(
                start_lat, start_lon, end_lat, end_lon, avoid_zones, profile
            )
        else:
            # Fallback to simple calculation without API
            return self._calculate_simple_route(
                start_lat, start_lon, end_lat, end_lon
            )
    
    def _get_route_from_api(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        avoid_zones: Optional[List[Dict]],
        profile: str
    ) -> Dict:
        """Get route from OpenRouteService API."""
        try:
            url = f"{self.base_url}/v2/directions/{profile}"
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            
            body = {
                "coordinates": [
                    [start_lon, start_lat],
                    [end_lon, end_lat]
                ],
                "instructions": True,
                "units": "km"
            }
            
            # Add avoid areas if specified
            if avoid_zones:
                avoid_polygons = []
                for zone in avoid_zones:
                    # Create circular polygon around danger zone
                    polygon = self._create_avoid_polygon(
                        zone["lat"], zone["lon"], zone.get("radius_km", 5)
                    )
                    avoid_polygons.append(polygon)
                
                if avoid_polygons:
                    body["options"] = {
                        "avoid_polygons": {
                            "type": "MultiPolygon",
                            "coordinates": avoid_polygons
                        }
                    }
            
            response = requests.post(url, json=body, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            route = data.get("routes", [{}])[0]
            segments = route.get("segments", [{}])[0]
            
            return {
                "status": "success",
                "distance_km": round(segments.get("distance", 0) / 1000, 2),
                "duration_minutes": round(segments.get("duration", 0) / 60, 1),
                "steps": self._parse_directions(segments.get("steps", [])),
                "warning": "Route may pass through affected areas" if avoid_zones else None,
                "source": "OpenRouteService",
                "profile": profile,
                "start": {"lat": start_lat, "lon": start_lon},
                "end": {"lat": end_lat, "lon": end_lon}
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouteService API error: {e}")
            return self._calculate_simple_route(start_lat, start_lon, end_lat, end_lon)
    
    def _calculate_simple_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict:
        """Simple distance calculation without routing API."""
        distance = self._haversine_distance(start_lat, start_lon, end_lat, end_lon)
        
        # Estimate travel time (assuming 50 km/h average for evacuation)
        duration_minutes = (distance / 50) * 60
        
        # Calculate bearing for general direction
        bearing = self._calculate_bearing(start_lat, start_lon, end_lat, end_lon)
        direction = self._bearing_to_direction(bearing)
        
        return {
            "status": "estimated",
            "distance_km": round(distance, 2),
            "duration_minutes": round(duration_minutes, 1),
            "steps": [
                {
                    "instruction": f"Head {direction} toward destination",
                    "distance_km": round(distance, 2),
                    "duration_minutes": round(duration_minutes, 1)
                }
            ],
            "warning": "This is an estimated route. Use GPS navigation for accurate directions.",
            "source": "estimated",
            "start": {"lat": start_lat, "lon": start_lon},
            "end": {"lat": end_lat, "lon": end_lon}
        }
    
    def find_nearby_shelters(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 15.0,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find nearby emergency shelters and safe zones.

        Strategy:
          1. Overpass API (OSM) — searches nodes, ways, AND relations
             for hospitals, shelters, schools, fire stations, police, etc.
          2. If Overpass fails → Nominatim search API as backup.
          3. Never returns fake/placeholder data.
        """
        # Try Overpass first
        shelters = self._shelters_from_overpass(latitude, longitude, radius_km, limit)
        if shelters:
            return shelters

        # Fallback: Nominatim search
        shelters = self._shelters_from_nominatim(latitude, longitude, radius_km, limit)
        if shelters:
            return shelters

        # No data available — return empty (honest)
        logger.warning(f"No shelter data for ({latitude}, {longitude})")
        return []

    def _shelters_from_overpass(
        self, latitude: float, longitude: float,
        radius_km: float, limit: int
    ) -> List[Dict]:
        """
        Query Overpass API for emergency-relevant amenities.

        Searches node + way + relation so we don't miss buildings
        mapped as polygons (hospitals, schools, etc.).
        Uses `out center` so ways/relations return a centroid coordinate.
        """
        overpass_url = "https://overpass-api.de/api/interpreter"
        radius_m = int(radius_km * 1000)

        # nwr = node + way + relation in Overpass QL
        query = f"""
[out:json][timeout:25];
(
  nwr["amenity"="hospital"](around:{radius_m},{latitude},{longitude});
  nwr["amenity"="shelter"](around:{radius_m},{latitude},{longitude});
  nwr["amenity"="community_centre"](around:{radius_m},{latitude},{longitude});
  nwr["amenity"="fire_station"](around:{radius_m},{latitude},{longitude});
  nwr["amenity"="police"](around:{radius_m},{latitude},{longitude});
  nwr["amenity"="school"](around:{radius_m},{latitude},{longitude});
  nwr["emergency"="assembly_point"](around:{radius_m},{latitude},{longitude});
  nwr["social_facility"="shelter"](around:{radius_m},{latitude},{longitude});
);
out center body;
"""
        try:
            resp = requests.post(
                overpass_url, data={"data": query}, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"Overpass API error: {e}")
            return []

        shelters = []
        seen = set()
        for el in data.get("elements", []):
            # Get coordinates — nodes have lat/lon directly,
            # ways/relations have center.lat / center.lon from `out center`
            if el.get("type") == "node":
                el_lat = el.get("lat")
                el_lon = el.get("lon")
            else:
                center = el.get("center", {})
                el_lat = center.get("lat")
                el_lon = center.get("lon")

            if el_lat is None or el_lon is None:
                continue

            tags = el.get("tags", {})
            name = (
                tags.get("name")
                or tags.get("name:en")
                or tags.get("name:ja")       # Japanese names
                or tags.get("official_name")
                or tags.get("short_name")
            )
            amenity = tags.get("amenity", tags.get("emergency", tags.get("social_facility", "shelter")))

            # Generate a fallback name from amenity type if no name tag
            if not name:
                name = amenity.replace("_", " ").title()

            # Deduplicate by name + type
            key = f"{name}:{amenity}"
            if key in seen:
                continue
            seen.add(key)

            distance = self._haversine_distance(latitude, longitude, el_lat, el_lon)

            # Build address from available tags
            addr_parts = [
                tags.get("addr:housenumber", ""),
                tags.get("addr:street", ""),
                tags.get("addr:city", ""),
            ]
            address = ", ".join(p for p in addr_parts if p) or None

            shelters.append({
                "name": name,
                "type": amenity,
                "distance_km": round(distance, 2),
                "coordinates": {"lat": round(el_lat, 6), "lon": round(el_lon, 6)},
                "address": address,
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "opening_hours": tags.get("opening_hours"),
                "wheelchair": tags.get("wheelchair", "unknown"),
                "source": "OpenStreetMap",
            })

        shelters.sort(key=lambda x: x["distance_km"])

        # Prioritise hospitals & shelters over schools/police
        priority = {"hospital": 0, "shelter": 1, "community_centre": 2,
                     "fire_station": 3, "assembly_point": 3, "police": 4, "school": 5}
        # Group by type, take top from each, then fill remaining
        by_type: Dict[str, List] = {}
        for s in shelters:
            by_type.setdefault(s["type"], []).append(s)

        result = []
        # First pass: take closest of each priority type
        for typ in sorted(priority, key=priority.get):
            if typ in by_type and by_type[typ]:
                result.append(by_type[typ][0])
                if len(result) >= limit:
                    return result[:limit]

        # Fill remaining with closest overall
        for s in shelters:
            if s not in result:
                result.append(s)
                if len(result) >= limit:
                    break

        return result[:limit]

    def _shelters_from_nominatim(
        self, latitude: float, longitude: float,
        radius_km: float, limit: int
    ) -> List[Dict]:
        """
        Backup: use Nominatim structured search for nearby hospitals
        and emergency facilities.
        """
        try:
            results = []
            for query_term in ["hospital", "fire station", "shelter", "school"]:
                resp = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": query_term,
                        "format": "json",
                        "limit": 3,
                        "viewbox": self._bounding_box(latitude, longitude, radius_km),
                        "bounded": 1,
                    },
                    headers={"User-Agent": "ClimateX-Disaster/1.0"},
                    timeout=10,
                )
                if resp.status_code != 200:
                    continue

                for place in resp.json():
                    p_lat = float(place.get("lat", 0))
                    p_lon = float(place.get("lon", 0))
                    dist = self._haversine_distance(latitude, longitude, p_lat, p_lon)
                    results.append({
                        "name": place.get("display_name", "").split(",")[0],
                        "type": query_term.replace(" ", "_"),
                        "distance_km": round(dist, 2),
                        "coordinates": {"lat": round(p_lat, 6), "lon": round(p_lon, 6)},
                        "address": place.get("display_name"),
                        "phone": None,
                        "opening_hours": None,
                        "wheelchair": "unknown",
                        "source": "Nominatim",
                    })

            results.sort(key=lambda x: x["distance_km"])
            return results[:limit]

        except Exception as e:
            logger.warning(f"Nominatim shelter search failed: {e}")
            return []

    @staticmethod
    def _bounding_box(lat: float, lon: float, radius_km: float) -> str:
        """Return 'west,south,east,north' bounding box string for Nominatim."""
        dlat = radius_km / 111.0
        dlon = radius_km / (111.0 * max(0.01, math.cos(math.radians(lat))))
        return f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}"
    
    def get_emergency_contacts(self, country_code: str = "DEFAULT") -> Dict:
        """Get emergency contact numbers for a country."""
        country_code = country_code.upper()
        contacts = self.emergency_contacts.get(
            country_code,
            self.emergency_contacts["DEFAULT"]
        )
        
        return {
            "country": country_code,
            "contacts": contacts,
            "note": "Call emergency services immediately in life-threatening situations"
        }
    
    def estimate_population_at_risk(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        disaster_type: str = "general"
    ) -> Dict:
        """
        Estimate population and infrastructure at risk.
        Uses location-based density estimation for major cities.
        """
        area_sq_km = math.pi * (radius_km ** 2)
        
        # Location-based density estimates (people per sq km)
        # Based on approximate urban densities for major cities
        density = self._get_location_density(latitude, longitude)
        
        estimated_population = int(area_sq_km * density)
        
        # Infrastructure estimates based on density
        if density > 10000:  # Very dense urban
            buildings_per_person = 3.5
            roads_per_sqkm = 15
        elif density > 3000:  # Urban
            buildings_per_person = 4
            roads_per_sqkm = 8
        elif density > 500:  # Suburban
            buildings_per_person = 5
            roads_per_sqkm = 4
        else:  # Rural
            buildings_per_person = 8
            roads_per_sqkm = 1.5
        
        estimated_buildings = int(estimated_population / buildings_per_person)
        estimated_roads_km = area_sq_km * roads_per_sqkm
        
        severity_multipliers = {
            "earthquake": {"population": 1.0, "buildings": 1.2, "roads": 0.8},
            "flood": {"population": 0.8, "buildings": 0.6, "roads": 1.0},
            "wildfire": {"population": 1.0, "buildings": 1.0, "roads": 0.5},
            "hurricane": {"population": 1.0, "buildings": 1.0, "roads": 0.9},
            "cyclone": {"population": 1.0, "buildings": 1.0, "roads": 0.9},
            "general": {"population": 1.0, "buildings": 1.0, "roads": 1.0}
        }
        
        multiplier = severity_multipliers.get(disaster_type.lower(), severity_multipliers["general"])
        
        return {
            "radius_km": radius_km,
            "area_sq_km": round(area_sq_km, 2),
            "disaster_type": disaster_type,
            "density_per_sqkm": round(density, 1),
            "estimates": {
                "population_at_risk": int(estimated_population * multiplier["population"]),
                "buildings_affected": int(estimated_buildings * multiplier["buildings"]),
                "roads_affected_km": round(estimated_roads_km * multiplier["roads"], 1)
            },
            "note": "Density from GeoNames API + Clark (1951) exponential gradient model.",
            "data_source": "geonames_api_with_scaling_model"
        }
    
    def _get_location_density(self, lat: float, lon: float) -> float:
        """
        Get population density using the GeoNames API (live data).

        Falls back to a mathematical urban-scaling model when the
        API is unavailable.

        Mathematical model (fallback):
            Given city population P and distance d from city centre,
            density = (P / (π × r²)) × exp(−d / r)
            where r = √(P / (π × 5000))  is the effective city radius
            (calibrated so average urban density ≈ 5000 /km²).
        """
        # ── Try GeoNames API first ──
        density = self._density_from_geonames(lat, lon)
        if density is not None:
            return density

        # ── Fallback: Nominatim reverse-geocode → population ──
        density = self._density_from_nominatim(lat, lon)
        if density is not None:
            return density

        # ── Last resort: generic rural density ──
        return 50.0

    def _density_from_geonames(self, lat: float, lon: float) -> Optional[float]:
        """
        Query GeoNames findNearbyPlaceNameJSON for nearby settlements.
        Returns estimated density using urban scaling law.
        """
        username = os.getenv("GEONAMES_USERNAME", "demo")
        try:
            resp = requests.get(
                "http://api.geonames.org/findNearbyPlaceNameJSON",
                params={
                    "lat": lat, "lng": lon,
                    "maxRows": 3, "radius": 50,
                    "username": username,
                },
                timeout=8,
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            places = data.get("geonames", [])
            if not places:
                return None

            # Use the nearest place with population data
            for place in places:
                pop = int(place.get("population", 0))
                place_lat = float(place.get("lat", lat))
                place_lon = float(place.get("lng", lon))
                dist = self._haversine_distance(lat, lon, place_lat, place_lon)

                if pop > 0:
                    return self._density_from_population(pop, dist)

            return None
        except Exception as e:
            logger.warning(f"GeoNames API failed: {e}")
            return None

    def _density_from_nominatim(self, lat: float, lon: float) -> Optional[float]:
        """
        Reverse-geocode via Nominatim to identify settlement type.
        """
        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat, "lon": lon,
                    "format": "json", "zoom": 10,
                },
                headers={"User-Agent": "ClimateX-Disaster/1.0"},
                timeout=8,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            addr = data.get("address", {})

            # Identify settlement type from address hierarchy
            if addr.get("city"):
                # It's in a city — assume moderate urban density
                return 3000.0
            elif addr.get("town"):
                return 1000.0
            elif addr.get("village"):
                return 200.0
            elif addr.get("hamlet"):
                return 50.0
            else:
                return None
        except Exception as e:
            logger.warning(f"Nominatim reverse-geocode failed: {e}")
            return None

    @staticmethod
    def _density_from_population(population: int, distance_from_centre_km: float) -> float:
        """
        Urban-scaling density model.

        Given a city of population P, the effective radius is:
            r = √(P / (π × ρ₀))      with ρ₀ = 5000 /km² (average urban density)

        The density at distance d from the city centre decays exponentially:
            ρ(d) = ρ_centre × exp(−d / r)
            where ρ_centre = P / (π × r²)

        This is a standard urban geography model (Clark 1951 negative-
        exponential density gradient).
        """
        if population <= 0:
            return 50.0

        RHO_0 = 5000.0  # average urban density assumption
        r = math.sqrt(population / (math.pi * RHO_0))  # effective radius (km)
        r = max(r, 0.5)  # minimum 0.5 km

        rho_centre = population / (math.pi * r * r)
        density = rho_centre * math.exp(-distance_from_centre_km / r)

        return max(10.0, density)  # floor at 10 /km²
    
    def _create_avoid_polygon(self, lat: float, lon: float, radius_km: float) -> List:
        """Create a circular polygon for avoid zones."""
        points = []
        num_points = 16
        
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            # Approximate: 1 degree latitude ≈ 111 km
            d_lat = (radius_km / 111) * math.sin(angle)
            d_lon = (radius_km / (111 * math.cos(math.radians(lat)))) * math.cos(angle)
            points.append([lon + d_lon, lat + d_lat])
        
        points.append(points[0])  # Close the polygon
        return [points]
    
    def _parse_directions(self, steps: List[Dict]) -> List[Dict]:
        """Parse OpenRouteService direction steps."""
        parsed = []
        for step in steps:
            parsed.append({
                "instruction": step.get("instruction", "Continue"),
                "distance_km": round(step.get("distance", 0) / 1000, 2),
                "duration_minutes": round(step.get("duration", 0) / 60, 1),
                "type": step.get("type", 0)
            })
        return parsed
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in km."""
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2."""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def _bearing_to_direction(self, bearing: float) -> str:
        """Convert bearing to compass direction."""
        directions = ["north", "northeast", "east", "southeast", 
                      "south", "southwest", "west", "northwest"]
        index = round(bearing / 45) % 8
        return directions[index]
