import geopandas as gpd
from shapely.geometry import Point

coso = gpd.read_file("data/raw/projet-coso-eau.geojson")
cantons = gpd.read_file("data/raw/fri-cantons.gpkg")

# Reprojeter les cantons en WGS84 (lat/lon) pour correspondre aux coordonnées COSO
cantons_wgs84 = cantons.to_crs(epsg=4326)

# Ne garder que les ouvrages à coordonnées valides (pas 0,0)
coso_valides = coso[~((coso["latitude"] == 0) & (coso["longitude"] == 0))].copy()
print(f"Ouvrages à coordonnées valides : {len(coso_valides)} sur {len(coso)}")

# Jointure spatiale : quel canton contient chaque point ?
resultat = gpd.sjoin(
    coso_valides,
    cantons_wgs84[["canton_nom", "region_nom", "prefecture", "FRI", "total_pop", "geometry"]],
    how="left",
    predicate="within"
)

print()
print("=== Résultat pour les 3 cantons problématiques ===")
def extraire_canton(h):
    parts = [p.strip() for p in str(h).split(">")]
    return parts[1] if len(parts) >= 5 else (parts[0] if len(parts) == 4 else None)

resultat["canton_declare"] = resultat["hierarchy"].apply(extraire_canton)
for c in ["CINKASSE", "GNOAGA", "MAMPROUGOU"]:
    sous = resultat[resultat["canton_declare"] == c]
    print(f"--- {c} ({len(sous)} ouvrages) ---")
    print(sous[["canton_declare", "canton_nom", "region_nom"]].drop_duplicates())
    print()

print("=== Bilan global de la jointure spatiale ===")
print("Non résolus (hors de tout polygone) :", resultat["canton_nom"].isna().sum(), "sur", len(resultat))