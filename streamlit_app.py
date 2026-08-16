import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import geopandas as gpd
from pathlib import Path

ROOT = Path(__file__).parent
CLEAN = ROOT / "data" / "clean"

@st.cache_data
def load_all():
    cantons = gpd.read_file(CLEAN / "cantons.geojson")
    points = gpd.read_file(CLEAN / "water_points.geojson")
    points_full = pd.read_csv(CLEAN / "water_points_full.csv")
    sales = pd.read_csv(CLEAN / "water_sales.csv")
    pop = pd.read_csv(CLEAN / "population_rgph.csv")
    return cantons, points, points_full, sales, pop

cantons, points, points_full, sales, pop = load_all()

TEAL_DARK = "#0B3D3A"
TEAL = "#12645C"
GOLD = "#D4A62A"
BG = "#F5F7F6"

nb_ouvrages = len(points_full)
nb_cantons = len(cantons)
nb_cantons_sans_ouvrage = (cantons["nb_ouvrages"] == 0).sum()

# ensure there is an 'index' property in the GeoJSON properties for featureidkey
if "index" not in cantons.columns:
    # preserve existing index by creating a column named 'index'
    cantons = cantons.reset_index(drop=False)
# make sure it's a string so feature matching is consistent
cantons["index"] = cantons["index"].astype(str)
geojson = json.loads(cantons.to_json())

coso_pts_full = points_full[points_full["source"] == "COSO"]

st.set_page_config(page_title="Diagnostic eau Togo", layout="wide")

