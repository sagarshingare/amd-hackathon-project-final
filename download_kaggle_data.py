import kagglehub
import os
import zipfile
import pandas as pd
import numpy as np

# This script assumes you have authenticated with Kaggle.
# The most reliable way is to place your kaggle.json file in ~/.kaggle/
# See the README or documentation for instructions.

# Download latest version
path = kagglehub.competition_download('nyc-taxi-trip-duration')
print("Path to competition files:", path)

# --- Extract and Process Data into historical_delays.csv ---
train_zip = os.path.join(path, "train.zip")
train_csv = os.path.join(path, "train.csv")

if os.path.exists(train_zip):
    print("Extracting train.zip...")
    with zipfile.ZipFile(train_zip, 'r') as z:
        z.extractall(path)
    train_csv = os.path.join(path, "train.csv")

if not os.path.exists(train_csv):
    raise FileNotFoundError(f"Could not find train.csv in {path}")

print("Loading dataset into Pandas (sampling 200,000 rows for efficiency)...")
df = pd.read_csv(train_csv, nrows=200000)

# 1. Calculate distance using a vectorized Haversine formula
def haversine_vectorized(lat1, lon1, lat2, lon2):
    R = 3959.0 # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    return R * 2 * np.arcsin(np.sqrt(a))

print("Calculating trip distances...")
df['distance'] = haversine_vectorized(
    df['pickup_latitude'], df['pickup_longitude'],
    df['dropoff_latitude'], df['dropoff_longitude']
)

# 2. Derive traffic level proxy from pickup time
print("Deriving traffic_level proxy from timestamps...")
df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])
df['hour'] = df['pickup_datetime'].dt.hour

# Rule: Rush hours = 1.8, Mid-day = 1.2, Off-peak = 1.0
conditions = [
    (df['hour'].between(7, 10)) | (df['hour'].between(16, 19)),
    (df['hour'].between(11, 15))
]
df['traffic_level'] = np.select(conditions, [1.8, 1.2], default=1.0)

# 3. Compute delay (convert trip_duration from seconds to minutes)
df['delay'] = df['trip_duration'] / 60.0

# 4. Filter anomalies for clean ML training
print("Cleaning anomalous data...")
df = df[(df['distance'] > 0.1) & (df['distance'] < 50)]
df = df[(df['delay'] > 1) & (df['delay'] < 120)]

# 5. Format and save the final ML dataframe
final_df = df[['distance', 'traffic_level', 'delay']]

output_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(output_dir, exist_ok=True)
out_file = os.path.join(output_dir, "historical_delays.csv")

final_df.to_csv(out_file, index=False)
print(f"Success! {len(final_df)} rows processed and saved to {out_file}")

# 6. Generate deliveries.csv from the same dataset for the VRP Solver
print("Generating deliveries.csv for routing optimization...")
sample_df = df.sample(200, random_state=42)

delivery_records = []
for i, (_, row) in enumerate(sample_df.iterrows()):
    if i == 0:
        delivery_records.append({
            "order_id": "DEPOT",
            "latitude": row['pickup_latitude'],
            "longitude": row['pickup_longitude'],
            "demand": 0,
            "address": "NYC Taxi Depot",
            "city": "NYC",
            "time_window_start": 8 * 60,  # 8 AM in minutes
            "time_window_end": 18 * 60,   # 6 PM in minutes
        })
    else:
        # Assign morning or afternoon delivery windows
        if i % 2 == 0:
            time_start, time_end = (9 * 60, 12 * 60)  # 9 AM - 12 PM
        else:
            time_start, time_end = (13 * 60, 16 * 60) # 1 PM - 4 PM

        delivery_records.append({
            "order_id": f"ORD-{i}",
            "latitude": row['dropoff_latitude'],
            "longitude": row['dropoff_longitude'],
            "demand": np.random.randint(1, 4),
            "address": f"NYC Delivery {i}",
            "city": "NYC",
            "time_window_start": time_start,
            "time_window_end": time_end,
        })

delivery_out_file = os.path.join(output_dir, "deliveries.csv")
pd.DataFrame(delivery_records).to_csv(delivery_out_file, index=False)
print(f"Success! Created production routing dataset at {delivery_out_file}")
