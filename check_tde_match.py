import geopandas as gpd
import pandas as pd
from shapely import wkt

tde = pd.read_csv("data/raw/file-chateaux-deau-forages-tde-19-12-2024-18-55-00.csv")
cantons = gpd.read_file("data/raw/fri-cantons.gpkg")

print("=== Coordonnées TdE valides ? ===")
print(tde["geometry"].isna().sum(), "géométries manquantes sur", len(tde))
print()

# Conversion du texte WKT ("POINT (...)") en objets géométriques
tde["geometry"] = tde["geometry"].apply(wkt.loads)
tde_gdf = gpd.GeoDataFrame(tde, geometry="geometry", crs="EPSG:4326")

cantons_wgs84 = cantons.to_crs(epsg=4326)

resultat = gpd.sjoin(
    tde_gdf,
    cantons_wgs84[["canton_nom", "region_nom", "geometry"]],
    how="left",
    predicate="within"
)
print("=== Jointure spatiale TdE -> cantons ===")
print("Résolus :", resultat["canton_nom"].notna().sum(), "sur", len(resultat))
print("Non résolus :", resultat["canton_nom"].isna().sum())
print()

print("=== Comparaison canton déclaré vs canton spatial (échantillon) ===")
print(resultat[["canton_nom_bdd", "canton_nom", "region_nom_bdd", "region_nom"]].head(15))