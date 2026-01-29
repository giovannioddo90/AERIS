import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html

#====================== Athlete Profile ===================================

# ===================== Team Radar ========================================
# Load radar data
df_radar = pd.read_csv("https://docs.google.com/spreadsheets/d/1u2qa2sIZU9izlymRfDG7VtOD6wRt4MvppcwPdyulaE4/export?format=csv&gid=396575242")

# Pick one athlete + date for now
athlete_name = df_radar["Name"].iloc[1]
date = df_radar["Date"].iloc[1]

row = df_radar.iloc[1]

# Radar metrics (explicit = safer)
metrics = [
    "Jump Height Scaled",
    "Peak Velocity Scaled",
    "mRSI Scaled",
    "Jump Momentum Scaled",
    "Peak Relative Propulsive Power Scaled",
    "Peak Relative Braking Power Scaled"
]

values = [row[m] for m in metrics]

# Radar chart
fig = go.Figure()
metrics_closed = metrics + [metrics[0]]
# Athelete values
fig.add_trace(go.Scatterpolar(
    r=values,
    theta=metrics_closed,
    fill='toself',
    name=f"{athlete_name} ({date})"
))

# Team average 
fig.add_trace(go.Scatterpolar(
    r=[50 for _ in range(7)],
    theta=metrics_closed,
    
    name=f"Team Avg",
    line=dict(
        color="rgba(220, 20, 60, 1.0)",
        width=2,
        dash="dot"
    ),
    fill=None
))

fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    ),
    showlegend=True,
    title="Athlete Vs Team"
)
#============================================================================================================

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
            'profile movement_a injury'
            'profile placeholder comparison'
            'profile notes notes'
        """,
        "gap": "16px",
        "padding": "16px",
        "height": "100vh",
        "boxSizing": "border-box",
    },

    children = [
        # LEFT COLUMN
        html.Div(style={**CARD_STYLE, "gridArea": "profile"}, className="card",
                children = [
                    html.H3("Athlete Profile"), 
                    html.P("Name"),
                    html.P("Age"),
                    html.P("Height"),
                    html.P("Weight"),
                    html.Hr(),
                    html.P("Sport"),
                    html.P("Position"),
                    html.P("Team"),
                    html.P("Year"),
                    html.Hr(),
                    html.P("Test Date: "),
                    html.P("Test Type: "),
                    html.P("Comparison Group")
                ] 
            ),

        # TOP ROW
        html.Div("Radar: Athlete", style={**CARD_STYLE, "gridArea": "radar_self"}, className="card"),

                
        html.Div(style={**CARD_STYLE, "gridArea": "radar_team"}, className="card",
                 children = [
                    html.H3("Radar: Athlete"),
                    dcc.Graph(
                    id='radar-chart',
                    figure=fig,
                        ) 
                    ]
                ),

        # MIDDLE ROW
        html.Div("Movement Analysis", style={**CARD_STYLE, "gridArea": "movement_a"}, className="card"),
        html.Div("Injury / Asymmetry", style={**CARD_STYLE, "gridArea": "injury"}, className="card"),

        # LOWER ROW
        html.Div("Placeholder", style={**CARD_STYLE, "gridArea": "placeholder"}, className="card"),
        html.Div("Comparison / Percentiles", style={**CARD_STYLE, "gridArea": "comparison"}, className="card"),

        # FOOTER
        html.Div("Strategy / Notes", style={**CARD_STYLE, "gridArea": "notes"}, className="card"),
    ]
)

if __name__ == "__main__":
    # Set app.run(host='0.0.0.0', port=8050, debug=False) to access on other clients in the network
    app.run(debug=True)
