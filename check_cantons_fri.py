import geopandas as gpd

cantons = gpd.read_file("data/raw/fri-cantons.gpkg")

print("=== Valeurs manquantes par colonne ===")
print(cantons[["region_nom", "prefecture", "canton_nom", "total_pop", "FRI"]].isna().sum())
print()

print("=== Doublons de canton_nom ===")
doublons = cantons["canton_nom"].duplicated().sum()
print(f"{doublons} noms de canton dupliqués sur {len(cantons)}")
if doublons > 0:
    noms_dupliques = cantons[cantons["canton_nom"].duplicated(keep=False)].sort_values("canton_nom")
    print(noms_dupliques[["region_nom", "prefecture", "canton_nom"]].head(20))
print()

print("=== Statistiques FRI et population ===")
print(cantons[["FRI", "total_pop"]].describe())
print()

print("=== Régions présentes ===")
print(cantons["region_nom"].value_counts())