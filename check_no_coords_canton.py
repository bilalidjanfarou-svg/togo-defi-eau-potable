import geopandas as gpd

coso = gpd.read_file("data/raw/projet-coso-eau.geojson")

def extraire_canton(h):
    parts = [p.strip() for p in str(h).split(">")]
    if len(parts) >= 5:
        return parts[1]
    elif len(parts) == 4:
        return parts[0]
    return None

coso["canton_extrait"] = coso["hierarchy"].apply(extraire_canton)

sans_coords = coso[
    coso["latitude"].isna() |
    ((coso["latitude"] == 0) & (coso["longitude"] == 0))
]

print(f"Ouvrages sans coordonnées valides : {len(sans_coords)}")
print("Dont canton_extrait manquant :", sans_coords["canton_extrait"].isna().sum())
print()
print("=== Répartition par région (dernier niveau hierarchy) ===")
sans_coords_copy = sans_coords.copy()
sans_coords_copy["region"] = sans_coords_copy["hierarchy"].apply(lambda h: str(h).split(">")[-1].strip())
print(sans_coords_copy["region"].value_counts())