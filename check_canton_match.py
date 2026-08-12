import geopandas as gpd

coso = gpd.read_file("data/raw/projet-coso-eau.geojson")
cantons = gpd.read_file("data/raw/fri-cantons.gpkg")

def extraire_canton(h):
    parts = [p.strip() for p in str(h).split(">")]
    if len(parts) >= 5:
        return parts[1]
    elif len(parts) == 4:
        return parts[0]  # cas particulier à vérifier
    return None

coso["canton_extrait"] = coso["hierarchy"].apply(extraire_canton)

print("=== Cantons extraits (premiers 10) ===")
print(coso["canton_extrait"].head(10).tolist())
print()

print("=== La ligne à 4 niveaux ===")
mask = coso["hierarchy"].apply(lambda h: len(str(h).split(">")) == 4)
print(coso.loc[mask, ["hierarchy", "canton_extrait"]])
print()

# Vérifier la correspondance avec les noms de cantons du fichier FRI
cantons_fri = set(cantons["canton_nom"].str.strip().str.upper())
cantons_coso = set(coso["canton_extrait"].dropna().str.strip().str.upper())

matches = cantons_coso & cantons_fri
non_matches = cantons_coso - cantons_fri

print("=== Correspondance cantons ===")
print(f"Cantons COSO : {len(cantons_coso)}")
print(f"Trouvés dans FRI : {len(matches)}")
print(f"Non trouvés : {len(non_matches)}")
print("Exemples non trouvés :", list(non_matches)[:15])