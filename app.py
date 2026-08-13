from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import json
from data_loader import load_all

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
fig_map.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=600)

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = html.Div([
    html.H1("Diagnostic Eau Potable - Togo"),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H2(str(nb_ouvrages)), html.P("Ouvrages recenses")]))),
        dbc.Col(dbc.Card(dbc.CardBody([html.H2(f"{nb_cantons_sans_ouvrage}/{nb_cantons}"), html.P("Cantons sans ouvrage")]))),
    ], className="m-3"),
    dcc.Graph(figure=fig_map, className="m-3"),
])

if __name__ == "__main__":
    app.run(debug=True, port=8050)