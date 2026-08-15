import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data_loader import load_all

cantons, points, points_full, sales, pop = load_all()

TEAL_DARK = "#0B3D3A"
GOLD = "#D4A62A"

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

import os
os.makedirs("report_assets", exist_ok=True)
fig.savefig("report_assets/01_carte_ouvrages.png", dpi=200, bbox_inches="tight", facecolor="white")
print("Image sauvegardee : report_assets/01_carte_ouvrages.png")