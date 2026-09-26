import csv
import os
import sys
import random
import time
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

# Add src to path to import OpenMeteoClient
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../src"))

from data_sources.open_meteo import OpenMeteoClient

def fetch_and_process_data():
    client = OpenMeteoClient()
    
    # Define major historical events (Case Studies)
    # Format: (Name, Lat, Lon, StartDate, EndDate, Category)
    # Extended date ranges to capture build-up and after-effects + normal days for variety
    events = [
        # --- Hurricanes / Typhoons ---
        ("Hurricane Ian (FL)", 26.6406, -81.8723, "2022-09-01", "2022-10-30", "Hurricane"),
        ("Hurricane Katrina (NO)", 30.0668, -89.9315, "2005-08-15", "2005-09-15", "Hurricane"),
        ("Hurricane Sandy (NY)", 40.7128, -74.0060, "2012-10-15", "2012-11-15", "Hurricane"),
        ("Typhoon Haiyan (PH)", 11.0409, 125.0388, "2013-11-01", "2013-11-30", "Hurricane"),
        ("Hurricane Harvey (TX)", 29.7604, -95.3698, "2017-08-15", "2017-09-15", "Hurricane"),
        
        # --- Extreme Cold ---
        ("Texas Freeze 2021", 29.7604, -95.3698, "2021-01-15", "2021-03-15", "Cold Snap"),
        ("Polar Vortex 2019 (Chi)", 41.8781, -87.6298, "2019-01-15", "2019-02-15", "Cold Snap"),
        
        # --- Heatwaves ---
        ("Europe Heatwave 2022", 51.5074, -0.1278, "2022-06-01", "2022-09-01", "Heatwave"),
        ("PNW Heat Dome 2021", 45.5152, -122.6784, "2021-06-01", "2021-07-30", "Heatwave"),
        ("India Heatwave 2024", 28.6139, 77.2090, "2024-04-01", "2024-06-30", "Heatwave"),
        
        # --- Wildfires ---
        ("August Complex (CA)", 39.7817, -122.9286, "2020-08-01", "2020-11-01", "Wildfire"),
        ("Australian Black Summer", -35.2809, 149.1300, "2019-11-01", "2020-02-28", "Wildfire"),
        ("Canada Wildfires 2023", 53.9333, -116.5765, "2023-05-01", "2023-08-30", "Wildfire"),
        
        # --- Floods ---
        ("Chennai Floods 2023", 13.0827, 80.2707, "2023-11-01", "2023-12-31", "Flood"),
        ("Dubai Floods 2024", 25.2048, 55.2708, "2024-03-01", "2024-05-30", "Flood"),
        ("German Floods 2021", 50.9375, 6.9603, "2021-07-01", "2021-08-30", "Flood"),
        ("Pakistan Floods 2022", 24.8607, 67.0011, "2022-06-01", "2022-09-30", "Flood"),
        
        # --- Baseline / Normal Control (Extended) ---
        ("Miami Normal Year", 25.7617, -80.1918, "2023-01-01", "2023-06-30", "Normal"),
        ("London Normal Year", 51.5074, -0.1278, "2023-01-01", "2023-12-31", "Normal"),
        ("Tokyo Normal Year", 35.6762, 139.6503, "2023-01-01", "2023-12-31", "Normal"),
        ("Singapore Normal", 1.3521, 103.8198, "2023-01-01", "2023-06-30", "Normal"),
    ]

    raw_data = []
    print(f"Fetching data for {len(events)} case studies...")
    
    for name, lat, lon, start, end, category in events:
        print(f"  > Processing {name}...")
        try:
            # Fetch hourly historical data
            data = client.get_historical_weather(
                latitude=lat, 
                longitude=lon, 
                start_date=start, 
                end_date=end,
                hourly=["temperature_2m", "precipitation", "wind_speed_10m", "relative_humidity_2m"]
            )
            
            hourly = data.get("hourly", {})
            temps = hourly.get("temperature_2m", [])
            rain = hourly.get("precipitation", [])
            wind = hourly.get("wind_speed_10m", [])
            humidity = hourly.get("relative_humidity_2m", [])
            
            # Aggregate to daily stats to create multiple data points per event
            # We'll treat every 24h block as a data point
            total_hours = len(temps)
            for i in range(0, total_hours, 24):
                if i + 24 > total_hours: break
                
                # Extract 24h slice
                slice_temps = temps[i:i+24]
                slice_rain = rain[i:i+24]
                slice_wind = wind[i:i+24]
                slice_hum = humidity[i:i+24]
                
                # Calculate aggregated features
                max_temp = max(slice_temps)
                min_temp = min(slice_temps)
                avg_temp = sum(slice_temps) / 24
                total_rain = sum(slice_rain)
                max_wind = max(slice_wind)
                avg_hum = sum(slice_hum) / 24
                
                raw_data.append({
                    "event_name": name,
                    "category": category,
                    "max_temp": round(max_temp, 2),
                    "min_temp": round(min_temp, 2),
                    "avg_temp": round(avg_temp, 2),
                    "total_rain": round(total_rain, 2),
                    "max_wind": round(max_wind, 2),
                    "avg_humidity": round(avg_hum, 2)
                })
                
        except Exception as e:
            print(f"    Error fetching {name}: {e}")
            
        # Polite delay for API
        time.sleep(1)

    print(f"Fetched {len(raw_data)} raw records. Running Unsupervised Anomaly Detection...")

    # --- Unsupervised Learning Phase ---
    
    # 1. Prepare Feature Matrix for Isolation Forest
    # Features: Max Temp, Min Temp, Total Rain, Max Wind
    # We ignore "event_name" and "category" for the anomaly detection itself related to physics
    feature_matrix = []
    for record in raw_data:
        feature_matrix.append([
            record["max_temp"],
            record["min_temp"],
            record["total_rain"],
            record["max_wind"]
        ])
    
    X = np.array(feature_matrix)
    
    # 2. Train Isolation Forest
    # contamination='auto' allows the model to determine the proportion of outliers
    iso_forest = IsolationForest(contamination=0.15, random_state=42)
    iso_forest.fit(X)
    
    # 3. Get Anomaly Scores
    # decision_function returns negative for anomalies, positive for inliers
    # We want the opposite: lower score = normal, higher score = anomalous
    scores = -iso_forest.decision_function(X)
    
    # 4. Normalize Scores to 1-10 Range for Impact Score
    # We use MinMaxScaler to map the raw anomaly scores to 1.0 - 10.0
    scaler = MinMaxScaler(feature_range=(1.0, 10.0))
    impact_scores = scaler.fit_transform(scores.reshape(-1, 1)).flatten()
    
    # 5. Assign Scores back to Data
    final_dataset = []
    for i, record in enumerate(raw_data):
        impact = float(impact_scores[i])
        
        # Calculate Probability of Disruption based on Impact
        # Sigmoid function centered at impact 7.5
        prob = 1 / (1 + np.exp(-(impact - 7.5)))
        
        record["impact_score"] = round(impact, 2)
        record["prob_disruption"] = round(prob, 2)
        final_dataset.append(record)
        
    # Validating distribution
    avg_impact = sum(d["impact_score"] for d in final_dataset) / len(final_dataset)
    print(f"Average unsupervised impact score: {avg_impact:.2f}")

    # Save to CSV
    output_dir = os.path.join(os.path.dirname(__file__), "../../../data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "real_causal_data.csv")
    
    keys = final_dataset[0].keys() if final_dataset else []
    with open(output_file, 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(final_dataset)
        
    print(f"\nSuccessfully generated dataset with {len(final_dataset)} records.")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    fetch_and_process_data()
