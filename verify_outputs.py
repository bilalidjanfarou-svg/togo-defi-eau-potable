import geopandas as gpd
import pandas as pd

print("=== water_points.geojson ===")
pts = gpd.read_file("data/clean/water_points.geojson")
print(pts[["source", "canton_nom", "proxy_risque_panne"]].head(5))
print("Lignes :", len(pts))
print()

print("=== cantons.geojson ===")
cantons = gpd.read_file("data/clean/cantons.geojson")
print(cantons[["region", "canton_nom", "nb_ouvrages", "total_pop", "FRI"]].sort_values("nb_ouvrages", ascending=False).head(5))
print()

print("=== water_sales.csv ===")
print(pd.read_csv("data/clean/water_sales.csv").head(3))
print()

print("=== population_rgph.csv ===")
print(pd.read_csv("data/clean/population_rgph.csv").head(3))