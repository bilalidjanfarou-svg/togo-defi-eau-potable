import geopandas as gpd
import pandas as pd

print("=== 1. COSO (geojson) ===")
gdf = gpd.read_file("data/raw/projet-coso-eau.geojson")
print("Nombre de lignes :", len(gdf))
print("Colonnes :", gdf.columns.tolist())
print(gdf.head(3))
print()

print("=== 2. TdE (chateaux d'eau / forages) ===")
tde = pd.read_csv("data/raw/file-chateaux-deau-forages-tde-19-12-2024-18-55-00.csv")
print("Nombre de lignes :", len(tde))
print("Colonnes :", tde.columns.tolist())
print(tde.head(3))
print()

print("=== 3. FRI cantons (gpkg) ===")
cantons = gpd.read_file("data/raw/fri-cantons.gpkg")
print("Nombre de lignes :", len(cantons))
print("Colonnes :", cantons.columns.tolist())
print("CRS :", cantons.crs)
print(cantons.head(3))
print()

print("=== 4. Ventes d'eau ===")
sales = pd.read_csv("data/raw/observationdata-mfcialc.csv")
print("Nombre de lignes :", len(sales))
print("Colonnes :", sales.columns.tolist())
print(sales.head(5))
print()

print("=== 5. Population RGPH ===")
pop = pd.read_csv("data/raw/observationdata-sapxctg.csv")
print("Nombre de lignes :", len(pop))
print("Colonnes :", pop.columns.tolist())
print(pop.head(5))