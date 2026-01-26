import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html

# Load radar data
df = pd.read_csv("https://docs.google.com/spreadsheets/d/1u2qa2sIZU9izlymRfDG7VtOD6wRt4MvppcwPdyulaE4/export?format=csv&gid=396575242")

# Pick one athlete + date for now
athlete_name = df["Name"].iloc[1]
date = df["Date"].iloc[1]

row = df.iloc[1]

# Radar metrics (explicit = safer)
metrics = [
    "Jump Height",
    "Peak Velocity",
    "mRSI",
    "Jump Momentum",
    "Peak Relative Propulsive Power",
    "Peak Relative Braking Power"
]

values = [row[m] for m in metrics]

# Radar chart
fig = go.Figure()

fig.add_trace(go.Scatterpolar(
    r=values,
    theta=metrics,
    fill='toself',
    name=f"{athlete_name} ({date})"
))

fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    ),
    showlegend=True,
    title="Countermovement Jump Radar Profile"
)

# Dash app
app = Dash(__name__)

app.layout = html.Div(
    style={"width": "700px", "margin": "auto"},
    children=[
        html.H1("Aegis Performance"),
        dcc.Graph(figure=fig)
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
