import pandas as pd
import plotly.graph_objects as go

from dash import Dash, dcc, html
from config import df_radar_url, df_raw_data_url
from login import login_layout

# ====================== Athlete Profile ===================================
# Load raw data
df_raw_data = pd.read_csv(df_raw_data_url)

# Sort and store unique names from the name col
athlete_options = sorted(df_raw_data["Name"].dropna().unique())

# Store unique dates from data source
date_options = df_raw_data["Date"].dropna().unique()

# Test Type options
test_type_options = ["CMJ-RE", "CMJ", "ISO", "MAXED"]

# Comparison group options
comparison_group_options = ["Self", "Team", "Other"]

# ===================== Team Radar ========================================
# Load radar data
df_radar = pd.read_csv(df_radar_url)

# Pick one athlete + date for now
athlete_name = df_radar["Name"].iloc[1]
date = df_radar["Date"].iloc[1]

row = df_radar.iloc[1]

# Radar metrics needed
metrics = [
    "Jump Height Scaled",
    "Peak Velocity Scaled",
    "mRSI Scaled",
    "Jump Momentum Scaled",
    "Peak Relative Propulsive Power Scaled",
    "Peak Relative Braking Power Scaled",
]

# Metric labels to change value titles in radar chart
metric_label_map = {
    "Jump Height Scaled": "Jump Height",
    "Peak Velocity Scaled": "Speed",
    "mRSI Scaled": "Athletic Capacity",
    "Jump Momentum Scaled": "Acceleration",
    "Peak Relative Propulsive Power Scaled": "Push-off Power",
    "Peak Relative Braking Power Scaled": "Loading Power",
}


# Get values for each metric in data source
values = [row[m] for m in metrics]

# Radar chart
fig = go.Figure()

# Display layman tiles on radar chart
metrics_display = [metric_label_map.get(m, m) for m in metrics]

# Connects all dashed lines for the athlete and team average values
metrics_closed = metrics + [metrics[0]]
values_closed = values + [values[0]]

# Athelete values
fig.add_trace(
    go.Scatterpolar(
        r=values_closed,
        theta=metrics_display,
        fill="toself",
        name=f"{athlete_name} ({date})",
    )
)

# Team average
fig.add_trace(
    go.Scatterpolar(
        r=[50 for _ in range(6)],
        theta=metrics_display,
        name=f"Team Avg",
        line=dict(color="rgba(220, 20, 60, 1.0)", width=2, dash="dot"),
        opacity=0.3,
        fill=None,
    )
)

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    legend=dict(orientation="h", x=0.5, y=-0.2, xanchor="center", yanchor="top"),
    showlegend=True,
    title=dict(text="Athlete Vs Team", x=0.5, xanchor="center"),
)
# ============================================================================================================

# ====================== Bar Chart vs Self & Team ============================================================

# --- Current session values (same row used for the radar) ---
current_values = [row[m] for m in metrics]

# --- Athlete historical average: mean of all rows for this athlete across all dates ---
athlete_history = df_radar[df_radar["Name"] == athlete_name]
avg_values = [athlete_history[m].mean() for m in metrics]

# --- Friendly labels reused from the radar ---
bar_labels = [metric_label_map.get(m, m) for m in metrics]

# --- Build the grouped bar figure ---
fig_bar = go.Figure()

# Current session bars
fig_bar.add_trace(
    go.Bar(
        name="Current",
        x=bar_labels,
        y=current_values,
        marker_color="#4a90d9",  # solid blue
        marker_line=dict(color="#2c5f8a", width=1.2),
        width=0.35,
        textposition="outside",
        text=[f"{v:.1f}" for v in current_values],
        textfont=dict(size=11, color="#2c5f8a"),
    )
)

# Athlete average bars
fig_bar.add_trace(
    go.Bar(
        name="Avg",
        x=bar_labels,
        y=avg_values,
        marker_color="#7ec67e",  # solid green
        marker_line=dict(color="#4a8f4a", width=1.2),
        width=0.35,
        textposition="outside",
        text=[f"{v:.1f}" for v in avg_values],
        textfont=dict(size=11, color="#4a8f4a"),
    )
)

