import pandas as pd
from data_loader import load_all

cantons, points, points_full, sales, pop = load_all()

coso = points_full[points_full["source"] == "COSO"]
print("=== Repartition proxy_risque_panne (COSO) ===")
print(coso["proxy_risque_panne"].value_counts())
print()
print("=== Par region ===")
print(pd.crosstab(coso["region"], coso["proxy_risque_panne"]))