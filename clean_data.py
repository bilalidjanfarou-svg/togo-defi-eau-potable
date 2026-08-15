# -*- coding: utf-8 -*-
"""
clean_data.py — Défi 1 Environnement (Togo AI Lab)
Nettoyage et fusion des données pour le diagnostic d'accès à l'eau potable.
"""
import unicodedata
import pandas as pd
import geopandas as gpd
from shapely import wkt

RAW = "data/raw"
CLEAN = "data/clean"


def normaliser(texte):
    """Retire les accents et met en majuscules pour comparer des noms de lieux."""
    if texte is None or pd.isna(texte):
        return None
    texte = str(texte).strip().upper()
    texte = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in texte if not unicodedata.combining(c))


def extraire_hierarchy(h, niveau):
    """Extrait un niveau de la chaîne hierarchy (LOCALITE > CANTON > COMMUNE > PREFECTURE > REGION)."""
    parts = [p.strip() for p in str(h).split(">")]
    if len(parts) >= 5:
        idx_map = {"canton": 1, "region": 4}
    elif len(parts) == 4:
        idx_map = {"canton": 0, "region": 3}
    else:
        return None
    idx = idx_map.get(niveau)
    return parts[idx] if idx is not None and idx < len(parts) else None


# ----------------------------------------------------------------------------
# 1. CANTONS + INDICE DE RISQUE D'INONDATION (FRI) — base de référence
# ----------------------------------------------------------------------------
cantons = gpd.read_file(f"{RAW}/fri-cantons.gpkg").to_crs(epsg=4326)
cantons = cantons.rename(columns={"region_nom": "region", "prefecture": "prefecture_nom"})
cantons["canton_norm"] = cantons["canton_nom"].apply(normaliser)
cantons["region_norm"] = cantons["region"].apply(normaliser)
cantons["fri_classe"] = pd.qcut(cantons["FRI"], q=[0, 0.5, 0.8, 1.0], labels=["Faible", "Modéré", "Élevé"])

print(f"Cantons chargés : {len(cantons)}")

# ----------------------------------------------------------------------------
# 2. OUVRAGES COSO
# ----------------------------------------------------------------------------
coso = gpd.read_file(f"{RAW}/projet-coso-eau.geojson")
coso["canton_hier"] = coso["hierarchy"].apply(lambda h: extraire_hierarchy(h, "canton"))
coso["region_hier"] = coso["hierarchy"].apply(lambda h: extraire_hierarchy(h, "region"))
coso["canton_norm"] = coso["canton_hier"].apply(normaliser)
coso["region_norm"] = coso["region_hier"].apply(normaliser)

coso["coord_invalide"] = coso["latitude"].isna() | ((coso["latitude"] == 0) & (coso["longitude"] == 0))
print(f"COSO — coordonnées valides : {(~coso['coord_invalide']).sum()} / invalides : {coso['coord_invalide'].sum()}")

# --- 2a. Ouvrages à coordonnées valides : jointure spatiale (+ proximité pour les cas limites) ---
coso_valides = coso[~coso["coord_invalide"]].copy()
resultat_spatial = gpd.sjoin(
    coso_valides,
    cantons[["canton_nom", "region", "prefecture_nom", "FRI", "fri_classe", "total_pop", "geometry"]],
    how="left", predicate="within",
).drop(columns=["index_right"])

non_resolus_mask = resultat_spatial["canton_nom"].isna()
if non_resolus_mask.any():
    resolus = resultat_spatial[~non_resolus_mask]
    a_corriger = resultat_spatial[non_resolus_mask].drop(
        columns=["canton_nom", "region", "prefecture_nom", "FRI", "fri_classe", "total_pop"]
    )
    a_corriger_proj = a_corriger.to_crs(epsg=32631)
    cantons_proj = cantons.to_crs(epsg=32631)
    plus_proche = gpd.sjoin_nearest(
        a_corriger_proj,
        cantons_proj[["canton_nom", "region", "prefecture_nom", "FRI", "fri_classe", "total_pop", "geometry"]],
        how="left",
    ).drop(columns=["index_right"], errors="ignore").to_crs(epsg=4326)
    resultat_spatial = pd.concat([resolus, plus_proche], ignore_index=True)
    print(f"  -> {len(plus_proche)} cas limites résolus par proximité")

