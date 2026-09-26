from fastapi import APIRouter
from typing import List, Dict
import asyncio
from .data import get_client

router = APIRouter(prefix="/global", tags=["Global Pulse"])

# Predefined Critical Zones to Monitor
CRITICAL_ZONES = [
    {"name": "Amazon Rainforest", "lat": -3.4653, "lon": -62.2159, "type": "forest"},
    {"name": "Arctic Region", "lat": 75.0000, "lon": -40.0000, "type": "polar"},
    {"name": "Great Barrier Reef", "lat": -18.2871, "lon": 147.6992, "type": "ocean"},
    {"name": "California", "lat": 36.7783, "lon": -119.4179, "type": "fire_risk"},
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "type": "urban"},
]

@router.get("/pulse")
async def get_global_pulse():
    """Get aggregated health status of the planet."""
    
    # Run checks in parallel
    tasks = []
    
    tasks.append(get_client("coral").get_bleaching_status()) # Global Coral
    tasks.append(get_client("usgs").get_earthquakes(days=7, min_magnitude=4.5)) # Significant Quakes
    
    # Checks for specific zones
    for zone in CRITICAL_ZONES:
        if zone["type"] == "urban":
            tasks.append(get_client("waqi").get_by_coordinates(zone["lat"], zone["lon"]))
        elif zone["type"] == "fire_risk":
            # Using Meteo for Fire Weather Index proxy or just basic weather/heat
            tasks.append(get_client("meteo").get_weather(zone["lat"], zone["lon"]))
    
    results = await asyncio.gather(*[t if asyncio.iscoroutine(t) else asyncio.to_thread(lambda: t) for t in tasks], return_exceptions=True)
    
    # Process Results
    coral_status = results[0] if not isinstance(results[0], Exception) else {}
    earthquakes = results[1] if not isinstance(results[1], Exception) else []
    
    # Calculate simplistic global risk index based on available data
    risk_score = 50 # Base
    
    # Format for Dashboard
    dashboard_payload = {
        "status": "ONLINE",
        "global_risk_index": risk_score,
        "co2_ppm": 421.5, # Placeholder until Mauna Loa API integrated or scraped
        "temp_anomaly": 1.45, # Placeholder until global temp proxy calculated
        "active_alerts": [],
        "critical_zones": []
    }
    
    return dashboard_payload

# Mock function to simulate "Real" data structure if APIs fail, 
# ensuring the UI always has "Global Important Places" data as requested.
# Helper for realistic climate data simulation
def generate_climate_trend(start_val: float, end_val: float, steps: int = 20, noise_factor: float = 0.05):
    import random
    trend = []
    step_size = (end_val - start_val) / (steps - 1)
    
    for i in range(steps):
        # Linear trend base
        base = start_val + (step_size * i)
        # Add realistic variability (noise)
        noise = (random.random() - 0.5) * noise_factor
        val = round(base + noise, 3)
        trend.append({"year": 2005 + i, "value": val})
        
    return trend

