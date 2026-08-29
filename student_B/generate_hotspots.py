"""
Student B - Hotspot Analysis & DBSCAN Execution Script.

Reproduces the exact DBSCAN clustering and feature aggregation pipeline
from student_B/student_B_DBSCAN.ipynb over the preprocessed UK Road Safety dataset.
"""

import logging
import os
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("student_b_dbscan")

EARTH_RADIUS = 6371000.0  # Earth radius in metres
EPS_METERS = 500.0        # 500 metres neighborhood radius
EPS_RADIANS = EPS_METERS / EARTH_RADIUS
MIN_SAMPLES = 25          # Minimum samples for dense cluster core


def reduce_memory(df: pd.DataFrame) -> pd.DataFrame:
    """Downcast numeric types to reduce RAM footprint."""
    start_mem = df.memory_usage(deep=True).sum() / (1024 ** 2)
    for col in df.columns:
        col_type = df[col].dtype
        if pd.api.types.is_integer_dtype(col_type):
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min >= np.iinfo(np.int8).min and c_max <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif c_min >= np.iinfo(np.int16).min and c_max <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        elif pd.api.types.is_float_dtype(col_type):
            df[col] = df[col].astype(np.float32)
    end_mem = df.memory_usage(deep=True).sum() / (1024 ** 2)
    logger.info(f"Memory reduced from {start_mem:.2f} MB to {end_mem:.2f} MB")
    return df