st.markdown(f"""
<div style="background: linear-gradient(120deg, {TEAL_DARK}, {TEAL}); padding: 28px 34px; color: white; border-radius:6px">
  <h1 style="margin:0">Diagnostic de l'accès à l'eau potable au Togo</h1>
  <p style="margin:0">Togo AI Lab - Data Challenge Environnement, Defi 1</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.metric("Ouvrages recenses", str(nb_ouvrages))
with col2:
    st.metric("Cantons sans ouvrage", f"{nb_cantons_sans_ouvrage}/{nb_cantons}")

tabs = st.tabs(["Cartographie", "Fonctionnalite", "Demographie", "Inondation", "Ventes d'eau", "Recommandations"]) 

# helper to create safe scatter traces from a GeoDataFrame of Points
def safe_scatter_from_points(df, name, color):
    if df is None:
        return None
    df = df[df.geometry.notnull()].copy()
    if df.empty:
        return None
    # ensure points are Points with x/y
    try:
        lats = df.geometry.y
        lons = df.geometry.x
    except Exception:
        return None
    return go.Scattermapbox(
        lat=lats, lon=lons, mode="markers",
        marker=dict(size=7, color=color), name=name,
        text=df.get("canton_nom", None),
        hovertemplate=f"<b>{name}</b><br>Canton: %{{text}}<extra></extra>"
    )

# Tab 1: Cartographie
with tabs[0]:
    fig_map = px.choropleth_mapbox(
        cantons,
        geojson=geojson,
        locations=cantons["index"],
        color="nb_ouvrages",
        hover_name="canton_nom",
        hover_data={"region": True, "total_pop": ":,.0f", "nb_ouvrages": True},
        color_continuous_scale=[[0, "#E8ECEA"], [0.5, "#1E8A7E"], [1, TEAL_DARK]],
        mapbox_style="carto-positron",
        zoom=6.3,
        center={"lat": 8.6, "lon": 1.0},
        opacity=0.75,
        labels={"nb_ouvrages": "Nb ouvrages"},
        featureidkey="properties.index"
    )

    coso_pts = points[points["source"] == "COSO"]
    tde_pts = points[points["source"] == "TdE"]

    trace_coso = safe_scatter_from_points(coso_pts, "Ouvrages COSO", "#0B3D3A")
    if trace_coso is not None:
        fig_map.add_trace(trace_coso)

    trace_tde = safe_scatter_from_points(tde_pts, "Ouvrages TdE", "#D4A62A")
    if trace_tde is not None:
        fig_map.add_trace(trace_tde)

    fig_map.update_layout(title="Repartition des ouvrages par canton", height=600, margin=dict(l=0, r=0, t=40, b=0), legend=dict(orientation="h", y=1.02, x=0))

    # show map with error handling to avoid client-side crash
    try:
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        st.error(f"Impossible d'afficher la carte : {e}")

    couverture = cantons.groupby("region").apply(lambda d: round((d["nb_ouvrages"] == 0).mean() * 100, 1)).reset_index(name="pct_sans_ouvrage").sort_values("pct_sans_ouvrage")
    fig_couverture = px.bar(couverture, x="pct_sans_ouvrage", y="region", orientation="h", text="pct_sans_ouvrage",
                             labels={"pct_sans_ouvrage": "% cantons sans ouvrage", "region": ""}, color="pct_sans_ouvrage", color_continuous_scale="Reds")
    fig_couverture.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_couverture.update_layout(title="% de cantons sans aucun ouvrage recense, par region", height=350, coloraxis_showscale=False, xaxis_range=[0, 110])
    st.plotly_chart(fig_couverture, use_container_width=True)

# Tab 2: Fonctionnalite
with tabs[1]:
    risque_par_region = pd.crosstab(coso_pts_full["region"], coso_pts_full["proxy_risque_panne"], normalize="index") * 100
    risque_par_region = risque_par_region.reset_index().melt(id_vars="region", var_name="niveau", value_name="pct")
    ordre_niveaux = ["Faible risque", "Risque modéré", "Risque élevé"]
    couleurs_risque = {"Faible risque": "#1E8A7E", "Risque modéré": "#D4A62A", "Risque élevé": "#C0392B"}
    fig_risque = px.bar(risque_par_region, x="region", y="pct", color="niveau",
                        category_orders={"niveau": ordre_niveaux}, color_discrete_map=couleurs_risque,
                        labels={"pct": "% d'ouvrages COSO", "region": "", "niveau": ""})
    fig_risque.update_layout(height=400, legend=dict(orientation="h", y=-0.15), title="Risque de panne par region")

    maintenance = coso_pts_full["maintenance_manquante"].map({0: "Plan existant", 1: "Aucun plan"}).fillna("Non renseigne")
    fig_maintenance = px.pie(maintenance.value_counts().reset_index(), names="maintenance_manquante", values="count",
                             color="maintenance_manquante",
                             color_discrete_map={"Plan existant": "#1E8A7E", "Aucun plan": "#C0392B", "Non renseigne": "#9AA6A4"}, hole=0.5)
    fig_maintenance.update_layout(title="Plan de maintenance declare (ouvrages COSO)", height=400)

    st.plotly_chart(fig_risque, use_container_width=True)
    st.plotly_chart(fig_maintenance, use_container_width=True)

# Tab 3: Demographie
with tabs[2]:
    fig_demo = px.scatter(cantons, x="total_pop", y="nb_ouvrages", color="region", hover_name="canton_nom",
                         labels={"total_pop": "Population du canton", "nb_ouvrages": "Nb ouvrages recenses"}, log_x=True,
                         color_discrete_sequence=[TEAL_DARK, TEAL, "#1E8A7E", GOLD, "#8E6E00"])
    fig_demo.update_layout(height=550, legend=dict(orientation="h", y=-0.15), title="Repartition des ouvrages par canton")
    st.plotly_chart(fig_demo, use_container_width=True)

# Tab 4: Inondation
with tabs[3]:
    fig_fri = px.choropleth_mapbox(cantons, geojson=geojson, locations=cantons["index"], color="FRI",
                                  hover_name="canton_nom", hover_data={"region": True, "FRI": ":.2f", "nb_ouvrages": True},
                                  color_continuous_scale=[[0, "#EAF4F2"], [0.5, GOLD], [1, "#C0392B"]], mapbox_style="carto-positron",
                                  zoom=6.3, center={"lat": 8.6, "lon": 1.0}, opacity=0.8, featureidkey="properties.index")
    # add points safely
    pts_for_fri = points[points.geometry.notnull()]
    trace_pts = safe_scatter_from_points(pts_for_fri, "Ouvrages", "#0B3D3A")
    if trace_pts is not None:
        fig_fri.add_trace(trace_pts)
    fig_fri.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=600, legend=dict(orientation="h", y=1.02, x=0))
    try:
        st.plotly_chart(fig_fri, use_container_width=True)
    except Exception as e:
        st.error(f"Impossible d'afficher la carte FRI : {e}")

# Tab 5: Ventes d'eau
with tabs[4]:
    try:
        fig_ventes = px.line(sales, x="annee", y="valeur_m3", color="categorie", labels={"annee": "Annee", "valeur_m3": "Ventes (m3)", "categorie": "Categorie"}, markers=True)
        fig_ventes.update_layout(title="Evolution des ventes d'eau par categorie (2018-2022)")
        derniere_annee = sales["annee"].max()
        sales_derniere = sales[sales["annee"] == derniere_annee].sort_values("valeur_m3", ascending=True)
        fig_derniere = px.bar(sales_derniere, x="valeur_m3", y="categorie", orientation="h", labels={"valeur_m3": f"Ventes m3 ({derniere_annee})", "categorie": ""}, color="valeur_m3")
        fig_derniere.update_layout(title=f"Ventes par categorie - {derniere_annee}", height=500, coloraxis_showscale=False)
        st.plotly_chart(fig_ventes, use_container_width=True)
        st.plotly_chart(fig_derniere, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de la génération des graphiques de ventes : {e}")

# Tab 6: Recommandations
with tabs[5]:
    st.subheader("Recommandations")
    st.markdown("""
- PRIORITE 1 — Combler le vide de couverture: Plateaux, Kara et Centrale sont quasi non couverts par les donnees COSO/TdE. Verifier sur le terrain avant tout nouveau forage.
- PRIORITE 1 — Securiser la maintenance existante: Une part importante des ouvrages COSO n'a pas de plan de maintenance declare.
- PRIORITE 2 — Proteger les ouvrages en zone inondable: Integrer le FRI comme critere de choix d'implantation.
- PRIORITE 2 — Fiabiliser la donnee: Georeferencement obligatoire a la reception.
""")

st.markdown("\n---\n")
st.caption("Application convertie pour Streamlit — si vous déployez via Docker, utilisez le Dockerfile fourni.")