# --- 2b. Ouvrages à coordonnées invalides : jointure par (canton, région) normalisés ---
coso_invalides = coso[coso["coord_invalide"]].copy()
coso_invalides_joint = coso_invalides.merge(
    cantons[["canton_norm", "region_norm", "canton_nom", "region", "prefecture_nom", "FRI", "fri_classe", "total_pop"]],
    on=["canton_norm", "region_norm"], how="left",
)
n_non_trouves = coso_invalides_joint["canton_nom"].isna().sum()
print(f"COSO sans coordonnées — rattachés par nom : {len(coso_invalides_joint) - n_non_trouves} / non trouvés : {n_non_trouves}")

# --- 2c. Repli région seule pour les cantons introuvables dans le référentiel FRI ---
mask_non_trouve = coso_invalides_joint["canton_nom"].isna()
if mask_non_trouve.any():
    moyennes_region = cantons.groupby("region_norm").agg(
        FRI=("FRI", "mean"), total_pop=("total_pop", "mean")
    ).reset_index()
    a_completer = coso_invalides_joint[mask_non_trouve].drop(columns=["region", "FRI", "total_pop"])
    a_completer = a_completer.merge(moyennes_region, on="region_norm", how="left")
    a_completer["region"] = a_completer["region_norm"].map(
        cantons.drop_duplicates("region_norm").set_index("region_norm")["region"]
    )
    a_completer["canton_nom"] = None
    a_completer["fri_classe"] = None
    a_completer["prefecture_nom"] = None
    coso_invalides_joint = pd.concat([coso_invalides_joint[~mask_non_trouve], a_completer], ignore_index=True)
    print(f"  -> {mask_non_trouve.sum()} ouvrages repliés au niveau région (canton introuvable dans FRI)")

# --- 2d. Fusion des deux sous-ensembles COSO (coordonnées valides + invalides) ---
coso_invalides_joint["geometry"] = None
coso_final = pd.concat([
    resultat_spatial.drop(columns=["canton_hier", "region_hier"], errors="ignore"),
    coso_invalides_joint.drop(columns=["canton_hier", "region_hier"], errors="ignore"),
], ignore_index=True)
coso_final["source"] = "COSO"

# ----------------------------------------------------------------------------
# 3. OUVRAGES TdE
# ----------------------------------------------------------------------------
tde = pd.read_csv(f"{RAW}/file-chateaux-deau-forages-tde-19-12-2024-18-55-00.csv")
tde["geometry"] = tde["geometry"].apply(wkt.loads)
tde_gdf = gpd.GeoDataFrame(tde, geometry="geometry", crs="EPSG:4326")

tde_final = gpd.sjoin(
    tde_gdf,
    cantons[["canton_nom", "region", "prefecture_nom", "FRI", "fri_classe", "total_pop", "geometry"]],
    how="left", predicate="within",
).drop(columns=["index_right"])
tde_final["source"] = "TdE"
tde_final["coord_invalide"] = False
print(f"TdE — résolus : {tde_final['canton_nom'].notna().sum()} / {len(tde_final)}")

# ----------------------------------------------------------------------------
# 4. PROXY DE FONCTIONNALITÉ (statut de réception + plan de maintenance)
# ----------------------------------------------------------------------------
def statut_score(s):
    if s == "Réception définitive":
        return 0
    elif s in ("Réception provisoire", "Réception technique", "Achevé"):
        return 1
    return None

coso_final["score_statut"] = coso_final["current_status_of_the_site"].apply(statut_score)
coso_final["maintenance_manquante"] = coso_final["existence_of_maintenance_plan"].apply(
    lambda x: 0 if x is True or str(x).lower() == "true" else (1 if pd.notna(x) else None)
)

