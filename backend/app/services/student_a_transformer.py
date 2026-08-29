from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
import pickle

import numpy as np
import pandas as pd

from app.schemas.severity import SeverityPredictionRequest

logger = logging.getLogger(__name__)

# Fallback training-set median values derived from dataset preprocessing
TRAINING_MEDIANS: dict[str, float] = {
    "1st_Road_Number": 118.0,
    "2nd_Road_Number": 0.0,
    "Did_Police_Officer_Attend_Scene_of_Accident": 1.0,
    "Latitude": 52.23759,
    "Local_Authority_(District)": 195.0,
    "Local_Authority_(Highway)": 96.0,
    "Location_Easting_OSGR": 443050.0,
    "Location_Northing_OSGR": 261185.0,
    "Longitude": -1.362233,
    "LSOA_of_Accident_Location": 18604.0,
    "Number_of_Casualties": 1.0,
    "Number_of_Vehicles": 2.0,
    "Pedestrian_Crossing-Human_Control": 0.0,
    "Pedestrian_Crossing-Physical_Facilities": 0.0,
    "Police_Force": 1.0,
    "Speed_limit": 30.0,
    "Year": 2015.0,
    "Age_of_Vehicle_mean": 7.0,
    "Age_of_Vehicle_max": 7.0,
    "Engine_Capacity_.CC._mean": 1598.0,
    "Engine_Capacity_.CC._max": 1598.0,
    "Driver_IMD_Decile_mean": 5.0,
    "Driver_IMD_Decile_max": 5.0,
    "Number_of_Vehicles_Involved": 2.0,
    "Vehicle_Type_Diversity": 1.0,
    "Dominant_Vehicle_Type": 9.0,
    "Month": 6.0,
    "Day": 15.0,
    "Hour": 14.0,
    "Is_Weekend": 0.0,
    "Is_Rush_Hour": 0.0,
    "Is_Peak_Hour": 0.0,
    "Is_Night": 0.0,
    "Is_Morning": 0.0,
    "Is_Evening": 0.0,
    "Bad_Weather_Flag": 0.0,
    "Poor_Visibility_Flag": 0.0,
    "Road_Risk_Score": 1.71,
}

BAD_WEATHER_KEYWORDS = {"rain", "snow", "fog", "mist", "wind", "storm", "hail"}
POOR_VISIBILITY_KEYWORDS = {"dark_unlit", "no_lighting", "unlit", "darkness - no lighting", "darkness - lights unlit"}


