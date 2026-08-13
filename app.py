from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import json
from data_loader import load_all
import plotly.graph_objects as go
import pandas as pd


cantons, points, points_full, sales, pop = load_all()

nb_ouvrages = len(points_full)
nb_cantons = len(cantons)
nb_cantons_sans_ouvrage = (cantons["nb_ouvrages"] == 0).sum()

# --- Carte choroplethe : nombre d'ouvrages par canton ---
geojson = json.loads(cantons.to_json())

fig_map = px.choropleth_map(
    cantons,
    geojson=geojson,
    locations=cantons.index,
    color="nb_ouvrages",
    hover_name="canton_nom",
    hover_data={"region": True, "total_pop": ":,.0f", "nb_ouvrages": True},
    color_continuous_scale="BuGn",
    map_style="carto-positron",
    zoom=6.3,
    center={"lat": 8.6, "lon": 1.0},
    opacity=0.75,
    labels={"nb_ouvrages": "Nb ouvrages"},
)

# --- Points COSO et TdE superposes ---
coso_pts = points[points["source"] == "COSO"]
tde_pts = points[points["source"] == "TdE"]

fig_map.add_trace(go.Scattermap(
    lat=coso_pts.geometry.y, lon=coso_pts.geometry.x,
    mode="markers",
    marker=dict(size=7, color="#0B3D3A"),
    name="Ouvrages COSO",
    text=coso_pts["canton_nom"],
    hovertemplate="<b>COSO</b><br>Canton: %{text}<extra></extra>",
))

fig_map.add_trace(go.Scattermap(
    lat=tde_pts.geometry.y, lon=tde_pts.geometry.x,
    mode="markers",
    marker=dict(size=7, color="#D4A62A"),
    name="Ouvrages TdE",
    text=tde_pts["canton_nom"],
    hovertemplate="<b>TdE</b><br>Canton: %{text}<extra></extra>",
))

fig_map.update_layout(legend=dict(orientation="h", y=1.02, x=0))

fig_map.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=600)

# --- Graphique : % de cantons sans ouvrage par region ---
couverture = cantons.groupby("region").apply(
    lambda d: round((d["nb_ouvrages"] == 0).mean() * 100, 1)
).reset_index(name="pct_sans_ouvrage").sort_values("pct_sans_ouvrage")

fig_couverture = px.bar(
    couverture, x="pct_sans_ouvrage", y="region", orientation="h",
    text="pct_sans_ouvrage",
    labels={"pct_sans_ouvrage": "% cantons sans ouvrage", "region": ""},
    color="pct_sans_ouvrage", color_continuous_scale="Reds",
)
fig_couverture.update_traces(texttemplate="%{text}%", textposition="outside")
fig_couverture.update_layout(height=350, coloraxis_showscale=False, xaxis_range=[0, 110])

# --- Graphique : proxy de risque de panne par region (ouvrages COSO) ---
coso_pts_full = points_full[points_full["source"] == "COSO"]

risque_par_region = pd.crosstab(coso_pts_full["region"], coso_pts_full["proxy_risque_panne"], normalize="index") * 100
risque_par_region = risque_par_region.reset_index().melt(id_vars="region", var_name="niveau", value_name="pct")

ordre_niveaux = ["Faible risque", "Risque modéré", "Risque élevé"]
couleurs_risque = {"Faible risque": "#1E8A7E", "Risque modéré": "#D4A62A", "Risque élevé": "#C0392B"}

fig_risque = px.bar(
    risque_par_region, x="region", y="pct", color="niveau",
    category_orders={"niveau": ordre_niveaux},
    color_discrete_map=couleurs_risque,
    labels={"pct": "% d'ouvrages COSO", "region": "", "niveau": ""},
)
fig_risque.update_layout(height=400, legend=dict(orientation="h", y=-0.15))
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = html.Div([

    dcc.Graph(figure=fig_map, className="m-3"),
    dcc.Graph(figure=fig_couverture, className="m-3"),
    dcc.Graph(figure=fig_risque, className="m-3"),
])


if __name__ == "__main__":
    app.run(debug=True, port=8050)