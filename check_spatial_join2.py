import geopandas as gpd

coso = gpd.read_file("data/raw/projet-coso-eau.geojson")
cantons = gpd.read_file("data/raw/fri-cantons.gpkg").to_crs(epsg=4326)

# On ne garde que les ouvrages à coordonnées réellement valides (ni NaN, ni 0,0)
coso_valides = coso[
    coso["latitude"].notna() &
    coso["longitude"].notna() &
    ~((coso["latitude"] == 0) & (coso["longitude"] == 0))
].copy()
print(f"Ouvrages réellement valides : {len(coso_valides)} sur {len(coso)}")

# Jointure spatiale stricte (point à l'intérieur du polygone)
resultat = gpd.sjoin(
    coso_valides,
    cantons[["canton_nom", "region_nom", "prefecture", "FRI", "total_pop", "geometry"]],
    how="left",
    predicate="within"
)
print("Non résolus après jointure stricte :", resultat["canton_nom"].isna().sum())
print()

# Pour les non résolus, jointure au canton le plus proche (en mètres, CRS projeté)
non_resolus = resultat[resultat["canton_nom"].isna()].drop(
    columns=["canton_nom", "region_nom", "prefecture", "FRI", "total_pop", "index_right"]
)
if len(non_resolus) > 0:
    non_resolus_proj = non_resolus.to_crs(epsg=32631)
    cantons_proj = cantons.to_crs(epsg=32631)
    plus_proche = gpd.sjoin_nearest(
        non_resolus_proj,
        cantons_proj[["canton_nom", "region_nom", "prefecture", "FRI", "total_pop", "geometry"]],
        how="left"
    )
    print("=== Cas limites résolus par proximité ===")
    print(plus_proche[["id", "canton_nom", "region_nom"]])