def proxy_risque(row):
    s = row.get("score_statut") or 0
    m = row.get("maintenance_manquante") or 0
    total = s + m
    if total == 0:
        return "Faible risque"
    elif total == 1:
        return "Risque modéré"
    return "Risque élevé"

coso_final["proxy_risque_panne"] = coso_final.apply(proxy_risque, axis=1)
tde_final["proxy_risque_panne"] = "Non évalué (donnée indisponible)"

# ----------------------------------------------------------------------------
# 5. FUSION FINALE DES OUVRAGES
# ----------------------------------------------------------------------------
colonnes_communes = ["source", "canton_nom", "region", "prefecture_nom", "FRI", "fri_classe",
                     "total_pop", "proxy_risque_panne", "coord_invalide", "geometry"]
colonnes_coso_only = ["score_statut", "maintenance_manquante"]

points_final = pd.concat([
    coso_final[colonnes_communes + colonnes_coso_only + [c for c in ["location_name", "latitude", "longitude"] if c in coso_final.columns]],
    tde_final[colonnes_communes + [c for c in ["forage_chateau_nom"] if c in tde_final.columns]],
], ignore_index=True)

import os
os.makedirs(CLEAN, exist_ok=True)

points_mappable = gpd.GeoDataFrame(points_final[~points_final["coord_invalide"] & points_final["geometry"].notna()],
                                    geometry="geometry", crs="EPSG:4326")
points_mappable.to_file(f"{CLEAN}/water_points.geojson", driver="GeoJSON")
pd.DataFrame(points_final.drop(columns="geometry")).to_csv(f"{CLEAN}/water_points_full.csv", index=False)

print()
print(f"=== TOTAL OUVRAGES : {len(points_final)} (COSO: {len(coso_final)}, TdE: {len(tde_final)}) ===")
print(f"=== Cartographiables : {len(points_mappable)} ===")

# ----------------------------------------------------------------------------
# 6. AGRÉGATION PAR CANTON
# ----------------------------------------------------------------------------
agg = points_final.groupby("canton_nom").agg(
    nb_ouvrages=("source", "count"),
    nb_risque_eleve=("proxy_risque_panne", lambda s: (s == "Risque élevé").sum()),
).reset_index()

cantons_enriched = cantons.merge(agg, on="canton_nom", how="left")
cantons_enriched["nb_ouvrages"] = cantons_enriched["nb_ouvrages"].fillna(0)
cantons_enriched["nb_risque_eleve"] = cantons_enriched["nb_risque_eleve"].fillna(0)
cantons_enriched.to_file(f"{CLEAN}/cantons.geojson", driver="GeoJSON")

print()
print(f"=== CANTONS SANS OUVRAGE : {(cantons_enriched['nb_ouvrages'] == 0).sum()} / {len(cantons_enriched)} ===")

# ----------------------------------------------------------------------------
# 7. VENTES D'EAU PAR CATÉGORIE D'ABONNÉ
# ----------------------------------------------------------------------------
sales = pd.read_csv(f"{RAW}/observationdata-mfcialc.csv")
sales.columns = ["categorie", "unite", "annee", "valeur_m3"]
sales["annee"] = sales["annee"].astype(int)
sales["valeur_m3"] = pd.to_numeric(sales["valeur_m3"], errors="coerce")
sales.to_csv(f"{CLEAN}/water_sales.csv", index=False)
print(f"=== VENTES D'EAU : {len(sales)} lignes, années {sales['annee'].min()}-{sales['annee'].max()} ===")

# ----------------------------------------------------------------------------
# 8. POPULATION RGPH 2010
# ----------------------------------------------------------------------------
pop = pd.read_csv(f"{RAW}/observationdata-sapxctg.csv")
pop.columns = ["localite", "unite", "annee", "population"]
pop["population"] = pd.to_numeric(pop["population"], errors="coerce")
pop.to_csv(f"{CLEAN}/population_rgph.csv", index=False)
print(f"=== POPULATION RGPH : {len(pop)} localités ===")