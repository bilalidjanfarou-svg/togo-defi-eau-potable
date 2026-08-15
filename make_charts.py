import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from data_loader import load_all

cantons, points, points_full, sales, pop = load_all()

TEAL_DARK = "#0B3D3A"
TEAL = "#12645C"
TEAL_LIGHT = "#1E8A7E"
GOLD = "#D4A62A"
RED = "#C0392B"
GREY = "#9AA6A4"

os.makedirs("report_assets", exist_ok=True)

def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"report_assets/{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("Sauvegarde :", name)

# 1. Carte des ouvrages
fig, ax = plt.subplots(figsize=(9, 9))
cantons.plot(column="nb_ouvrages", ax=ax, cmap="BuGn", edgecolor="white", linewidth=0.3,
             legend=True, legend_kwds={"label": "Nb ouvrages par canton", "shrink": 0.6})
coso = points[points["source"] == "COSO"]
tde = points[points["source"] == "TdE"]
ax.scatter(coso.geometry.x, coso.geometry.y, s=14, color=TEAL_DARK, label="Ouvrages COSO", zorder=5)
ax.scatter(tde.geometry.x, tde.geometry.y, s=14, color=GOLD, label="Ouvrages TdE", zorder=5)
ax.set_axis_off()
ax.legend(loc="lower left", frameon=False)
ax.set_title("Repartition spatiale des ouvrages hydrauliques", fontsize=15, fontweight="bold")
save(fig, "01_carte_ouvrages")

# 2. Couverture par region
couverture = cantons.groupby("region").apply(
    lambda d: round((d["nb_ouvrages"] == 0).mean() * 100, 1)
).reset_index(name="pct").sort_values("pct")
fig, ax = plt.subplots(figsize=(9, 5))
colors = [TEAL_LIGHT if v < 80 else RED for v in couverture["pct"]]
bars = ax.barh(couverture["region"], couverture["pct"], color=colors)
for b, v in zip(bars, couverture["pct"]):
    ax.text(v + 1.5, b.get_y() + b.get_height()/2, f"{v}%", va="center", fontweight="bold")
ax.set_xlim(0, 112)
ax.set_xlabel("% de cantons sans aucun ouvrage recense")
ax.set_title("Couverture par region", fontsize=15, fontweight="bold")
save(fig, "02_couverture_region")

# 3. Proxy de risque par region (COSO)
coso_full = points_full[points_full["source"] == "COSO"]
order = ["Faible risque", "Risque modéré", "Risque élevé"]
colors_risk = {"Faible risque": TEAL_LIGHT, "Risque modéré": GOLD, "Risque élevé": RED}
ct = pd.crosstab(coso_full["region"], coso_full["proxy_risque_panne"], normalize="index") * 100
ct = ct.reindex(columns=order).fillna(0)
fig, ax = plt.subplots(figsize=(9, 5.5))
bottom = np.zeros(len(ct))
for cat in order:
    ax.bar(ct.index, ct[cat], bottom=bottom, label=cat, color=colors_risk[cat])
    bottom += ct[cat].values
ax.set_ylabel("% d'ouvrages COSO")
ax.set_title("Proxy de risque de panne par region", fontsize=15, fontweight="bold")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
save(fig, "03_risque_region")

# 4. Plan de maintenance (donut)
maint = coso_full["maintenance_manquante"].map({0: "Plan existant", 1: "Aucun plan"}).fillna("Non renseigne")
vc = maint.value_counts()
colors_m = {"Plan existant": TEAL_LIGHT, "Aucun plan": RED, "Non renseigne": GREY}
fig, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(vc.values, labels=vc.index, autopct="%1.0f%%", startangle=90,
                                   colors=[colors_m[k] for k in vc.index], wedgeprops=dict(width=0.45))
for t in autotexts:
    t.set_color("white"); t.set_fontweight("bold")
ax.set_title("Plan de maintenance declare (ouvrages COSO)", fontsize=14, fontweight="bold")
save(fig, "04_plan_maintenance")

# 5. Population vs nb ouvrages
region_colors = {"Maritime": TEAL_DARK, "Plateaux": TEAL, "Centrale": TEAL_LIGHT, "Kara": GOLD, "Savanes": "#8E6E00"}
fig, ax = plt.subplots(figsize=(9, 6))
for region, color in region_colors.items():
    sub = cantons[cantons["region"] == region]
    ax.scatter(sub["total_pop"], sub["nb_ouvrages"] + 0.08, s=40, color=color, alpha=0.75, label=region)
ax.set_xscale("log")
ax.set_xlabel("Population du canton (echelle log)")
ax.set_ylabel("Nb ouvrages recenses")
ax.set_title("Pression demographique vs infrastructure existante", fontsize=15, fontweight="bold")
ax.legend(loc="upper left", frameon=False)
save(fig, "05_pop_vs_ouvrages")

# 6. Carte FRI
fig, ax = plt.subplots(figsize=(9, 9))
cantons.plot(column="FRI", ax=ax, cmap="YlOrRd", edgecolor="white", linewidth=0.3,
             legend=True, legend_kwds={"label": "Indice de risque d'inondation (FRI)", "shrink": 0.6})
ax.scatter(points.geometry.x, points.geometry.y, s=12, color=TEAL_DARK, label="Ouvrages", zorder=5)
ax.set_axis_off()
ax.legend(loc="lower left", frameon=False)
ax.set_title("Ouvrages hydrauliques et risque d'inondation", fontsize=15, fontweight="bold")
save(fig, "06_carte_fri")

# 7. Ventes d'eau par categorie (derniere annee)
derniere_annee = sales["annee"].max()
sales_derniere = sales[sales["annee"] == derniere_annee].sort_values("valeur_m3", ascending=True)
fig, ax = plt.subplots(figsize=(9, 6))
bars = ax.barh(sales_derniere["categorie"], sales_derniere["valeur_m3"], color=TEAL)
for b, v in zip(bars, sales_derniere["valeur_m3"]):
    ax.text(v + max(sales_derniere["valeur_m3"]) * 0.01, b.get_y() + b.get_height()/2, f"{v:,.0f}", va="center", fontsize=10)
ax.set_xlabel(f"Ventes en m3 ({derniere_annee})")
ax.set_title(f"Ventes d'eau par categorie d'abonne ({derniere_annee})", fontsize=15, fontweight="bold")
save(fig, "07_ventes_eau")

print("=== TOUTES LES IMAGES GENEREES ===")