def run_pipeline(
    input_csv: Path,
    output_dir: Path,
) -> None:
    """Execute the complete Student B DBSCAN hotspot pipeline."""
    if not input_csv.exists():
        raise FileNotFoundError(f"Input dataset not found at {input_csv}")

    output_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # 1. Load dataset
    logger.info(f"Loading processed dataset from {input_csv}...")
    df = pd.read_csv(input_csv)
    raw_count = len(df)
    logger.info(f"Loaded {raw_count:,} records with {df.shape[1]} columns.")

    # 2. Preprocessing & Clean up
    drop_cols = [c for c in ["Year", "Month", "Day"] if c in df.columns]
    if drop_cols:
        df.drop(columns=drop_cols, inplace=True)
        logger.info(f"Dropped unused date breakdown columns: {drop_cols}")

    if "Hour" in df.columns and df["Hour"].isnull().any():
        hour_mode = df["Hour"].mode()[0]
        df["Hour"].fillna(hour_mode, inplace=True)
        logger.info(f"Imputed missing Hour with mode: {hour_mode}")

    df = reduce_memory(df)

    # 3. Coordinate validation
    if "Latitude" not in df.columns or "Longitude" not in df.columns:
        raise ValueError("Dataset missing 'Latitude' or 'Longitude' columns.")

    geo_df = df[["Latitude", "Longitude"]].copy()
    valid_mask = (
        geo_df["Latitude"].notnull()
        & geo_df["Longitude"].notnull()
        & (geo_df["Latitude"] != 0)
        & (geo_df["Longitude"] != 0)
    )
    geo_df = geo_df[valid_mask]
    valid_count = len(geo_df)
    logger.info(f"Valid coordinates: {valid_count:,} / {raw_count:,} ({valid_count/raw_count*100:.2f}%)")

    # Save processed coordinates
    proc_coords_file = output_dir / "processed_coordinates.csv"
    geo_df.to_csv(proc_coords_file, index=False)
    logger.info(f"Saved processed coordinates to {proc_coords_file}")

    # 4. Radian conversion
    coords_rad = np.radians(geo_df[["Latitude", "Longitude"]].values)

    # 5. DBSCAN Clustering
    logger.info(f"Running DBSCAN (eps={EPS_METERS}m / {EPS_RADIANS:.6f} rad, min_samples={MIN_SAMPLES}, metric=haversine, algorithm=ball_tree)...")
    t_db_start = time.time()
    dbscan = DBSCAN(
        eps=EPS_RADIANS,
        min_samples=MIN_SAMPLES,
        metric="haversine",
        algorithm="ball_tree",
    )
    clusters = dbscan.fit_predict(coords_rad)
    t_db_end = time.time()
    logger.info(f"DBSCAN execution completed in {t_db_end - t_db_start:.2f} seconds.")

    geo_df["Cluster"] = clusters
    n_noise = int((clusters == -1).sum())
    n_clusters = int(len(set(clusters)) - (1 if -1 in clusters else 0))
    logger.info(f"Clusters found: {n_clusters:,} | Noise points: {n_noise:,}")

    # 6. Map back to full dataset
    df_clustered = df.copy()
    df_clustered["Cluster"] = -1
    df_clustered.loc[geo_df.index, "Cluster"] = geo_df["Cluster"]

    # Save accident clusters matching notebook Cell 41 (Latitude, Longitude, Cluster)
    clusters_file = output_dir / "accident_clusters.csv"
    geo_df.to_csv(clusters_file, index=False)
    logger.info(f"Saved accident clusters to {clusters_file}")

    # 7. Hotspot Summary Extraction (Non-noise only)
    hotspot_df = df_clustered[df_clustered["Cluster"] != -1].copy()
    logger.info(f"Aggregating metadata for {len(hotspot_df):,} hotspot accident records across {n_clusters:,} clusters...")

    # Center coordinates (Notebook Cell 45)
    cluster_centers = (
        hotspot_df.groupby("Cluster")
        .agg({"Latitude": "mean", "Longitude": "mean"})
        .reset_index()
        .rename(columns={"Latitude": "Center_Latitude", "Longitude": "Center_Longitude"})
    )

    # Accident count (Notebook Cell 46)
    accident_counts = (
        hotspot_df.groupby("Cluster")
        .size()
        .reset_index(name="Total_Accidents")
    )

    # Dominant severity (Notebook Cell 47)
    if "Accident_Severity" in hotspot_df.columns:
        severity = (
            hotspot_df.groupby("Cluster")["Accident_Severity"]
            .agg(lambda x: x.mode().iloc[0])
            .reset_index()
            .rename(columns={"Accident_Severity": "Dominant_Severity"})
        )
    else:
        severity = pd.DataFrame({"Cluster": cluster_centers["Cluster"], "Dominant_Severity": "Unknown"})

    # Dominant weather (Notebook Cells 48-49)
    weather_cols = [c for c in hotspot_df.columns if c.startswith("Weather_Conditions_")]
    if weather_cols:
        weather_sum = hotspot_df.groupby("Cluster")[weather_cols].sum()
        dom_weather = weather_sum.idxmax(axis=1).str.replace("Weather_Conditions_", "", regex=False).reset_index()
        dom_weather.columns = ["Cluster", "Dominant_Weather"]
    else:
        dom_weather = pd.DataFrame({"Cluster": cluster_centers["Cluster"], "Dominant_Weather": "Unknown"})

    # Dominant road type (Notebook Cell 50)
    road_cols = [c for c in hotspot_df.columns if c.startswith("Road_Type_")]
    if road_cols:
        road_sum = hotspot_df.groupby("Cluster")[road_cols].sum()
        dom_road = road_sum.idxmax(axis=1).str.replace("Road_Type_", "", regex=False).reset_index()
        dom_road.columns = ["Cluster", "Dominant_Road_Type"]
    else:
        dom_road = pd.DataFrame({"Cluster": cluster_centers["Cluster"], "Dominant_Road_Type": "Unknown"})

    # Average speed (Notebook Cell 51)
    if "Speed_limit" in hotspot_df.columns:
        speed = (
            hotspot_df.groupby("Cluster")["Speed_limit"]
            .mean()
            .round(2)
            .reset_index()
            .rename(columns={"Speed_limit": "Average_Speed"})
        )
    else:
        speed = pd.DataFrame({"Cluster": cluster_centers["Cluster"], "Average_Speed": 0.0})

    # Average casualties (Notebook Cell 52)
    if "Number_of_Casualties" in hotspot_df.columns:
        casualties = (
            hotspot_df.groupby("Cluster")["Number_of_Casualties"]
            .mean()
            .round(2)
            .reset_index()
            .rename(columns={"Number_of_Casualties": "Average_Casualties"})
        )
    else:
        casualties = pd.DataFrame({"Cluster": cluster_centers["Cluster"], "Average_Casualties": 0.0})

    # Peak hour (Notebook Cell 53)
    if "Hour" in hotspot_df.columns:
        hour = (
            hotspot_df.groupby("Cluster")["Hour"]
            .agg(lambda x: x.mode().iloc[0])
            .reset_index()
            .rename(columns={"Hour": "Peak_Hour"})
        )
    else:
        hour = pd.DataFrame({"Cluster": cluster_centers["Cluster"], "Peak_Hour": 17})

    # Merge core metadata in exact notebook order (Notebook Cell 54)
    summary = cluster_centers
    for df_part in [accident_counts, severity, dom_weather, dom_road, speed, casualties, hour]:
        summary = summary.merge(df_part, on="Cluster")

    # Additional Enhancement (documented in audit): Exact severity counts
    if "Accident_Severity" in hotspot_df.columns:
        sev_counts = (
            hotspot_df.groupby(["Cluster", "Accident_Severity"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        sev_cols_mapping = {}
        for c in sev_counts.columns:
            c_lower = str(c).strip().lower()
            if "fatal" in c_lower:
                sev_cols_mapping[c] = "Fatal_Count"
            elif "serious" in c_lower:
                sev_cols_mapping[c] = "Serious_Count"
            elif "slight" in c_lower:
                sev_cols_mapping[c] = "Slight_Count"
        sev_counts.rename(columns=sev_cols_mapping, inplace=True)
        for expected_col in ["Fatal_Count", "Serious_Count", "Slight_Count"]:
            if expected_col not in sev_counts.columns:
                sev_counts[expected_col] = 0
        summary = summary.merge(sev_counts[["Cluster", "Fatal_Count", "Serious_Count", "Slight_Count"]], on="Cluster", how="left")

    # Sort descending by Total_Accidents (Notebook Cell 55)
    summary.sort_values("Total_Accidents", ascending=False, inplace=True)
    summary.reset_index(drop=True, inplace=True)

    # Save hotspot summary (Notebook Cell 56)
    summary_file = output_dir / "hotspot_summary.csv"
    summary.to_csv(summary_file, index=False)
    logger.info(f"Successfully saved {len(summary):,} hotspot clusters to {summary_file}")

    total_time = time.time() - t0
    logger.info(f"Student B Pipeline execution complete in {total_time:.2f} seconds.")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    default_input = project_root / "data" / "output" / "processed_data.csv"
    if not default_input.exists():
        default_input = project_root / "data" / "raw" / "processed_data.csv"

    default_output = project_root / "data" / "output"
    run_pipeline(default_input, default_output)