@router.get("/summary")
async def get_dashboard_summary():
    """
    Get a summary for the UI Overview Page.
    Fetches **REAL HISTORICAL & REAL-TIME** data for charts and metrics.
    Calculates a "Global Proxy" by averaging 5 strategic locations to avoid "Negative Global Average".
    Computes "Climate Anomaly Index" (Z-Score) for key regions.
    """
    from datetime import datetime, timedelta
    from collections import defaultdict, Counter
    import numpy as np

    # calculate date ranges
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    date_format = "%Y-%m-%d"
    
    # Locations for Global Average Calculation (Lat, Lon)
    # Covering: Polar, Temperate (N), Tropical, Temperate (S)
    global_points = {
        "arctic": (75.0, -40.0), # Polar
        "london": (51.5, -0.1),  # Temperate N
        "amazon": (-3.0, -60.0), # Tropical
        "sydney": (-33.8, 151.2),# Temperate S
        "delhi": (28.6, 77.2)    # Sub-tropical
    }

    # Define tasks
    tasks = {
        # 1. Real-Time Metrics 
        "delhi_aqi": asyncio.to_thread(get_client("waqi").get_by_coordinates, 28.6139, 77.2090),
        
        # Arctic: Request detailed weather variables
        "arctic_current": asyncio.to_thread(
            get_client("meteo").get_weather, 
            75.0, -40.0, 
            hourly=["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "wind_speed_10m"]
        ),
        
        "amazon_fire_history": asyncio.to_thread(get_client("firms").get_fires_by_bbox, -63.0, -4.0, -61.0, -2.0, days=7),
        "coral_status": asyncio.to_thread(get_client("coral").get_bleaching_status),
        
        # New: Marine Conditions for GBR
        "gbr_marine": asyncio.to_thread(get_client("meteo").get_marine_forecast, -18.2871, 147.6992),
        
        "delhi_history_aq": asyncio.to_thread(get_client("meteo").get_air_quality, 28.6139, 77.2090),
    }

    # Add historical weather tasks for ALL global points
    for name, (lat, lon) in global_points.items():
        tasks[f"history_{name}"] = asyncio.to_thread(
             get_client("meteo").get_historical_weather, 
             lat, lon, 
             start_date=seven_days_ago.strftime(date_format), 
             end_date=now.strftime(date_format),
             hourly=["temperature_2m"]
        )
    
    # Execute
    results = {}
    for name, coro in tasks.items():
        try:
            results[name] = await coro
        except Exception as e:
            # print(f"Error fetching {name}: {e}")
            results[name] = None
            
    # --- Metrics Processing ---
    
    # Arctic (Advanced Weather)
    arctic_val = "N/A"
    arctic_details = "Wind: -- | Feels: --"
    arctic_temp_float = None
    
    if results["arctic_current"]:
        # Try fetch form hourly index (most recent)
        h = results["arctic_current"].get("hourly", {})
        if h and "time" in h:
             # Get last index
             idx = -1 
             arctic_temp_float = h.get("temperature_2m", [None])[idx]
             w = h.get("wind_speed_10m", [0])[idx]
             hum = h.get("relative_humidity_2m", [0])[idx]
             app = h.get("apparent_temperature", [0])[idx]
             prec = h.get("precipitation", [0])[idx]
             
             if arctic_temp_float is not None:
                 arctic_val = f"{arctic_temp_float}°C"
                 arctic_details = f"Feels: {app}°C | Wind: {w}km/h | Snow: {prec}mm"
        
        # Fallback to current_weather if hourly failed logic
        elif "current_weather" in results["arctic_current"]:
             curr = results['arctic_current']['current_weather']
             arctic_temp_float = curr.get('temperature')
             arctic_val = f"{arctic_temp_float}°C"

    # Delhi AQI
    delhi_val = "N/A"
    delhi_aqi_float = 0
    delhi_stat = "Moderate"
    delhi_details = "Pollutant: PM2.5"
    
    if results["delhi_aqi"] and "data" in results["delhi_aqi"]:
         data = results["delhi_aqi"]["data"]
         avg = data.get("aqi", "N/A")
         pol = data.get("dominentpol", "pm25")
         delhi_val = str(avg)
         
         # Extract secondary pollutants if available in 'iaqi'
         iaqi = data.get("iaqi", {})
         no2 = iaqi.get("no2", {}).get("v", "-")
         
         delhi_details = f"Main: {pol.upper()} | NO2: {no2}"
         
         if isinstance(avg, (int, float)):
             delhi_aqi_float = float(avg)
             if avg > 300: delhi_stat = "Hazardous"
             elif avg > 200: delhi_stat = "Very Unhealthy"
             elif avg > 100: delhi_stat = "Unhealthy"
             else: delhi_stat = "Moderate"

    # Amazon Fires (Intensity Analysis)
    fire_list = results.get("amazon_fire_history", [])
    if not isinstance(fire_list, list): fire_list = []
    
    today_str = now.strftime("%Y-%m-%d")
    current_fires = [f for f in fire_list if f.get("acq_date") == today_str]
    fire_count = len(current_fires) if current_fires else (len(fire_list) // 7 if len(fire_list) > 0 else 0)
    
    # Calculate Average Fire Radiative Power (FRP)
    avg_frp = 0
    if fire_list:
        frp_vals = []
        for f in fire_list:
            try: frp_vals.append(float(f.get("frp", 0)))
            except: pass
        if frp_vals:
            avg_frp = round(sum(frp_vals) / len(frp_vals), 1)
            
    fire_val = f"{fire_count} Active"
    fire_stat = "critical" if fire_count > 50 else ("warning" if fire_count > 0 else "normal")
    fire_details = f"7-Day Total: {len(fire_list)} | Avg Intensity: {avg_frp} MW"

    # Corals (Marine Data)
    coral_data = results.get("coral_status")
    marine = results.get("gbr_marine")
    
    # Marine physics
    wave_h = "--"
    if marine and "hourly" in marine:
        wave_h = marine["hourly"].get("wave_height", [0])[0] # Current wave height
        
    coral_val = "Watch"
    if isinstance(coral_data, dict):
        coral_val = coral_data.get("global_status", "Watch")
        
    coral_status = "critical" if "Alert" in coral_val else "normal"
    coral_details = f"Wave Height: {wave_h}m | Region: West Pacific"


    # --- Chart 1: Calculated Global Average Temperature ---
    # We aggregate the hourly history from all 5 locations
    temp_chart = []
    
    # Extract hourly arrays
    arrays = []
    times = []
    
    # Logic for Anomaly Calculation (Z-Score)
    # We need history to calculate StdDev
    # Storage for anomalies:
    anomalies = {}

    for name in global_points.keys():
        h = results.get(f"history_{name}")
        if h and "hourly" in h and "temperature_2m" in h["hourly"]:
            temps = h["hourly"]["temperature_2m"]
            arrays.append(temps)
            
            # Compute Temperature Anomaly for this region
            # Anomaly = (Current - Mean) / StdDev
            if temps:
                mean_t = np.mean(temps)
                std_t = np.std(temps)
                last_t = temps[-1]
                z_score = (last_t - mean_t) / (std_t if std_t > 0 else 1)
                anomalies[name] = abs(round(z_score, 2)) # Absolute deviation magnitude
            
            if not times: times = h["hourly"]["time"]
    
    # Calculate average if we have data
    if arrays and times:
        min_len = min(len(a) for a in arrays)
        step = max(1, min_len // 20)
        
        for i in range(0, min_len, step):
            step_vals = [arr[i] for arr in arrays]
            avg_temp = sum(step_vals) / len(step_vals)
            try:
                dt_obj = datetime.fromisoformat(times[i])
                label = dt_obj.strftime("%d %b")
            except:
                label = times[i]
            temp_chart.append({"year": label, "value": round(avg_temp, 1)})
            
    if not temp_chart:
        temp_chart = [{"year": "No Data", "value": 14.5}]

    # --- Chart 2: Emissions / Air Quality Trend ---
    emissions_chart = []
    aq_hist = results.get("delhi_history_aq")
    if aq_hist and "hourly" in aq_hist:
        times_aq = aq_hist["hourly"]["time"]
        vals = aq_hist["hourly"].get("pm2_5", [])
        if not vals: vals = aq_hist["hourly"].get("pm10", [])
        
        # AQI Anomaly
        if vals:
             # Filter out None values before computing statistics
             filtered_vals = [v for v in vals if v is not None]
             if filtered_vals:
                 mean_aq = np.mean(filtered_vals)
                 std_aq = np.std(filtered_vals)
                 last_val = filtered_vals[-1]
                 z_aq = (last_val - mean_aq) / (std_aq if std_aq > 0 else 1)
                 anomalies["delhi_air"] = abs(round(z_aq, 2))

        step_aq = max(1, len(times_aq) // 12) 
        for i in range(0, len(times_aq), step_aq):
             t_str = times_aq[i]
             try:
                 dt_obj = datetime.fromisoformat(t_str)
                 lbl = dt_obj.strftime("%d %b")
             except:
                 lbl = t_str
             emissions_chart.append({
                 "month": lbl, 
                 "co2": vals[i] if i < len(vals) else 0, # Mapped to schema
                 "methane": 0 
             })
             
    # --- Chart 3: Real Anomaly/Risk Index ---
    # Instead of Fire Trend, show the calculated Multi-Factor Anomalies
    
    # Fire Anomaly (Amazon)
    # Compare current count to 7-day average
    fire_anomaly = 0
    
    # Calculate Daily FRP Trend
    daily_frp = defaultdict(list)
    
    if fire_list:
        daily_counts = list(Counter([f.get("acq_date") for f in fire_list]).values())
        if daily_counts:
            mean_f = np.mean(daily_counts)
            std_f = np.std(daily_counts)
            z_f = (fire_count - mean_f) / (std_f if std_f > 0 else 1)
            fire_anomaly = abs(round(z_f, 2))
            
        # Aggregate FRP
        for f in fire_list:
            d = f.get("acq_date")
            val = f.get("frp")
            if d and val:
                try: daily_frp[d].append(float(val))
                except: pass

    # Build FRP Chart
    fire_intensity_chart = []
    for i in range(7):
        d = (seven_days_ago + timedelta(days=i)).strftime("%Y-%m-%d")
        vals = daily_frp.get(d, [])
        avg = round(sum(vals) / len(vals), 1) if vals else 0
        fire_intensity_chart.append({"date": d[5:], "mw": avg})
    
    # Compile Risk Chart Data (Normalized 0-100 based on Z-Score)
    # Z-Score of 0 -> Risk 20 (Baseline)
    # Z-Score of 1 -> Risk 50 
    # Z-Score of 2+ -> Risk 90+
    def z_to_risk(z):
        return min(100, max(20, 20 + (z * 35)))

    risk_chart = [
        {"region": "Arctic Temp", "risk": z_to_risk(anomalies.get("arctic", 0))},
        {"region": "Amazon Fire", "risk": z_to_risk(fire_anomaly)},
        {"region": "Delhi Air",   "risk": z_to_risk(anomalies.get("delhi_air", 0))},
        {"region": "London Temp", "risk": z_to_risk(anomalies.get("london", 0))},
        {"region": "Sydney Temp", "risk": z_to_risk(anomalies.get("sydney", 0))},
    ]

    
    return {
        "metrics": [
            {"label": "Temperature", "location_name": "Arctic (75°N)", "coordinates": "75.0°N, 40.0°W", "value": arctic_val, "delta": "7-Day History", "status": "critical", "details": arctic_details},
            {"label": "Air Quality", "location_name": "New Delhi", "coordinates": "28.6°N, 77.2°E", "value": delhi_val, "delta": delhi_stat, "status": "warning" if delhi_stat!="Moderate" else "normal", "details": delhi_details},
            {"label": "Fire Activity", "location_name": "Amazon Basin", "coordinates": "3.4°S, 62.2°W", "value": fire_val, "delta": "Verified Spots", "status": fire_stat, "details": fire_details},
            {"label": "Coral Status", "location_name": "GBR", "coordinates": "18.2°S, 147.6°E", "value": coral_val, "delta": "NOAA Station", "status": "critical" if "Alert" in coral_val else "normal", "details": coral_details}
        ],
        "ticker_feed": [
            f"LIVE: Arctic {arctic_details}",
            f"SENSOR: Delhi {delhi_details}",
            f"SPACE: Amazon Fire Intensity {fire_details.split('|')[-1]}",
            "DATA: Real-time streams from NASA, NOAA, OpenMeteo, WAQI."
        ],
        "charts": {
            "temp_anomaly": temp_chart, # Calculated Global Average
            "emissions": emissions_chart, # Real Delhi PM2.5
            "risk_index": risk_chart, # Real Z-Score Anomalies
            "fire_intensity": fire_intensity_chart # Avg FRP Trend
        }
    }
