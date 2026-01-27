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

# Card styling
CARD_STYLE = {
    "backgroundColor": "#e2efe2",
    "borderRadius": "12px",
    "padding": "16px",
    "boxShadow": "0 4px 10px rgba(0,0,0,0.08)",
}

# Dash app
app = Dash(__name__)

app.layout = html.Div(
    className="app-container",
    
    # Main container style
    style={
        "display": "grid",
        "gridTemplateColumns": "280px 1fr 1fr",
        "gridTemplateRows": "auto auto auto 1fr",
        "gridTemplateAreas": """
            'profile radar_self radar_team'
            'profile movement_a movement_b'
            'profile injury comparison'
            'profile notes notes'
        """,
        "gap": "16px",
        "padding": "16px",
        "height": "100vh",
        "boxSizing": "border-box",
    },
    children=[
        # LEFT COLUMN
        html.Div("Athlete Profile", style={**CARD_STYLE, "gridArea": "profile"}, className="card"),

        # TOP ROW
        html.Div("Radar: Athlete", style={**CARD_STYLE, "gridArea": "radar_self"}, className="card"),
        html.Div("Radar: Team", style={**CARD_STYLE, "gridArea": "radar_team"}, className="card"),

        # MIDDLE ROW
        html.Div("Movement Analysis A", style={**CARD_STYLE, "gridArea": "movement_a"}, className="card"),
        html.Div("Movement Analysis B", style={**CARD_STYLE, "gridArea": "movement_b"}, className="card"),

        # LOWER ROW
        html.Div("Injury Risk / Asymmetry", style={**CARD_STYLE, "gridArea": "injury"}, className="card"),
        html.Div("Comparison / Percentiles", style={**CARD_STYLE, "gridArea": "comparison"}, className="card"),

        # FOOTER
        html.Div("Strategy / Notes", style={**CARD_STYLE, "gridArea": "notes"}, className="card"),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
