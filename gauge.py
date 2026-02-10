import pandas as pd
import plotly.graph_objects as go

from dash import Dash, dcc, html
from config import df_radar_url, df_raw_data_url

# ====================== Data Loading ===================================
df_raw_data = pd.read_csv(df_raw_data_url)

# Sort and store unique names from the name col
athlete_options = sorted(df_raw_data["Name"].dropna().unique())

# Store unique dates from data source
date_options = df_raw_data["Date"].dropna().unique()

# Test Type options
test_type_options = ["CMJ-RE", "CMJ", "ISO", "MAXED"]

# Comparison group options
comparison_group_options = ["Self", "Team", "Other"]

# Load radar data for metrics
df_radar = pd.read_csv(df_radar_url)

# Pick one athlete + date for now (will be dynamic later)
row = df_radar.iloc[1]
athlete_name = row["Name"]

# ====================== Gauge Helper Function ===================================
def create_gauge(value, title, min_val=0, max_val=100):
    """Create a single gauge chart with scaled z-score (0-100)."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title, "font": {"size": 14}},
            number={"font": {"size": 24}},
            gauge={
                "axis": {"range": [min_val, max_val], "tickwidth": 1},
                "bar": {"color": "#4a90d9"},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 25], "color": "#ffcccc"},
                    {"range": [25, 50], "color": "#ffffcc"},
                    {"range": [50, 75], "color": "#ccffcc"},
                    {"range": [75, 100], "color": "#99ff99"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 2},
                    "thickness": 0.75,
                    "value": 50,
                },
            },
        )
    )
    fig.update_layout(
        height=200,
        margin=dict(l=30, r=30, t=50, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ====================== Gauge Data (Scaled Z-Scores 0-100) ===================================
# Performance Output metrics from radar data
speed_agility = row.get("Jump Momentum Scaled", 50)
explosive_athleticism = row.get("mRSI Scaled", 50)
power = row.get("Peak Relative Propulsive Power Scaled", 50)
total_strength = 55  # Net Positive Impulse - placeholder (not in sheet)
vertical = row.get("Jump Height Scaled", 50)

# Total Score Athleticism (TSA) = mean of the 5 performance outputs
tsa = (speed_agility + explosive_athleticism + power + total_strength + vertical) / 5

# ====================== Create Gauge Figures ===================================
# TSA gauge (larger)
gauge_tsa = create_gauge(tsa, "Total Score Athleticism (TSA)")
gauge_tsa.update_layout(height=220)

# Performance Output gauges
gauge_speed_agility = create_gauge(speed_agility, "Speed & Agility")
gauge_explosive = create_gauge(explosive_athleticism, "Explosive Athleticism")
gauge_power = create_gauge(power, "Power")
gauge_strength = create_gauge(total_strength, "Total Strength")
gauge_vertical = create_gauge(vertical, "Vertical")

# ====================== Bar Graph Data ===================================
# Metrics for bar graphs (mapping to available columns or placeholders)
bar_metrics = {
    "Impulse Ratio": "mRSI Scaled",
    "Braking Impulse": "Peak Relative Braking Power Scaled",
    "Propulsive Impulse": "Peak Relative Propulsive Power Scaled",
    "Peak Relative Landing Force": None,  # Placeholder - not in sheet
    "Peak Velocity": "Peak Velocity Scaled",
    "Time to Takeoff": None,  # Placeholder - not in sheet
    "Peak Relative Braking Force": "Peak Relative Braking Power Scaled",
}

# Get athlete's historical data (excluding most recent)
athlete_history = df_radar[df_radar["Name"] == athlete_name]

# Calculate team averages
team_averages = {}
for label, col in bar_metrics.items():
    if col and col in df_radar.columns:
        team_averages[label] = df_radar[col].mean()
    else:
        team_averages[label] = 50  # Placeholder


def create_metric_bar_graph(metric_label, column_name):
    """Create a bar graph with 3 bars: most recent, avg (excluding recent), team avg."""
    if column_name and column_name in df_radar.columns:
        most_recent = row.get(column_name, 50)
        # Average excluding most recent (if more than 1 record)
        if len(athlete_history) > 1:
            avg_excluding_recent = athlete_history[column_name].iloc[:-1].mean()
        else:
            avg_excluding_recent = most_recent
        team_avg = team_averages[metric_label]
    else:
        # Placeholder values
        most_recent = 50
        avg_excluding_recent = 48
        team_avg = 50

    fig = go.Figure(
        data=[
            go.Bar(
                name="Most Recent",
                x=["Most Recent"],
                y=[most_recent],
                marker_color="#4a90d9",
                text=[f"{most_recent:.1f}"],
                textposition="outside",
            ),
            go.Bar(
                name="Avg (Previous)",
                x=["Avg (Previous)"],
                y=[avg_excluding_recent],
                marker_color="#7ec67e",
                text=[f"{avg_excluding_recent:.1f}"],
                textposition="outside",
            ),
            go.Bar(
                name="Team Avg",
                x=["Team Avg"],
                y=[team_avg],
                marker_color="#d9534f",
                text=[f"{team_avg:.1f}"],
                textposition="outside",
            ),
        ]
    )

    fig.update_layout(
        title=dict(text=metric_label, x=0.5, xanchor="center", font=dict(size=14)),
        height=250,
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(range=[0, 110], title="", gridcolor="lightgray"),
        xaxis=dict(title="", showticklabels=False),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.3,
    )
    return fig


# Create bar graphs for each metric
bar_graphs = {}
for label, col in bar_metrics.items():
    bar_graphs[label] = create_metric_bar_graph(label, col)

# ====================== Asymmetry Data ===================================
# Mock asymmetry data (scaled percentages)
asymmetry_metrics = [
    "Loading Asymmetry",
    "Takeoff Asymmetry",
    "Braking Asymmetry",
]
avg_to_date = [8, 15, -12]
baseline = [-5, -2, -18]

# Create asymmetry diverging bar chart
fig_asymmetry = go.Figure(
    data=[
        go.Bar(
            y=asymmetry_metrics,
            x=baseline,
            orientation="h",
            name="Baseline",
            marker=dict(opacity=0.45),
        ),
        go.Bar(
            y=asymmetry_metrics,
            x=avg_to_date,
            orientation="h",
            name="Avg to Date",
            marker_color="#7ec67e",
            text=avg_to_date,
            textposition="auto",
        ),
    ]
)

fig_asymmetry.update_layout(
    title=dict(text="Asymmetry Analysis", x=0.5, xanchor="center"),
    barmode="overlay",
    height=300,
    xaxis=dict(
        range=[-30, 30],
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="black",
        tickmode="linear",
        tick0=-30,
        dtick=10,
        gridcolor="lightgray",
        title="Asymmetry %",
    ),
    yaxis=dict(autorange="reversed"),
    legend=dict(orientation="h", x=0.5, xanchor="center", yanchor="bottom", y=-0.55),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=40, t=50, b=60),
)

# ====================== Styling ===================================
CARD_STYLE = {
    "backgroundColor": "#e2efe2",
    "borderRadius": "12px",
    "padding": "16px",
    "boxShadow": "0 4px 10px rgba(0,0,0,0.08)",
}

GAUGE_CLUSTER_STYLE = {
    "display": "flex",
    "flexWrap": "wrap",
    "justifyContent": "center",
    "gap": "8px",
}

# ====================== Layout Function ===================================
def gauge_layout():
    return html.Div(
        className="gauge-container",
        style={
            "display": "grid",
            "gridTemplateColumns": "280px 1fr",
            "gridTemplateRows": "auto",
            "gridTemplateAreas": """
                'profile gauges'
            """,
            "gap": "16px",
            "padding": "16px",
            "minHeight": "100vh",
            "boxSizing": "border-box",
        },
        children=[
            # ====================== Athlete Profile (Left Column) ===================================
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
                    html.Hr(),
                    html.P(f"Total Tests Available: {len(date_options)}"),
                ],
            ),
            # ====================== Performance Outputs (Gauge Clusters) ===================================
            html.Div(
                style={"gridArea": "gauges"},
                children=[
                    # TSA (Total Score Athleticism) - Top gauge
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "16px", "display": "flex", "justifyContent": "center"},
                        children=[
                            html.Div(
                                dcc.Graph(figure=gauge_tsa, config={"displayModeBar": False}),
                                style={"width": "300px"},
                            ),
                        ],
                    ),
                    # 5 Performance Output gauges below TSA
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "16px"},
                        children=[
                            html.H3("Performance Outputs", style={"textAlign": "center", "marginBottom": "8px"}),
                            html.Div(
                                style=GAUGE_CLUSTER_STYLE,
                                children=[
                                    html.Div(
                                        dcc.Graph(figure=gauge_speed_agility, config={"displayModeBar": False}),
                                        style={"width": "200px"},
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=gauge_explosive, config={"displayModeBar": False}),
                                        style={"width": "200px"},
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=gauge_power, config={"displayModeBar": False}),
                                        style={"width": "200px"},
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=gauge_strength, config={"displayModeBar": False}),
                                        style={"width": "200px"},
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=gauge_vertical, config={"displayModeBar": False}),
                                        style={"width": "200px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # ====================== Metric Bar Graphs ===================================
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "16px"},
                        children=[
                            html.H3("Detailed Metrics", style={"textAlign": "center", "marginBottom": "8px"}),
                            # Legend
                            html.Div(
                                style={
                                    "display": "flex",
                                    "justifyContent": "center",
                                    "gap": "24px",
                                    "marginBottom": "16px",
                                },
                                children=[
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "6px"},
                                        children=[
                                            html.Div(style={"width": "16px", "height": "16px", "backgroundColor": "#4a90d9", "borderRadius": "2px"}),
                                            html.Span("Most Recent", style={"fontSize": "13px"}),
                                        ],
                                    ),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "6px"},
                                        children=[
                                            html.Div(style={"width": "16px", "height": "16px", "backgroundColor": "#7ec67e", "borderRadius": "2px"}),
                                            html.Span("Avg (Previous)", style={"fontSize": "13px"}),
                                        ],
                                    ),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "6px"},
                                        children=[
                                            html.Div(style={"width": "16px", "height": "16px", "backgroundColor": "#d9534f", "borderRadius": "2px"}),
                                            html.Span("Team Avg", style={"fontSize": "13px"}),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(4, 1fr)",
                                    "gap": "8px",
                                },
                                children=[
                                    html.Div(
                                        dcc.Graph(figure=bar_graphs["Impulse Ratio"], config={"displayModeBar": False}),
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=bar_graphs["Braking Impulse"], config={"displayModeBar": False}),
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=bar_graphs["Propulsive Impulse"], config={"displayModeBar": False}),
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=bar_graphs["Peak Relative Landing Force"], config={"displayModeBar": False}),
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=bar_graphs["Peak Velocity"], config={"displayModeBar": False}),
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=bar_graphs["Time to Takeoff"], config={"displayModeBar": False}),
                                    ),
                                    html.Div(
                                        dcc.Graph(figure=bar_graphs["Peak Relative Braking Force"], config={"displayModeBar": False}),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # ====================== Asymmetry Section ===================================
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "16px"},
                        children=[
                            dcc.Graph(figure=fig_asymmetry, config={"displayModeBar": False}),
                            html.P(
                                "Over 25% recommends a deeper dive, 12-25% place on monitoring.",
                                style={
                                    "textAlign": "center",
                                    "fontStyle": "italic",
                                    "color": "#666",
                                    "marginTop": "10px",
                                },
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


# ====================== Standalone App (for testing) ===================================
if __name__ == "__main__":
    app = Dash(__name__)
    app.layout = gauge_layout()
    app.run(debug=True, port=8051)
