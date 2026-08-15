from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from data_loader import load_all

cantons, points, points_full, sales, pop = load_all()
TEAL_DARK = "#0B3D3A"
TEAL = "#12645C"
GOLD = "#D4A62A"
BG = "#F5F7F6"

TAB_STYLE = {
    "padding": "12px 6px",
    "fontWeight": "500",
    "color": TEAL_DARK,
    "border": "none",
    "borderBottom": "3px solid #E3E8E6",
}
TAB_SELECTED_STYLE = {
    "padding": "12px 6px",
    "fontWeight": "700",
    "color": TEAL_DARK,
    "border": "none",
    "borderBottom": f"3px solid {GOLD}",
    "backgroundColor": "transparent",
}
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
        color_continuous_scale=[[0, "#E8ECEA"], [0.5, "#1E8A7E"], [1, TEAL_DARK]], map_style="carto-positron",
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
    color_discrete_sequence=[TEAL_DARK, TEAL, "#1E8A7E", GOLD, "#8E6E00"],
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
        color_continuous_scale=[[0, "#EAF4F2"], [0.5, GOLD], [1, "#C0392B"]], map_style="carto-positron",
        zoom=6.3, center={"lat": 8.6, "lon": 1.0}, opacity=0.8,
    )
    fig_fri.add_trace(go.Scattermap(
        lat=points.geometry.y, lon=points.geometry.x, mode="markers",
        marker=dict(size=6, color="#0B3D3A"), name="Ouvrages", hovertemplate="Ouvrage<extra></extra>",
    ))
    fig_fri.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=600, legend=dict(orientation="h", y=1.02, x=0))
    return html.Div([dcc.Graph(figure=fig_fri)])

# ============================================================
# ONGLET 5 : VENTES D'EAU
# ============================================================
def build_tab_ventes():
    fig_ventes = px.line(
    sales, x="annee", y="valeur_m3", color="categorie",
    labels={"annee": "Annee", "valeur_m3": "Ventes (m3)", "categorie": "Categorie"},
    markers=True,
    color_discrete_sequence=px.colors.qualitative.Prism,
)
    fig_ventes.update_layout(height=500, legend=dict(orientation="h", y=-0.2))

    derniere_annee = sales["annee"].max()
    sales_derniere = sales[sales["annee"] == derniere_annee].sort_values("valeur_m3", ascending=True)
    fig_derniere = px.bar(
        sales_derniere, x="valeur_m3", y="categorie", orientation="h",
        labels={"valeur_m3": f"Ventes m3 ({derniere_annee})", "categorie": ""},
        color="valeur_m3", color_continuous_scale="Teal",
    )
    fig_derniere.update_layout(height=500, coloraxis_showscale=False)

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_ventes), md=6),
            dbc.Col(dcc.Graph(figure=fig_derniere), md=6),
        ]),
    ])

# ============================================================
# ONGLET 6 : RECOMMANDATIONS
# ============================================================
def carte_recommandation(titre, priorite, couleur, items):
    return dbc.Card(dbc.CardBody([
        dbc.Badge(priorite, style={"backgroundColor": couleur, "marginBottom": "8px"}),
        html.H5(titre, className="mt-2"),
        html.Ul([html.Li(item) for item in items]),
    ]), className="h-100")

def build_tab_recommandations():
    return html.Div([
        dbc.Row([
            dbc.Col(carte_recommandation(
                "Combler le vide de couverture", "PRIORITE 1", "#C0392B",
                [
                    "Plateaux, Kara et Centrale sont quasi non couverts par les donnees COSO/TdE",
                    "Verifier sur le terrain avant tout nouveau forage (ouvrages non recenses possibles)",
                    "Prioriser les cantons a forte population et zero ouvrage recense",
                ]
            ), md=6, className="mb-3"),
            dbc.Col(carte_recommandation(
                "Securiser la maintenance existante", "PRIORITE 1", "#C0392B",
                [
                    "Une part importante des ouvrages COSO n'a pas de plan de maintenance declare",
                    "Exiger un plan formalise avant reception definitive",
                    "Creer un registre de suivi post-reception",
                ]
            ), md=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(carte_recommandation(
                "Proteger les ouvrages en zone inondable", "PRIORITE 2", "#D4A62A",
                [
                    "Plusieurs ouvrages se situent dans des cantons a risque d'inondation eleve (FRI)",
                    "Integrer le FRI comme critere de choix d'implantation des futurs forages",
                    "Auditer en priorite les ouvrages en zone a risque eleve",
                ]
            ), md=6, className="mb-3"),
            dbc.Col(carte_recommandation(
                "Fiabiliser la donnee elle-meme", "PRIORITE 2", "#D4A62A",
                [
                    "Une partie des ouvrages COSO a des coordonnees invalides a la source",
                    "Aucun statut operationnel reel (panne/abandon) n'est disponible : a instaurer",
                    "Georeferencement obligatoire a la reception de tout ouvrage",
                ]
            ), md=6, className="mb-3"),
        ]),
    ])
# ============================================================
# LAYOUT PRINCIPAL
# ============================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = html.Div([
    html.Div([
        html.H1("Diagnostic de l'acces a l'eau potable au Togo",
                style={"color": "white", "fontWeight": "700", "marginBottom": "4px"}),
        html.P("Togo AI Lab - Data Challenge Environnement, Defi 1",
               style={"color": GOLD, "fontSize": "14px", "marginBottom": "0"}),
    ], style={"background": f"linear-gradient(120deg, {TEAL_DARK}, {TEAL})", "padding": "28px 34px"}),

    dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H2(str(nb_ouvrages), style={"color": TEAL, "fontWeight": "700"}),
                html.P("Ouvrages recenses", style={"marginBottom": "0", "opacity": 0.7}),
            ]), style={"borderRadius": "12px", "border": "none", "boxShadow": "0 2px 8px rgba(0,0,0,0.08)"})),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H2(f"{nb_cantons_sans_ouvrage}/{nb_cantons}", style={"color": "#C0392B", "fontWeight": "700"}),
                html.P("Cantons sans ouvrage", style={"marginBottom": "0", "opacity": 0.7}),
            ]), style={"borderRadius": "12px", "border": "none", "boxShadow": "0 2px 8px rgba(0,0,0,0.08)"})),
        ], className="g-3 my-3"),

       dcc.Tabs(
            id="tabs", value="tab-carte",
            children=[
                dcc.Tab(label="Cartographie", value="tab-carte", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(label="Fonctionnalite", value="tab-func", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(label="Demographie", value="tab-demo", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(label="Inondation", value="tab-flood", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(label="Ventes d'eau", value="tab-ventes", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(label="Recommandations", value="tab-reco", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
            ],
            style={"fontFamily": "Segoe UI, sans-serif"},
        ),
        html.Div(id="tab-content", className="my-3"),
    ], fluid=True, style={"maxWidth": "1300px"}),
], style={"backgroundColor": BG, "minHeight": "100vh", "fontFamily": "Segoe UI, sans-serif"})

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
    elif tab == "tab-ventes":
        return build_tab_ventes()
    elif tab == "tab-reco":
        return build_tab_recommandations()
    return html.Div()
   

if __name__ == "__main__":
    app.run(debug=True, port=8050)