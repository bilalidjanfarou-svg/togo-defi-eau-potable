from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from data_loader import load_all

cantons, points, points_full, sales, pop = load_all()

nb_ouvrages = len(points_full)
nb_cantons = len(cantons)
nb_cantons_sans_ouvrage = (cantons["nb_ouvrages"] == 0).sum()
geojson = json.loads(cantons.to_json())
coso_pts_full = points_full[points_full["source"] == "COSO"]

# ============================================================
# ONGLET 1 : CARTOGRAPHIE
# ============================================================
def build_tab_carte():
    fig_map = px.choropleth_map(
        cantons, geojson=geojson, locations=cantons.index, color="nb_ouvrages",
        hover_name="canton_nom",
        hover_data={"region": True, "total_pop": ":,.0f", "nb_ouvrages": True},
        color_continuous_scale="BuGn", map_style="carto-positron",
        zoom=6.3, center={"lat": 8.6, "lon": 1.0}, opacity=0.75,
        labels={"nb_ouvrages": "Nb ouvrages"},
    )
    coso_pts = points[points["source"] == "COSO"]
    tde_pts = points[points["source"] == "TdE"]
    fig_map.add_trace(go.Scattermap(
        lat=coso_pts.geometry.y, lon=coso_pts.geometry.x, mode="markers",
        marker=dict(size=7, color="#0B3D3A"), name="Ouvrages COSO",
        text=coso_pts["canton_nom"], hovertemplate="<b>COSO</b><br>Canton: %{text}<extra></extra>",
    ))
    fig_map.add_trace(go.Scattermap(
        lat=tde_pts.geometry.y, lon=tde_pts.geometry.x, mode="markers",
        marker=dict(size=7, color="#D4A62A"), name="Ouvrages TdE",
        text=tde_pts["canton_nom"], hovertemplate="<b>TdE</b><br>Canton: %{text}<extra></extra>",
    ))
    fig_map.update_layout(legend=dict(orientation="h", y=1.02, x=0), margin=dict(l=0, r=0, t=30, b=0), height=550)

    couverture = cantons.groupby("region").apply(
        lambda d: round((d["nb_ouvrages"] == 0).mean() * 100, 1)
    ).reset_index(name="pct_sans_ouvrage").sort_values("pct_sans_ouvrage")
    fig_couverture = px.bar(
        couverture, x="pct_sans_ouvrage", y="region", orientation="h", text="pct_sans_ouvrage",
        labels={"pct_sans_ouvrage": "% cantons sans ouvrage", "region": ""},
        color="pct_sans_ouvrage", color_continuous_scale="Reds",
    )
    fig_couverture.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_couverture.update_layout(height=350, coloraxis_showscale=False, xaxis_range=[0, 110])

    return html.Div([
        dcc.Graph(figure=fig_map, className="mb-3"),
        dcc.Graph(figure=fig_couverture),
    ])

# ============================================================
# ONGLET 2 : FONCTIONNALITE
# ============================================================
def build_tab_fonctionnalite():
    risque_par_region = pd.crosstab(coso_pts_full["region"], coso_pts_full["proxy_risque_panne"], normalize="index") * 100
    risque_par_region = risque_par_region.reset_index().melt(id_vars="region", var_name="niveau", value_name="pct")
    ordre_niveaux = ["Faible risque", "Risque modéré", "Risque élevé"]
    couleurs_risque = {"Faible risque": "#1E8A7E", "Risque modéré": "#D4A62A", "Risque élevé": "#C0392B"}
    fig_risque = px.bar(
        risque_par_region, x="region", y="pct", color="niveau",
        category_orders={"niveau": ordre_niveaux}, color_discrete_map=couleurs_risque,
        labels={"pct": "% d'ouvrages COSO", "region": "", "niveau": ""},
    )
    fig_risque.update_layout(height=400, legend=dict(orientation="h", y=-0.15))

    maintenance = coso_pts_full["maintenance_manquante"].map({0: "Plan existant", 1: "Aucun plan"})
    maintenance = maintenance.fillna("Non renseigne")
    fig_maintenance = px.pie(
        maintenance.value_counts().reset_index(), names="maintenance_manquante", values="count",
        color="maintenance_manquante",
        color_discrete_map={"Plan existant": "#1E8A7E", "Aucun plan": "#C0392B", "Non renseigne": "#9AA6A4"},
        hole=0.5,
    )
    fig_maintenance.update_layout(height=400)

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_risque), md=7),
            dbc.Col(dcc.Graph(figure=fig_maintenance), md=5),
        ]),
    ])

# ============================================================
# ONGLET 3 : DEMOGRAPHIE
# ============================================================
def build_tab_demographie():
    fig_demo = px.scatter(
        cantons, x="total_pop", y="nb_ouvrages", color="region", hover_name="canton_nom",
        labels={"total_pop": "Population du canton", "nb_ouvrages": "Nb ouvrages recenses"},
        log_x=True,
    )
    fig_demo.update_layout(height=550, legend=dict(orientation="h", y=-0.15))
    return html.Div([dcc.Graph(figure=fig_demo)])

# ============================================================
# ONGLET 4 : INONDATION
# ============================================================
def build_tab_inondation():
    fig_fri = px.choropleth_map(
        cantons, geojson=geojson, locations=cantons.index, color="FRI",
        hover_name="canton_nom", hover_data={"region": True, "FRI": ":.2f", "nb_ouvrages": True},
        color_continuous_scale="YlOrRd", map_style="carto-positron",
        zoom=6.3, center={"lat": 8.6, "lon": 1.0}, opacity=0.8,
    )
    fig_fri.add_trace(go.Scattermap(
        lat=points.geometry.y, lon=points.geometry.x, mode="markers",
        marker=dict(size=6, color="#0B3D3A"), name="Ouvrages", hovertemplate="Ouvrage<extra></extra>",
    ))
    fig_fri.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=600, legend=dict(orientation="h", y=1.02, x=0))
    return html.Div([dcc.Graph(figure=fig_fri)])

# ============================================================
# LAYOUT PRINCIPAL
# ============================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = html.Div([
    html.H1("Diagnostic Eau Potable - Togo", className="m-3"),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H2(str(nb_ouvrages)), html.P("Ouvrages recenses")]))),
        dbc.Col(dbc.Card(dbc.CardBody([html.H2(f"{nb_cantons_sans_ouvrage}/{nb_cantons}"), html.P("Cantons sans ouvrage")]))),
    ], className="m-3"),
    dcc.Tabs(id="tabs", value="tab-carte", children=[
        dcc.Tab(label="Cartographie", value="tab-carte"),
        dcc.Tab(label="Fonctionnalite", value="tab-func"),
        dcc.Tab(label="Demographie", value="tab-demo"),
        dcc.Tab(label="Inondation", value="tab-flood"),
    ]),
    html.Div(id="tab-content", className="m-3"),
])

@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "tab-carte":
        return build_tab_carte()
    elif tab == "tab-func":
        return build_tab_fonctionnalite()
    elif tab == "tab-demo":
        return build_tab_demographie()
    elif tab == "tab-flood":
        return build_tab_inondation()
    return html.Div()

if __name__ == "__main__":
    app.run(debug=True, port=8050)