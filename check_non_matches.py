import geopandas as gpd
import difflib

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

cantons_fri_list = cantons["canton_nom"].str.strip().str.upper().unique().tolist()
cantons_coso = set(coso["canton_extrait"].dropna().str.strip().str.upper())
non_matches = cantons_coso - set(cantons_fri_list)

print("=== Suggestions de correspondance (les plus proches) ===")
for c in sorted(non_matches):
    proches = difflib.get_close_matches(c, cantons_fri_list, n=3, cutoff=0.5)
    nb_ouvrages = (coso["canton_extrait"].str.strip().str.upper() == c).sum()
    print(f"{c}  ({nb_ouvrages} ouvrages)  -->  {proches}")

print()
print("=== Régions concernées par ces cantons non trouvés ===")
coso["region_extraite"] = coso["hierarchy"].apply(lambda h: str(h).split(">")[-1].strip())
mask = coso["canton_extrait"].str.strip().str.upper().isin(non_matches)
print(coso.loc[mask, "region_extraite"].value_counts())