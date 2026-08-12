import geopandas as gpd

gdf = gpd.read_file("data/raw/projet-coso-eau.geojson")

print("=== Exemples de hierarchy ===")
for h in gdf["hierarchy"].head(10):
    print(h)
print()

print("=== Valeurs manquantes dans hierarchy ===")
print(gdf["hierarchy"].isna().sum(), "sur", len(gdf))
print()

print("=== Nombre de niveaux (separateur '>') ===")
niveaux = gdf["hierarchy"].dropna().apply(lambda h: len(h.split(">")))
print(niveaux.value_counts())