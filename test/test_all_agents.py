import sys
sys.path.insert(0, ".")

print("=" * 60)
print("ClimateX.ai - Testing New Environmental Agents")
print("=" * 60)

# Test 1: Ocean Agent
print("\n🌊 OCEAN AGENT TEST")
print("-" * 40)
try:
    from src.agents.ocean_agent import (
        get_sea_level_trend, get_coral_bleaching_status, 
        get_ocean_conditions, get_sea_surface_temperature
    )
    
    print("Testing get_ocean_conditions (Florida Keys)...")
    result = get_ocean_conditions.invoke({"latitude": 24.5, "longitude": -81.5})
    print(result[:300] if len(result) > 300 else result)
    
    print("\nTesting get_coral_bleaching_status...")
    result = get_coral_bleaching_status.invoke({"region": "great_barrier_reef"})
    print(result[:300] if len(result) > 300 else result)
    
    print("\n[OK] OceanAgent tools working!")
except Exception as e:
    print(f"[FAIL] OceanAgent: {e}")

# Test 2: Biodiversity Agent
print("\n\n🦋 BIODIVERSITY AGENT TEST")
print("-" * 40)
try:
    from src.agents.biodiversity_agent import (
        search_species, get_species_occurrences, 
        check_endangered_species, get_area_biodiversity
    )
    
    print("Testing search_species (Tiger)...")
    result = search_species.invoke({"query": "Panthera tigris"})
    print(result[:400] if len(result) > 400 else result)
    
    print("\nTesting check_endangered_species (India)...")
    result = check_endangered_species.invoke({"country_code": "IN"})
    print(result[:400] if len(result) > 400 else result)
    
    print("\n[OK] BiodiversityAgent tools working!")
except Exception as e:
    print(f"[FAIL] BiodiversityAgent: {e}")

# Test 3: Climate Anomaly Agent
print("\n\n🌡️ CLIMATE ANOMALY AGENT TEST")
print("-" * 40)
try:
    from src.agents.climate_anomaly_agent import (
        detect_heat_wave, get_weather_anomalies, 
        get_extreme_events, get_climate_summary
    )
    
    print("Testing detect_heat_wave (Delhi)...")
    result = detect_heat_wave.invoke({"latitude": 28.6139, "longitude": 77.2090})
    print(result[:400] if len(result) > 400 else result)
    
    print("\nTesting get_weather_anomalies (Mumbai)...")
    result = get_weather_anomalies.invoke({"latitude": 19.0760, "longitude": 72.8777})
    print(result[:400] if len(result) > 400 else result)
    
    print("\n[OK] ClimateAnomalyAgent tools working!")
except Exception as e:
    print(f"[FAIL] ClimateAnomalyAgent: {e}")

# Test 4: Carbon Emissions Agent
print("\n\n🏭 CARBON EMISSIONS AGENT TEST")
print("-" * 40)
try:
    from src.agents.carbon_emissions_agent import (
        get_country_emissions, get_sector_emissions,
        compare_countries, list_emission_sectors
    )
    
    print("Testing list_emission_sectors...")
    result = list_emission_sectors.invoke({})
    print(result)
    
    print("\nTesting get_country_emissions (India)...")
    result = get_country_emissions.invoke({"country_code": "IND", "year": 2023})
    print(result)
    
    print("\nTesting compare_countries...")
    result = compare_countries.invoke({"country_codes": "USA,CHN,IND"})
    print(result[:400] if len(result) > 400 else result)
    
    print("\n[OK] CarbonEmissionsAgent tools working!")
except Exception as e:
    print(f"[FAIL] CarbonEmissionsAgent: {e}")

# Test 5: Orchestrator routing
print("\n\n🎯 ORCHESTRATOR ROUTING TEST")
print("-" * 40)
try:
    from src.agents.orchestrator import OrchestratorAgent
    
    orchestrator = OrchestratorAgent()
    print(f"Orchestrator has {len(orchestrator.agents)} agents:")
    for name in orchestrator.agents:
        print(f"  - {name}")
    
    print("\n[OK] Orchestrator ready!")
except Exception as e:
    print(f"[FAIL] Orchestrator: {e}")

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)
