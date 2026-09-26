"""
Test ALL data sources - show actual responses with error handling
"""
import sys
import json
sys.path.insert(0, ".")
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("ClimateX.ai - Data Source Response Test")
print("=" * 70)

def safe_test(name, test_func):
    """Run test with error handling"""
    print(f"\n{name}")
    print("-" * 50)
    try:
        test_func()
        return True
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
        return False

# Test 1: WAQI
def test_waqi():
    from src.data_sources.openaq import WAQIClient
    waqi = WAQIClient()
    data = waqi.get_city_feed("Beijing")
    aqi = data.get('data', {}).get('aqi', 'N/A')
    city = data.get('data', {}).get('city', {}).get('name', 'Unknown')
    print(f"  {city} AQI: {aqi}")

# Test 2: USGS
def test_usgs():
    from src.data_sources.usgs_earthquake import USGSEarthquakeClient
    usgs = USGSEarthquakeClient()
    data = usgs.get_real_time_feed("day", "4.5")
    for eq in data.get("features", [])[:3]:
        props = eq.get("properties", {})
        print(f"  M{props.get('mag')} - {props.get('place')}")

# Test 3: Open-Meteo
def test_openmeteo():
    from src.data_sources.open_meteo import OpenMeteoClient
    meteo = OpenMeteoClient()
    data = meteo.get_weather(28.6139, 77.2090)
    temps = data.get("hourly", {}).get("temperature_2m", [])[:3]
    print(f"  Delhi temps (3h): {temps}°C")

# Test 4: NOAA Ocean  
def test_noaa():
    from src.data_sources.noaa_ocean import NOAAOceanClient
    noaa = NOAAOceanClient()
    data = noaa.get_water_level("8518750", hours=3)
    obs = data.get("data", [])
    if obs:
        latest = obs[-1]
        print(f"  NYC Battery water level: {latest.get('v')}m at {latest.get('t')}")
    else:
        print(f"  Response: {str(data)[:100]}")

# Test 5: Marine
def test_marine():
    from src.data_sources.noaa_ocean import OpenMeteoMarineClient
    marine = OpenMeteoMarineClient()
    data = marine.get_ocean_conditions(24.5, -81.5)
    hourly = data.get("hourly", {})
    sst = hourly.get("sea_surface_temperature", [0])[0]
    waves = hourly.get("wave_height", [0])[0]
    print(f"  Florida Keys - SST: {sst}°C, Waves: {waves}m")

# Test 6: GBIF
def test_gbif():
    from src.data_sources.gbif import GBIFClient
    gbif = GBIFClient()
    data = gbif.search_species("Tiger", limit=3)
    for sp in data.get("results", [])[:3]:
        print(f"  {sp.get('scientificName', 'Unknown')}")

# Test 7: Climate TRACE
def test_climatetrace():
    from src.data_sources.climate_trace import ClimateTraceClient
    ct = ClimateTraceClient()
    # Try sectors first (more reliable)
    sectors = ct.get_sectors()
    if sectors:
        print(f"  Sectors available: {len(sectors)} sectors")
        for s in sectors[:3]:
            if isinstance(s, dict):
                print(f"    - {s.get('name', s)}")
            else:
                print(f"    - {s}")
    else:
        print("  Using static sector list")
        for s in ct.get_available_sectors()[:3]:
            print(f"    - {s}")

# Test 8: Copernicus Marine
def test_copernicus_marine():
    from src.data_sources.copernicus import CopernicusMarineClient
    cmarine = CopernicusMarineClient()
    for ds in cmarine.get_available_datasets()[:2]:
        print(f"  {ds['name'][:45]}")

# Test 9: Copernicus Sentinel
def test_copernicus_sentinel():
    from src.data_sources.copernicus import CopernicusSentinelClient
    sentinel = CopernicusSentinelClient()
    for c in sentinel.get_available_collections()[:3]:
        print(f"  {c['name']} ({c['type']}) - {c['resolution']}")

# Test 10: Coral Reef Watch
def test_coral():
    from src.data_sources.noaa_ocean import CoralReefWatchClient
    coral = CoralReefWatchClient()
    data = coral.get_region_status("great_barrier_reef")
    print(f"  {data.get('region')} at {data.get('coordinates')}")

# Test 11: News Ingestion
def test_news():
    from src.data_sources.news_sources import NewsIngestionService
    service = NewsIngestionService()
    # Fetch small batch to verify connectivity
    articles = service.fetch_all_news(limit_per_source=10, days_back=3)
    print(f"  Fetched {len(articles)} articles from {len(set(a.source for a in articles))} sources")
    if articles:
        print(f"  Sample: {articles[0].title[:50]}...")

# Run all tests
tests = [
    ("1️⃣ WAQI (Air Quality)", test_waqi),
    ("2️⃣ USGS Earthquake", test_usgs),
    ("3️⃣ Open-Meteo Weather", test_openmeteo),
    ("4️⃣ NOAA Ocean (Sea Level)", test_noaa),
    ("5️⃣ Open-Meteo Marine", test_marine),
    ("6️⃣ GBIF (Biodiversity)", test_gbif),
    ("7️⃣ Climate TRACE (Emissions)", test_climatetrace),
    ("8️⃣ Copernicus Marine", test_copernicus_marine),
    ("9️⃣ Copernicus Sentinel", test_copernicus_sentinel),
    ("🔟 Coral Reef Watch", test_coral),
    ("1️⃣1️⃣ News Ingestion", test_news),
]

passed = sum(safe_test(name, func) for name, func in tests)

print("\n" + "=" * 70)
print(f"Results: {passed}/{len(tests)} data sources returned data")
print("=" * 70)