class StudentATransformer:
    """Transforms raw user/frontend accident prediction requests into the exact 138-feature
    matrix expected by Student A's Random Forest classifier.
    """

    def __init__(self, feature_names: Sequence[str] | None = None) -> None:
        self.feature_names = list(feature_names) if feature_names else []

    @classmethod
    def from_features_file(cls, features_path: Path) -> "StudentATransformer":
        """Initialize transformer with the verified 138-feature list from features.pkl."""
        with open(features_path, "rb") as f:
            features = pickle.load(f)
        return cls(feature_names=features)

    def transform(self, requests: list[SeverityPredictionRequest]) -> pd.DataFrame:
        """Transform a list of accident requests into a DataFrame with 138 columns."""
        rows = [self._transform_single(req) for req in requests]
        df = pd.DataFrame(rows)

        # Ensure all 138 features exist in the exact required order
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = TRAINING_MEDIANS.get(col, 0.0)

        # Re-order and fill any remaining NaNs
        df = df[self.feature_names].copy()
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(TRAINING_MEDIANS).fillna(0.0)

        return df

    def _transform_single(self, req: SeverityPredictionRequest) -> dict[str, Any]:
        """Extract and engineer features for a single accident request."""
        row: dict[str, Any] = {}

        # 1. Date & Time Parsing
        dt = req.occurred_at
        if dt is None:
            if req.accident_date:
                time_str = req.accident_time or "12:00"
                try:
                    dt = datetime.strptime(f"{req.accident_date} {time_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    try:
                        dt = datetime.strptime(f"{req.accident_date} {time_str}", "%d/%m/%Y %H:%M")
                    except ValueError:
                        dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

        year = float(dt.year)
        month = float(dt.month)
        day = float(dt.day)
        hour = float(dt.hour)
        weekday_name = req.day_of_week.capitalize() if req.day_of_week else dt.strftime("%A")

        row["Year"] = year
        row["Month"] = month
        row["Day"] = day
        row["Hour"] = hour

        # Day flags
        is_weekend = 1 if (weekday_name.lower() in ("saturday", "sunday") or dt.weekday() in (5, 6)) else 0
        row["Is_Weekend"] = is_weekend
        row["Is_Rush_Hour"] = 1 if int(hour) in (7, 8, 9, 16, 17, 18) else 0
        row["Is_Peak_Hour"] = 1 if int(hour) in (16, 17, 8) else 0
        row["Is_Night"] = 1 if (hour >= 20 or hour < 6) else 0
        row["Is_Morning"] = 1 if (6 <= hour <= 11) else 0
        row["Is_Evening"] = 1 if (17 <= hour <= 20) else 0

        # Season
        if month in (12, 1, 2):
            season = "Winter"
        elif month in (3, 4, 5):
            season = "Spring"
        elif month in (6, 7, 8):
            season = "Summer"
        else:
            season = "Autumn"

        # 2. Coordinates & Road info
        lat = float(req.latitude) if req.latitude is not None else TRAINING_MEDIANS["Latitude"]
        lon = float(req.longitude) if req.longitude is not None else TRAINING_MEDIANS["Longitude"]
        speed_limit = float(req.speed_limit) if req.speed_limit is not None else 30.0
        num_vehicles = float(req.number_of_vehicles) if req.number_of_vehicles is not None else 2.0
        num_casualties = float(req.number_of_casualties) if req.number_of_casualties is not None else 1.0

        row["Latitude"] = lat
        row["Longitude"] = lon
        row["Speed_limit"] = speed_limit
        row["Number_of_Vehicles"] = num_vehicles
        row["Number_of_Casualties"] = num_casualties

        # Estimated OSGR from Lat/Lon if not supplied
        row["Location_Easting_OSGR"] = 443050.0 + (lon - (-1.36)) * 70000.0
        row["Location_Northing_OSGR"] = 261185.0 + (lat - 52.23) * 111000.0
        row["1st_Road_Number"] = 118.0
        row["2nd_Road_Number"] = 0.0
        row["Did_Police_Officer_Attend_Scene_of_Accident"] = 1.0
        row["Pedestrian_Crossing-Human_Control"] = 0.0
        row["Pedestrian_Crossing-Physical_Facilities"] = 0.0

        # Administrative / Fleet defaults
        vehicle_age_mean = float(req.age_of_vehicle_mean) if req.age_of_vehicle_mean is not None else 7.0
        row["Age_of_Vehicle_mean"] = vehicle_age_mean
        row["Age_of_Vehicle_max"] = vehicle_age_mean
        row["Engine_Capacity_.CC._mean"] = 1598.0
        row["Engine_Capacity_.CC._max"] = 1598.0
        row["Driver_IMD_Decile_mean"] = 5.0
        row["Driver_IMD_Decile_max"] = 5.0
        row["Number_of_Vehicles_Involved"] = num_vehicles
        row["Vehicle_Type_Diversity"] = 1.0
        row["Dominant_Vehicle_Type"] = 9.0  # Car
        row["Police_Force"] = 1.0
        row["Local_Authority_(District)"] = 195.0
        row["Local_Authority_(Highway)"] = 96.0
        row["LSOA_of_Accident_Location"] = 18604.0

        # 3. Risk & Environmental flags
        weather_raw = (req.weather_conditions or req.weather or "fine").lower()
        surface_raw = (req.road_surface_conditions or req.road_surface or "dry").lower()
        light_raw = (req.light_conditions or "daylight").lower()
        urban_raw = (req.urban_or_rural_area or req.area_type or "urban").lower()
        road_type_raw = (req.road_type or "single_carriageway").lower()
        junct_ctrl_raw = (req.junction_control or "not_at_junction").lower()
        junct_dtl_raw = (req.junction_detail or "not_at_junction").lower()

        bad_weather = 1 if any(k in weather_raw for k in BAD_WEATHER_KEYWORDS) else 0
        poor_vis = 1 if any(k in light_raw for k in POOR_VISIBILITY_KEYWORDS) else 0
        is_wet_ice_snow = any(k in surface_raw for k in ("wet", "ice", "frost", "snow", "flood"))

        row["Bad_Weather_Flag"] = bad_weather
        row["Poor_Visibility_Flag"] = poor_vis

        # Road Risk Score calculation
        road_risk_score = (
            ((speed_limit / 70.0) * 3.0)
            + (bad_weather * 2.0)
            + (poor_vis * 2.0)
            + (1.5 if is_wet_ice_snow else 0.0)
        )
        row["Road_Risk_Score"] = round(road_risk_score, 2)

        # Traffic Density Indicator
        if num_vehicles <= 1:
            density_cat = "Single_Vehicle"
        elif num_vehicles == 2:
            density_cat = "Two_Vehicle"
        elif num_vehicles <= 4:
            density_cat = "Moderate"
        else:
            density_cat = "High_Density"

        # 4. Outlier Flags (IQR bounds verified from training)
        row["Number_of_Casualties_Outlier"] = not (num_casualties == 1.0)
        row["Age_of_Vehicle_mean_Outlier"] = not (3.0 <= vehicle_age_mean <= 11.0)
        row["Road_Risk_Score_Outlier"] = not (-1.27 <= road_risk_score <= 5.56)
        row["Number_of_Vehicles_Outlier"] = not (-0.5 <= num_vehicles <= 3.5)
        row["Speed_limit_Outlier"] = not (0.0 <= speed_limit <= 80.0)

        # 5. Student A Interaction Terms
        row["Vehicles_Per_Casualty"] = num_vehicles / (num_casualties + 1.0)
        row["Casualties_Per_Vehicle"] = num_casualties / (num_vehicles + 1.0)
        row["Total_Involved"] = num_vehicles + num_casualties
        row["Speed_Vehicle_Risk"] = speed_limit * num_vehicles
        row["Speed_Casualty_Risk"] = speed_limit * num_casualties
        row["RoadRisk_Speed"] = road_risk_score * speed_limit
        row["RoadRisk_Vehicles"] = road_risk_score * num_vehicles
        row["RoadRisk_Casualties"] = road_risk_score * num_casualties
        row["VehicleAge_Speed"] = vehicle_age_mean * speed_limit
        row["VehicleAge_Vehicles"] = vehicle_age_mean * num_vehicles

        # 6. One-Hot Encoded Dummies
        # InScotland
        row["InScotland_No"] = 1
        row["InScotland_Unknown"] = 0
        row["InScotland_Yes"] = 0

        # Urban or Rural
        is_rural = "rural" in urban_raw
        row["Urban_or_Rural_Area_Rural"] = 1 if is_rural else 0
        row["Urban_or_Rural_Area_Unallocated"] = 0
        row["Urban_or_Rural_Area_Urban"] = 0 if is_rural else 1

        # Traffic Density
        row["Traffic_Density_Indicator_Single_Vehicle"] = 1 if density_cat == "Single_Vehicle" else 0
        row["Traffic_Density_Indicator_Two_Vehicle"] = 1 if density_cat == "Two_Vehicle" else 0
        row["Traffic_Density_Indicator_Moderate"] = 1 if density_cat == "Moderate" else 0
        row["Traffic_Density_Indicator_High_Density"] = 1 if density_cat == "High_Density" else 0

        # Season
        row["Season_Autumn"] = 1 if season == "Autumn" else 0
        row["Season_Spring"] = 1 if season == "Spring" else 0
        row["Season_Summer"] = 1 if season == "Summer" else 0
        row["Season_Unknown"] = 0
        row["Season_Winter"] = 1 if season == "Winter" else 0

        # Road Type
        row["Road_Type_Dual Carriageway"] = 1 if "dual" in road_type_raw else 0
        row["Road_Type_One Way Street"] = 1 if "one" in road_type_raw else 0
        row["Road_Type_Roundabout"] = 1 if "roundabout" in road_type_raw else 0
        row["Road_Type_Single Carriageway"] = 1 if ("single" in road_type_raw or "default" in road_type_raw) else 0
        row["Road_Type_Slip Road"] = 1 if "slip" in road_type_raw else 0
        row["Road_Type_Unknown"] = 0
        if not any([row["Road_Type_Dual Carriageway"], row["Road_Type_One Way Street"], row["Road_Type_Roundabout"], row["Road_Type_Single Carriageway"], row["Road_Type_Slip Road"]]):
            row["Road_Type_Single Carriageway"] = 1

        # Road Surface Conditions
        row["Road_Surface_Conditions_Dry"] = 1 if "dry" in surface_raw else 0
        row["Road_Surface_Conditions_Flood Over 3Cm. Deep"] = 1 if "flood" in surface_raw else 0
        row["Road_Surface_Conditions_Frost Or Ice"] = 1 if ("frost" in surface_raw or "ice" in surface_raw) else 0
        row["Road_Surface_Conditions_Snow"] = 1 if "snow" in surface_raw else 0
        row["Road_Surface_Conditions_Unknown"] = 0
        row["Road_Surface_Conditions_Wet Or Damp"] = 1 if ("wet" in surface_raw or "damp" in surface_raw) else 0
        if not any([row["Road_Surface_Conditions_Dry"], row["Road_Surface_Conditions_Flood Over 3Cm. Deep"], row["Road_Surface_Conditions_Frost Or Ice"], row["Road_Surface_Conditions_Snow"], row["Road_Surface_Conditions_Wet Or Damp"]]):
            row["Road_Surface_Conditions_Dry"] = 1

        # 1st Road Class
        row["1st_Road_Class_A"] = 1
        row["1st_Road_Class_A(M)"] = 0
        row["1st_Road_Class_B"] = 0
        row["1st_Road_Class_C"] = 0
        row["1st_Road_Class_Motorway"] = 0
        row["1st_Road_Class_Unclassified"] = 0

        # 2nd Road Class
        row["2nd_Road_Class_A"] = 0
        row["2nd_Road_Class_A(M)"] = 0
        row["2nd_Road_Class_B"] = 0
        row["2nd_Road_Class_C"] = 0
        row["2nd_Road_Class_Motorway"] = 0
        row["2nd_Road_Class_Unclassified"] = 1
        row["2nd_Road_Class_Unknown"] = 0

        # Light Conditions
        row["Light_Conditions_Darkness - Lighting Unknown"] = 0
        row["Light_Conditions_Darkness - Lights Lit"] = 1 if ("lit" in light_raw and "unlit" not in light_raw) else 0
        row["Light_Conditions_Darkness - Lights Unlit"] = 1 if "unlit" in light_raw else 0
        row["Light_Conditions_Darkness - No Lighting"] = 1 if ("no_light" in light_raw or "no lighting" in light_raw) else 0
        row["Light_Conditions_Daylight"] = 1 if ("day" in light_raw or "dusk" in light_raw or "dawn" in light_raw) else 0
        row["Light_Conditions_Unknown"] = 0
        if not any([row["Light_Conditions_Darkness - Lights Lit"], row["Light_Conditions_Darkness - Lights Unlit"], row["Light_Conditions_Darkness - No Lighting"], row["Light_Conditions_Daylight"]]):
            row["Light_Conditions_Daylight"] = 1

        # Junction Control
        row["Junction_Control_Authorised Person"] = 1 if "authoris" in junct_ctrl_raw else 0
        row["Junction_Control_Auto Traffic Signal"] = 1 if "signal" in junct_ctrl_raw else 0
        row["Junction_Control_Give Way Or Uncontrolled"] = 1 if "give_way" in junct_ctrl_raw else 0
        row["Junction_Control_Not At Junction Or Within 20 Metres"] = 1 if ("not" in junct_ctrl_raw or "no_junction" in junct_ctrl_raw) else 0
        row["Junction_Control_Stop Sign"] = 1 if "stop" in junct_ctrl_raw else 0
        row["Junction_Control_Unknown"] = 0
        if not any([row["Junction_Control_Authorised Person"], row["Junction_Control_Auto Traffic Signal"], row["Junction_Control_Give Way Or Uncontrolled"], row["Junction_Control_Not At Junction Or Within 20 Metres"], row["Junction_Control_Stop Sign"]]):
            row["Junction_Control_Not At Junction Or Within 20 Metres"] = 1

        # Junction Detail
        row["Junction_Detail_Crossroads"] = 1 if "crossroad" in junct_dtl_raw else 0
        row["Junction_Detail_Mini-Roundabout"] = 1 if "mini" in junct_dtl_raw else 0
        row["Junction_Detail_More Than 4 Arms (Not Roundabout)"] = 1 if "4 arms" in junct_dtl_raw else 0
        row["Junction_Detail_Not At Junction Or Within 20 Metres"] = 1 if ("not" in junct_dtl_raw or "no_junction" in junct_dtl_raw) else 0
        row["Junction_Detail_Other Junction"] = 1 if "other" in junct_dtl_raw else 0
        row["Junction_Detail_Private Drive Or Entrance"] = 1 if "private" in junct_dtl_raw else 0
        row["Junction_Detail_Roundabout"] = 1 if "roundabout" in junct_dtl_raw else 0
        row["Junction_Detail_Slip Road"] = 1 if "slip" in junct_dtl_raw else 0
        row["Junction_Detail_T Or Staggered Junction"] = 1 if "staggered" in junct_dtl_raw or "t_" in junct_dtl_raw else 0
        row["Junction_Detail_Unknown"] = 0
        if not any([row["Junction_Detail_Crossroads"], row["Junction_Detail_Mini-Roundabout"], row["Junction_Detail_More Than 4 Arms (Not Roundabout)"], row["Junction_Detail_Not At Junction Or Within 20 Metres"], row["Junction_Detail_Other Junction"], row["Junction_Detail_Private Drive Or Entrance"], row["Junction_Detail_Roundabout"], row["Junction_Detail_Slip Road"], row["Junction_Detail_T Or Staggered Junction"]]):
            row["Junction_Detail_Not At Junction Or Within 20 Metres"] = 1

        # Day of Week & Weekday (both one-hot columns are present in features.pkl)
        for day_name in ["Friday", "Monday", "Saturday", "Sunday", "Thursday", "Tuesday", "Wednesday"]:
            is_this_day = 1 if day_name.lower() == weekday_name.lower() else 0
            row[f"Day_of_Week_{day_name}"] = is_this_day
            row[f"Weekday_{day_name}"] = is_this_day

        # Weather Conditions
        row["Weather_Conditions_Fine + High Winds"] = 1 if ("fine" in weather_raw and "wind" in weather_raw) else 0
        row["Weather_Conditions_Fine No High Winds"] = 1 if ("fine" in weather_raw and "wind" not in weather_raw) else 0
        row["Weather_Conditions_Fog Or Mist"] = 1 if ("fog" in weather_raw or "mist" in weather_raw) else 0
        row["Weather_Conditions_Other"] = 1 if "other" in weather_raw else 0
        row["Weather_Conditions_Raining + High Winds"] = 1 if ("rain" in weather_raw and "wind" in weather_raw) else 0
        row["Weather_Conditions_Raining No High Winds"] = 1 if ("rain" in weather_raw and "wind" not in weather_raw) else 0
        row["Weather_Conditions_Snowing + High Winds"] = 1 if ("snow" in weather_raw and "wind" in weather_raw) else 0
        row["Weather_Conditions_Snowing No High Winds"] = 1 if ("snow" in weather_raw and "wind" not in weather_raw) else 0
        row["Weather_Conditions_Unknown"] = 0
        if not any([row["Weather_Conditions_Fine + High Winds"], row["Weather_Conditions_Fine No High Winds"], row["Weather_Conditions_Fog Or Mist"], row["Weather_Conditions_Other"], row["Weather_Conditions_Raining + High Winds"], row["Weather_Conditions_Raining No High Winds"], row["Weather_Conditions_Snowing + High Winds"], row["Weather_Conditions_Snowing No High Winds"]]):
            row["Weather_Conditions_Fine No High Winds"] = 1

        return row

