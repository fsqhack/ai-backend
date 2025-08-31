import random
import uuid
from datetime import timedelta
import math

def simulate_scenario_points(user_id, trip_id, scenario, start_lat, start_lon, start_alt, start_time, end_time, time_interval=5):
    """
    Simulate health + movement points for different trekking/beach scenarios
    with more natural human-like movement (irregular steps, pauses, elevation bumps).
    """
    scenario_profiles = {
        "Trekking with palpitation problem": {
            "hr": (110, 25),
            "cal": (8, 3),
            "o2": (94, 3),
            "movement": "trekking"
        },
        "Trekking in low oxygen and high altitude area": {
            "hr": (120, 20),
            "cal": (10, 4),
            "o2": (85, 5),
            "movement": "trekking"
        },
        "Healthy person in a normal trekking": {
            "hr": (85, 12),
            "cal": (6, 2),
            "o2": (98, 1),
            "movement": "trekking"
        },
        "Roaming about in a beach": {
            "hr": (75, 8),
            "cal": (3, 1),
            "o2": (99, 0.5),
            "movement": "beach_walk"
        }
    }

    if scenario not in scenario_profiles:
        raise ValueError(f"Unknown scenario: {scenario}")

    profile = scenario_profiles[scenario]

    points = []
    ts = start_time
    idx = 0

    # Current position
    lat, lon, alt = start_lat, start_lon, start_alt
    heading = random.uniform(0, 2 * math.pi)  # random initial direction

    while ts <= end_time:
        # === Movement Simulation ===
        if profile["movement"] == "trekking":
            # Random step length (like human stride, 0.5–1.2 m equivalent in degrees)
            step = random.uniform(0.5e-4, 1.2e-4)

            # Small random direction change (turns while walking)
            heading += random.uniform(-0.2, 0.2)

            # Apply movement with jitter
            lat += step * math.cos(heading) + random.uniform(-2e-6, 2e-6)
            lon += step * math.sin(heading) + random.uniform(-2e-6, 2e-6)

            # Altitude: gradual climb but bumpy
            alt += random.gauss(0.3, 1.2)

            # Occasional downhill step (trekking trails are not always up)
            if random.random() < 0.1:
                alt -= random.uniform(0.5, 2.0)

            # Random pause events (person stops to rest/breathe)
            if random.random() < 0.05:
                step = 0
                heading += random.uniform(-0.5, 0.5)  # reorient
                alt += random.uniform(-0.2, 0.5)

            speed_x = step * 800 + random.uniform(-0.2, 0.2)
            speed_y = step * 800 + random.uniform(-0.2, 0.2)
            speed_z = (alt - start_alt) / (idx + 1 + 1e-5)

        elif profile["movement"] == "beach_walk":
            # Flatter movement with lots of direction changes
            step = random.uniform(0.3e-4, 0.8e-4)
            heading += random.uniform(-0.5, 0.5)  # meandering

            lat += step * math.cos(heading) + random.uniform(-5e-6, 5e-6)
            lon += step * math.sin(heading) + random.uniform(-5e-6, 5e-6)
            alt += random.uniform(-0.003, 0.003)  # nearly flat

            speed_x = step * 1000
            speed_y = step * 1000
            speed_z = 0

        else:
            # fallback random walk
            lat += random.uniform(-1e-4, 1e-4)
            lon += random.uniform(-1e-4, 1e-4)
            alt += random.uniform(-1, 1)
            speed_x = random.uniform(0.1, 1.0)
            speed_y = random.uniform(0.1, 1.0)
            speed_z = random.uniform(0.0, 0.1)

        # === Health metrics ===
        hr = max(40, int(random.gauss(profile["hr"][0], profile["hr"][1])))
        cal = max(0, int(random.gauss(profile["cal"][0], profile["cal"][1])))
        o2 = min(100, max(70, int(random.gauss(profile["o2"][0], profile["o2"][1]))))

        # HR spikes if climbing or pause (simulating exertion/recovery)
        if speed_z > 0.2:
            hr += random.randint(5, 15)
        if random.random() < 0.05:  # fatigue dip
            o2 -= random.randint(1, 5)

        point = {
            "point_id": f"pt-{user_id}-{trip_id}-{ts.isoformat()}",
            "trip_id": trip_id,
            "user_id": user_id,
            "timestamp": ts.isoformat(),
            "data": {
                "latitude": lat,
                "longitude": lon,
                "altitude": alt,
                "speed_x": speed_x,
                "speed_y": speed_y,
                "speed_z": speed_z,
                "heart_rate": hr,
                "calories_burned": cal,
                "o2_saturation": o2,
                "distance_traveled": idx * step * 100  # approx meters
            }
        }
        points.append(point)

        ts += timedelta(seconds=time_interval)
        idx += 1

    return points







import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata
import plotly.io as pio
pio.renderers.default = "browser"


def plot_3d_contour(points, metric_col="heart_rate"):
    """
    Create an interactive 3D contour plot of latitude, longitude, altitude vs metric value.

    Parameters:
    - points: list of dicts, each containing 'data' with 'latitude', 'longitude', 'altitude', and metric_col
    - metric_col: str, column name of the metric to visualize (inside data)
    """
    # Flatten list of dicts into a DataFrame
    data = pd.DataFrame([p["data"] for p in points])

    # Extract arrays
    lats = data["latitude"].values
    lons = data["longitude"].values
    alts = data["altitude"].values
    metric = data[metric_col].values

    # Create grid
    grid_x, grid_y, grid_z = np.mgrid[
        lats.min():lats.max():50j,
        lons.min():lons.max():50j,
        alts.min():alts.max():50j
    ]

    # Interpolate metric values
    grid_metric = griddata(
        (lats, lons, alts), metric,
        (grid_x, grid_y, grid_z),
        method="linear"
    )

    # Create interactive 3D isosurface plot
    fig = go.Figure()

    fig.add_trace(go.Isosurface(
        x=grid_x.flatten(),
        y=grid_y.flatten(),
        z=grid_z.flatten(),
        value=grid_metric.flatten(),
        isomin=np.nanmin(metric),
        isomax=np.nanmax(metric),
        surface_count=5,
        colorscale="Viridis",
        caps=dict(x_show=False, y_show=False, z_show=False),
        opacity=0.6
    ))

    # Also show original data points as scatter
    fig.add_trace(go.Scatter3d(
        x=lats, y=lons, z=alts,
        mode="markers",
        marker=dict(size=4, color=metric, colorscale="Viridis", colorbar=dict(title=metric_col)),
        name="Data points"
    ))

    fig.update_layout(
        scene=dict(
            xaxis_title="Latitude",
            yaxis_title="Longitude",
            zaxis_title="Altitude"
        ),
        title=f"3D Contour of {metric_col}"
    )

    fig.show()