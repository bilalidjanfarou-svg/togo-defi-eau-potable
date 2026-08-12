import geopandas as gpd

gdf = gpd.read_file("data/raw/projet-coso-eau.geojson")

print("=== Statut de réception ===")
print(gdf["current_status_of_the_site"].value_counts(dropna=False))
print()

print("=== Existence d'un plan de maintenance ===")
print(gdf["existence_of_maintenance_plan"].value_counts(dropna=False))
print()

print("=== Type d'ouvrage ===")
print(gdf["type"].value_counts(dropna=False))
print()

print("=== Champ canton ===")
print(gdf["canton"].isna().sum(), "valeurs manquantes sur", len(gdf))
print(gdf["canton"].head(10).tolist())
print()

print("=== Coordonnées à zéro (0,0) ===")
zero = gdf[(gdf["latitude"] == 0) & (gdf["longitude"] == 0)]
print(len(zero), "lignes avec latitude=0 et longitude=0")
print()

print("=== infrastructure_deleted ===")
print(gdf["infrastructure_deleted"].value_counts(dropna=False))