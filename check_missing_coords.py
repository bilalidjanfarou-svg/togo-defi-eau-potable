import geopandas as gpd

coso = gpd.read_file("data/raw/projet-coso-eau.geojson")

print("=== Diagnostic des coordonnées ===")
print("Total lignes :", len(coso))
print("Latitude NaN :", coso["latitude"].isna().sum())
print("Longitude NaN :", coso["longitude"].isna().sum())
print("Latitude=0 ET Longitude=0 :", ((coso["latitude"] == 0) & (coso["longitude"] == 0)).sum())
print("Geometry manquante (None) :", coso["geometry"].isna().sum())
print()

# Répartition croisée
coso["cas"] = "valide"
coso.loc[coso["latitude"].isna() | coso["longitude"].isna(), "cas"] = "NaN (manquant)"
coso.loc[(coso["latitude"] == 0) & (coso["longitude"] == 0), "cas"] = "zéro (0,0)"
print("=== Répartition ===")
print(coso["cas"].value_counts())