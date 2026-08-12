import geopandas as gpd
import unicodedata

def normaliser(texte):
    """Retire les accents et met en majuscules."""
    if texte is None:
        return None
    texte = str(texte).strip().upper()
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return texte

coso = gpd.read_file("data/raw/projet-coso-eau.geojson")
cantons = gpd.read_file("data/raw/fri-cantons.gpkg")

def extraire_canton(h):
    parts = [p.strip() for p in str(h).split(">")]
    if len(parts) >= 5:
        return parts[1]
    elif len(parts) == 4:
        return parts[0]
    return None

coso["canton_extrait"] = coso["hierarchy"].apply(extraire_canton)
coso["canton_norm"] = coso["canton_extrait"].apply(normaliser)
cantons["canton_norm"] = cantons["canton_nom"].apply(normaliser)

cantons_fri_norm = set(cantons["canton_norm"])
cantons_coso_norm = set(coso["canton_norm"].dropna())

non_matches = cantons_coso_norm - cantons_fri_norm
print(f"Cantons COSO (normalisés) : {len(cantons_coso_norm)}")
print(f"Toujours non trouvés après normalisation : {len(non_matches)}")
print(non_matches)
print()

# Pour les cas restants, on regarde tous les cantons FRI de la même préfecture
coso["prefecture_extraite"] = coso["hierarchy"].apply(lambda h: str(h).split(">")[2].strip() if len(str(h).split(">")) >= 5 else None)

for c in non_matches:
    mask = coso["canton_norm"] == c
    prefs = coso.loc[mask, "prefecture_extraite"].unique()
    print(f"--- Canton COSO '{c}' (préfecture: {prefs}) ---")
    for pref in prefs:
        pref_norm = normaliser(pref)
        cantons_meme_pref = cantons[cantons["prefecture"].apply(normaliser) == pref_norm]["canton_nom"].tolist()
        print(f"  Cantons FRI dans la préfecture '{pref}' : {cantons_meme_pref}")
    print()