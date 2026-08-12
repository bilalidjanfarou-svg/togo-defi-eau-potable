import json
import geopandas as gpd
import pandas as pd

CLEAN = "data/clean"

def load_all():
    cantons = gpd.read_file(f"{CLEAN}/cantons.geojson")
    points = gpd.read_file(f"{CLEAN}/water_points.geojson")
    points_full = pd.read_csv(f"{CLEAN}/water_points_full.csv")
    sales = pd.read_csv(f"{CLEAN}/water_sales.csv")
    pop = pd.read_csv(f"{CLEAN}/population_rgph.csv")
    return cantons, points, points_full, sales, pop