# --- Horizontal reference line at 50 (group / population average) ---
fig_bar.add_shape(
    type="line",
    x0=-0.5,
    x1=len(bar_labels) - 0.5,  # spans the full x-axis range
    y0=50,
    y1=50,
    line=dict(
        color="rgba(220, 20, 60, 0.7)",  # matches radar team-avg color
        width=2,
        dash="dash",
    ),
)

# Invisible scatter trace so the 50-line appears in the legend
fig_bar.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="lines",
        name="Group Avg (50)",
        line=dict(
            color="rgba(220, 20, 60, 0.7)",
            width=2,
            dash="dash",
        ),
        showlegend=True,
    )
)

fig_bar.update_layout(
    barmode="group",
    bargroupgap=0.1,  # gap between the two bars in each cluster
    bargap=0.25,  # gap between clusters
    yaxis=dict(
        range=[0, 115],  # extra headroom so "outside" text labels don't clip
        title=dict(text="Scaled Score (0–100)", font=dict(size=12)),
        tickvals=[0, 25, 50, 75, 100],
        ticktext=["0", "25", "50", "75", "100"],
        gridcolor="rgba(180,180,180,0.3)",
        zeroline=False,
    ),
    xaxis=dict(
        title=None,
        tickfont=dict(size=11),
    ),
    legend=dict(
        orientation="h",
        x=0.5,
        y=-0.18,
        xanchor="center",
        yanchor="top",
        font=dict(size=11),
    ),
    showlegend=True,
    title=dict(
        text="Self vs Team",
        x=0.5,
        xanchor="center",
        font=dict(size=15),
    ),
    margin=dict(t=45, b=60, l=45, r=20),
    plot_bgcolor="rgba(0,0,0,0)",  # transparent plot background
    paper_bgcolor="rgba(0,0,0,0)",  # transparent card background
)

# ============================================================================================================

# ====================== Bar Chart for movement analysis ============================================================

impulse_ratio = 2.35
impulse_ratio_team_avg = 2.41

metrics = {
    "Impulse Ratio": impulse_ratio,
    "Peak Relative Velocity": 1.92,  # m/s
    "Countermovement Depth": 0.31,  # m
    "Ground Contact Time": 0.182,  # s
}

# Build the graph
fig_movement_analysis = go.Figure(
    data=[
        go.Bar(
            name="Impulse Ratio",
            x=["Impulse Ratio"],
            y=[impulse_ratio],
            text=[f"{impulse_ratio:.2f}"],
            textposition="auto",
        ),
        go.Bar(
            name="Impulse Ratio Team Avg",
            x=["Impulse Ratio Team Avg"],
            y=[impulse_ratio_team_avg],
            text=[f"{impulse_ratio_team_avg:.2f}"],
            textposition="auto",
        ),
    ]
)

fig_movement_analysis.update_layout(
    height=350,
    margin=dict(l=40, r=40, t=40, b=40),
    yaxis=dict(title="", range=[0, 2.6], gridcolor="lightgray"),
    xaxis=dict(title=""),
    showlegend=False,
)
# ============================================================================================================

# ====================== Diverging bar chart for injury/asymmetry ============================================================

# Mock data
avg_to_date = [1, 0, -5]
baseline = [-5, -2, -10]

# Metric title for bars
metrics_asymmetry = [
    "Peak Loading Asymmetry",
    "Peak Takeoff Asymmetry",
    "Peak Braking Asymmetry",
]

# Create graph object
figure_injury_asymmetry = go.Figure(
    data=[
        # Baseline bar
        go.Bar(
            y=metrics_asymmetry,
            x=baseline,
            orientation="h",  # orient horizontally
            name="Baseline",
            marker=dict(opacity=0.45),
        ),
        # Avg to date
        go.Bar(
            y=metrics_asymmetry,
            x=avg_to_date,
            orientation="h",
            name="Avg to Date",
            marker_color="#7ec67e",
            text=avg_to_date,
            textposition="auto",
        ),
    ]
)

