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

coso = gpd.read_file("data/raw/projet-coso-eau.geojson")
coso["canton_hier"] = coso["hierarchy"].apply(lambda h: extraire_hierarchy(h, "canton"))
coso["region_hier"] = coso["hierarchy"].apply(lambda h: extraire_hierarchy(h, "region"))
coso["coord_invalide"] = coso["latitude"].isna() | ((coso["latitude"] == 0) & (coso["longitude"] == 0))

coso_invalides = coso[coso["coord_invalide"]]
non_trouves = coso_invalides[coso_invalides["canton_hier"].isin(["CINKASSE", "GNOAGA", "MAMPROUGOU"])]
print(non_trouves["canton_hier"].value_counts())
print("Total :", len(non_trouves))