import unicodedata
import pandas as pd
import geopandas as gpd

def normaliser(texte):
    if texte is None or pd.isna(texte):
        return None
    texte = str(texte).strip().upper()
    texte = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in texte if not unicodedata.combining(c))

def extraire_hierarchy(h, niveau):
    parts = [p.strip() for p in str(h).split(">")]
    if len(parts) >= 5:
        idx_map = {"canton": 1, "region": 4}
    elif len(parts) == 4:
        idx_map = {"canton": 0, "region": 3}
    else:
        return None
    idx = idx_map.get(niveau)
    return parts[idx] if idx is not None and idx < len(parts) else None

cantons = gpd.read_file("data/raw/fri-cantons.gpkg")
cantons["canton_norm"] = cantons["canton_nom"].apply(normaliser)
cantons["region_norm"] = cantons["region_nom"].apply(normaliser)

coso = gpd.read_file("data/raw/projet-coso-eau.geojson")
coso["canton_hier"] = coso["hierarchy"].apply(lambda h: extraire_hierarchy(h, "canton"))
coso["region_hier"] = coso["hierarchy"].apply(lambda h: extraire_hierarchy(h, "region"))
coso["canton_norm"] = coso["canton_hier"].apply(normaliser)
coso["region_norm"] = coso["region_hier"].apply(normaliser)
coso["coord_invalide"] = coso["latitude"].isna() | ((coso["latitude"] == 0) & (coso["longitude"] == 0))

coso_invalides = coso[coso["coord_invalide"]].copy()

paires_cantons = set(zip(cantons["canton_norm"], cantons["region_norm"]))
coso_invalides["trouve"] = coso_invalides.apply(lambda r: (r["canton_norm"], r["region_norm"]) in paires_cantons, axis=1)

non_trouves = coso_invalides[~coso_invalides["trouve"]]
print(f"Non trouvés : {len(non_trouves)}")
print()
print("=== Paires (canton, région) non trouvées ===")
print(non_trouves[["canton_hier", "region_hier"]].drop_duplicates())
print()
print("=== Vérif : ces cantons existent-ils dans FRI sous une autre région ? ===")
for _, row in non_trouves[["canton_norm", "region_norm"]].drop_duplicates().iterrows():
    matchs = cantons[cantons["canton_norm"] == row["canton_norm"]][["canton_nom", "region_nom"]]
    print(f"canton='{row['canton_norm']}' region_attendue='{row['region_norm']}' -> trouvé dans FRI: {matchs.values.tolist()}")