figure_injury_asymmetry.update_layout(
    title=dict(text="Asymmetry Analysis", x=0.5, xanchor="center"),
    barmode="overlay",
    height=350,
    xaxis=dict(
        range=[-11, 2],
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="black",
        tickmode="linear",
        tick0=-10,
        dtick=2,
        gridcolor="lightgray",
    ),
    yaxis=dict(autorange="reversed"),
    legend=dict(orientation="h", x=0.5, xanchor="center", yanchor="bottom", y=-0.5),
)
# ============================================================================================================

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
        "gridTemplateRows": "auto auto auto auto",
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
    children=[
        # LEFT COLUMN
        html.Div(
            style={**CARD_STYLE, "gridArea": "profile"},
            className="card",
            children=[
                html.H2("Athlete Profile"),
                html.Img(
                    src="assets/Images/Scott-founder.jpg", style={"width": "250px"}
                ),
                html.P("Name"),
                dcc.Dropdown(
                    id="athlete-dropdown",
                    options=[
                        {"label": name, "value": name} for name in athlete_options
                    ],
                    clearable=False,
                    placeholder="Select Athlete",
                ),
                html.P("Age: 17"),
                html.P("Height: 5' 10''"),
                html.P("Weight: 150 lbs"),
                html.Hr(),
                html.P("Sport: Basketball"),
                html.P("Position: Guard"),
                html.P("Team: PCHS"),
                html.P("Year: Sophomore"),
                html.Hr(),
                html.P("Test Date"),
                # TODO write the callback and function to only show dates from the selected athlete
                dcc.Dropdown(
                    id="date-dropdown",
                    options=[{"label": date, "value": date} for date in date_options],
                    placeholder="Select Date",
                ),
                html.P("Test Type: "),
                dcc.Dropdown(
                    id="test-type-dropdown",
                    options=[
                        {"label": test, "value": test} for test in test_type_options
                    ],
                    placeholder="Select test type",
                ),
                html.P("Comparison Group"),
                dcc.Dropdown(
                    id="comparison-group-dropdown",
                    options=[
                        {"label": group, "value": group}
                        for group in comparison_group_options
                    ],
                ),
            ],
        ),
        # TOP ROW
        html.Div(
            style={**CARD_STYLE, "gridArea": "radar_self"},
            className="card",
            children=[
                html.H2("Radar: Team", style={"text-align": "center"}),
                dcc.Graph(
                    id="radar-chart",
                    figure=fig,
                ),
            ],
        ),
        html.Div(
            style={**CARD_STYLE, "gridArea": "radar_team", "object-fit": "contain"},
            className="card",
            children=[
                html.H2("Self vs Team", style={"text-align": "center"}),
                dcc.Graph(
                    id="bar-chart",
                    figure=fig_bar,
                ),
            ],
        ),
        # MIDDLE ROW
        html.Div(
            style={**CARD_STYLE, "gridArea": "movement_a"},
            className="card",
            children=[
                html.H2("Movement Analysis", style={"test-align": "center"}),
                dcc.Graph(id="move-bar-chart", figure=fig_movement_analysis),
                html.Section(
                    children=[
                        html.P("Loading Speed"),
                        html.P("Sustained Push-off Power"),
                    ]
                ),
            ],
        ),
        html.Div(
            style={**CARD_STYLE, "gridArea": "injury"},
            className="card",
            children=[
                html.H2("Injury / Asymmetry", style={"test-align": "center"}),
                dcc.Graph(id="asymmetry-graph", figure=figure_injury_asymmetry),
            ],
        ),
        # LOWER ROW
        html.Div(
            "Placeholder",
            style={**CARD_STYLE, "gridArea": "placeholder"},
            className="card",
        ),
        html.Div(
            "Comparison / Percentiles",
            style={**CARD_STYLE, "gridArea": "comparison"},
            className="card",
        ),
        # FOOTER
        html.Div(
            "Strategy / Notes",
            style={**CARD_STYLE, "gridArea": "notes"},
            className="card",
        ),
    ],
)

if __name__ == "__main__":
    # Set app.run(host='0.0.0.0', port=8050, debug=False) to access on other clients in the network
    app.run(debug=True)
