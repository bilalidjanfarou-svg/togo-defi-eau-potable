from dash import Dash, html
import dash_bootstrap_components as dbc
from data_loader import load_all

cantons, points, points_full, sales, pop = load_all()

nb_ouvrages = len(points_full)
nb_cantons = len(cantons)
nb_cantons_sans_ouvrage = (cantons["nb_ouvrages"] == 0).sum()

print(f"Ouvrages : {nb_ouvrages}")
print(f"Cantons : {nb_cantons}")
print(f"Cantons sans ouvrage : {nb_cantons_sans_ouvrage}")

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = html.Div([
    html.H1("Diagnostic Eau Potable - Togo"),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H2(str(nb_ouvrages)), html.P("Ouvrages recenses")]))),
        dbc.Col(dbc.Card(dbc.CardBody([html.H2(f"{nb_cantons_sans_ouvrage}/{nb_cantons}"), html.P("Cantons sans ouvrage")]))),
    ], className="m-3"),
])

if __name__ == "__main__":
    app.run(debug=True, port=8050)