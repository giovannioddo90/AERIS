import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, dcc, html

import queries as q

# ====================== Gauge Config ===================================
# Maps gauge ID suffix -> (display title, DB column)
GAUGE_CONFIG = [
    ("explosive-vertical", "Explosive Vertical", "cmj_jump_height_m"),
    (
        "explosive-acceleration",
        "Explosive Acceleration",
        "rebound_jump_momentum_kg_m_s",
    ),
    ("explosive-capacity", "Explosive Capacity", "rebound_modified_rsi"),
    (
        "change-of-direction",
        "Change of Direction",
        "rebound_peak_relative_braking_power_w_kg",
    ),
    ("takeoff-power", "Take-Off Power", "rebound_peak_relative_propulsive_power_w_kg"),
]

# ====================== Injury Risk Config ===================================
# (id_suffix, display_title, db_column)
INJURY_CONFIG = [
    ("lr-peak-braking", "Peak Braking Force", "lr_peak_braking_force"),
    ("lr-peak-landing", "Peak Landing Force", "lr_peak_landing_force"),
    ("lr-peak-propulsive", "Peak Propulsive Force", "lr_peak_propulsive_force"),
]

# ====================== Bar Graph Config ===================================
# (id_suffix, display_title, db_column, unit)
BAR_CONFIG = [
    (
        "sustained-braking",
        "Sustained Force Braking",
        "rebound_relative_braking_impulse_n_s_kg",
        "N·s/kg",
    ),
    (
        "sustained-propulsive",
        "Sustained Force Propulsive",
        "rebound_relative_propulsive_impulse_n_s_kg",
        "N·s/kg",
    ),
    ("force-strategy", "Force Strategy", "rebound_impulse_ratio", "ratio"),
    ("ground-contact-time", "Ground Contact Time", "rebound_contact_time_ms", "ms"),
    (
        "peak-force-min-disp",
        "Peak Force at Min Displacement",
        "rebound_force_at_min_displacement_n",
        "N",
    ),
]


# ====================== Gauge Helper Function ===================================
def create_gauge(
    value: float, title: str, baseline: float | None = None, min_val=0, max_val=100
) -> go.Figure:
    """Create a single gauge chart with scaled z-score (0-100).

    baseline: optional scaled score from the athlete's earliest test,
              rendered as a colored tick line on the gauge arc.
    """
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
            domain={"x": [0, 1], "y": [0, 1]},
        )
    )

    # Overlay a second invisible gauge to render the baseline tick line
    if baseline is not None:
        fig.add_trace(
            go.Indicator(
                mode="gauge",
                value=0,
                gauge={
                    "axis": {"range": [min_val, max_val], "visible": False},
                    "bar": {"color": "rgba(0,0,0,0)"},
                    "bgcolor": "rgba(0,0,0,0)",
                    "borderwidth": 0,
                    "steps": [],
                    "threshold": {
                        "line": {"color": "orange", "width": 2},
                        "thickness": 0.75,
                        "value": baseline,
                    },
                },
                domain={"x": [0, 1], "y": [0, 1]},
            )
        )

    fig.update_layout(
        height=200,
        margin=dict(l=30, r=30, t=50, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def scale_to_gauge(value: float, mean: float, std: float) -> float:
    """Convert a raw metric value to a 0-100 gauge score via z-score.

    z=0 maps to 50, z=±3 maps to 0/100, clamped to [0, 100].
    """
    z = (value - mean) / std
    scaled = 50 + (z / 3) * 50
    return max(0.0, min(100.0, round(scaled, 1)))


# ====================== Bar Graph Helper Function ===================================
def create_bar_chart(
    athlete_value: float | None,
    athlete_avg: float | None,
    team_avg: float | None,
    title: str,
    unit: str,
) -> go.Figure:
    """Create a grouped bar chart with 3 bars: selected test, athlete avg, team avg."""
    values = [
        athlete_value if athlete_value is not None else 0,
        athlete_avg if athlete_avg is not None else 0,
        team_avg if team_avg is not None else 0,
    ]
    labels = ["Selected Test", "Athlete Avg", "Team Avg"]
    colors = ["#4a90d9", "#7ec67e", "#d9534f"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=[f"{v:.2f}" for v in values],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=14, color="white", family="Arial Black"),
            )
        ]
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=13)),
        height=280,
        margin=dict(l=40, r=20, t=50, b=40),
        yaxis=dict(title=unit, gridcolor="lightgray"),
        xaxis=dict(tickfont=dict(size=10)),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.3,
    )
    return fig


_default_bar = create_bar_chart(0, 0, 0, "—", "")


# ====================== Diverging Chart Helper Function ===================================
def create_diverging_chart(
    baseline_data: dict,
    selected_data: dict,
) -> go.Figure:
    """Create a horizontal diverging bar chart for injury risk asymmetry.

    Shows baseline vs selected test for each metric, overlaid.
    If selected_data is empty, shows baseline only.
    """
    labels = [title for _, title, _ in INJURY_CONFIG]
    cols = [col for _, _, col in INJURY_CONFIG]

    baseline_vals = [float(baseline_data.get(c) or 0) for c in cols]

    fig = go.Figure()

    if selected_data:
        selected_vals = [float(selected_data.get(c) or 0) for c in cols]
        # Baseline trace (semi-transparent, behind)
        fig.add_trace(
            go.Bar(
                y=labels,
                x=baseline_vals,
                orientation="h",
                name="Baseline",
                marker=dict(color="#4a90d9", opacity=0.45),
                text=[f"{v:.2f}" for v in baseline_vals],
                textposition="auto",
            )
        )
        # Selected test trace (solid, on top)
        fig.add_trace(
            go.Bar(
                y=labels,
                x=selected_vals,
                orientation="h",
                name="Selected Test",
                marker_color="#7ec67e",
                text=[f"{v:.2f}" for v in selected_vals],
                textposition="auto",
            )
        )
    else:
        # No selected data or selected date is baseline — show baseline only
        fig.add_trace(
            go.Bar(
                y=labels,
                x=baseline_vals,
                orientation="h",
                name="Baseline (only test)",
                marker_color="#4a90d9",
                text=[f"{v:.2f}" for v in baseline_vals],
                textposition="auto",
            )
        )

    # Determine symmetric x-axis range
    all_vals = baseline_vals + (
        [float(selected_data.get(c) or 0) for c in cols] if selected_data else []
    )
    max_abs = max(abs(v) for v in all_vals) if all_vals else 1
    x_range = max(max_abs * 1.3, 0.1)

    fig.update_layout(
        title=dict(text="Asymmetry Analysis", x=0.5, xanchor="center"),
        barmode="group",
        height=300,
        xaxis=dict(
            range=[-x_range, x_range],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="black",
            gridcolor="lightgray",
            title="Asymmetry",
        ),
        yaxis=dict(autorange="reversed"),
        legend=dict(
            orientation="h", x=0.5, xanchor="center", yanchor="bottom", y=-0.55
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=50, b=60),
    )
    return fig


_default_diverging = create_diverging_chart({}, {})


# =============== Startup data ==================================
dropdown_names = q.get_athlete_names()
population_stats = q.get_population_stats()
team_averages = q.get_team_average()

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

# Default empty gauge figure (shown before any selection)
_default_gauge = create_gauge(50, "—")


def serve_layout():
    """Returns the page layout"""
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
            # ====================== Athlete Profile ===================================
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
                            {"label": name, "value": name} for name in dropdown_names
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
                        options=[],
                        placeholder="Select Date",
                    ),
                    html.P("Test Type: "),
                    dcc.Dropdown(
                        id="test-type-dropdown",
                        options=[
                            {"label": test, "value": test} for test in ["CMJ", "CMJR"]
                        ],
                        placeholder="Select test type",
                    ),
                    html.P("Comparison Group"),
                    dcc.Dropdown(
                        id="comparison-group-dropdown",
                        options=[
                            {"label": group, "value": group}
                            for group in ["1", "2", "3"]
                        ],
                    ),
                    html.Hr(),
                    html.P(id="total-tests-text", children="Total Tests Available: —"),
                ],
            ),
            # ====================== Performance Outputs (Gauge Clusters) ===================================
            html.Div(
                style={"gridArea": "gauges"},
                children=[
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "16px"},
                        children=[
                            html.H3(
                                "Performance Outputs",
                                style={"textAlign": "center", "marginBottom": "8px"},
                            ),
                            html.Div(
                                style=GAUGE_CLUSTER_STYLE,
                                children=[
                                    html.Div(
                                        dcc.Graph(
                                            id=f"gauge-{gauge_id}",
                                            figure=create_gauge(50, title),
                                            config={"displayModeBar": False},
                                        ),
                                        style={"width": "200px"},
                                    )
                                    for gauge_id, title, _col in GAUGE_CONFIG
                                ],
                            ),
                        ],
                    ),
                    # ====================== Movement Analysis ===================================
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "16px"},
                        children=[
                            html.H3(
                                "Movement Analysis",
                                style={"textAlign": "center", "marginBottom": "8px"},
                            ),
                            # Legend
                            html.Div(
                                style={
                                    "display": "flex",
                                    "justifyContent": "center",
                                    "gap": "24px",
                                    "marginBottom": "12px",
                                },
                                children=[
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "gap": "6px",
                                        },
                                        children=[
                                            html.Div(
                                                style={
                                                    "width": "14px",
                                                    "height": "14px",
                                                    "backgroundColor": "#4a90d9",
                                                    "borderRadius": "2px",
                                                }
                                            ),
                                            html.Span(
                                                "Selected Test",
                                                style={"fontSize": "12px"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "gap": "6px",
                                        },
                                        children=[
                                            html.Div(
                                                style={
                                                    "width": "14px",
                                                    "height": "14px",
                                                    "backgroundColor": "#7ec67e",
                                                    "borderRadius": "2px",
                                                }
                                            ),
                                            html.Span(
                                                "Athlete Avg",
                                                style={"fontSize": "12px"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "gap": "6px",
                                        },
                                        children=[
                                            html.Div(
                                                style={
                                                    "width": "14px",
                                                    "height": "14px",
                                                    "backgroundColor": "#d9534f",
                                                    "borderRadius": "2px",
                                                }
                                            ),
                                            html.Span(
                                                "Team Avg", style={"fontSize": "12px"}
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(3, 1fr)",
                                    "gap": "8px",
                                },
                                children=[
                                    html.Div(
                                        dcc.Graph(
                                            id=f"bar-{bar_id}",
                                            figure=_default_bar,
                                            config={"displayModeBar": False},
                                        ),
                                    )
                                    for bar_id, _title, _col, _unit in BAR_CONFIG
                                ],
                            ),
                        ],
                    ),
                    # ====================== Injury Risk Assesment ===================================
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "16px"},
                        children=[
                            html.H3(
                                "Injury Risk Assesment",
                                style={"textAlign": "center", "marginBottom": "8px"},
                            ),
                            html.Div(
                                style={"display": "inline-block", "minWidth": "160px"},
                                children=[
                                    html.P("Test Date"),
                                    dcc.Dropdown(
                                        id="injury-date-dropdown",
                                        options=[],
                                        placeholder="Select Date",
                                    ),
                                ],
                            ),
                            dcc.Graph(
                                id="injury-diverging-chart",
                                figure=_default_diverging,
                                config={"displayModeBar": False},
                            ),
                            html.P(
                                "Over 25% recommends a deeper dive, 12-25% place on monitoring.",
                                style={
                                    "textAlign": "center",
                                    "fontStyle": "italic",
                                    "color": "#666",
                                    "marginTop": "10px",
                                },
                            ),
                            html.Hr(),
                            html.Div(
                                id="injury-data-display",
                                style={"padding": "8px"},
                                children=[
                                    html.P("Time to Stabilization: —"),
                                    html.P("Rebound CM Depth: —"),
                                    html.P("Relative Peak Landing Force: —"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


# ====================== Callbacks ===================================
@callback(
    Output("date-dropdown", "options"),
    Output("date-dropdown", "value"),
    Output("total-tests-text", "children"),
    Input("athlete-dropdown", "value"),
)
def update_date_dropdown(selected_name):
    """Populate test date dropdown based on selected athlete.

    Uses ISO date as the value (for DB queries) and MM-DD-YYYY as the label.
    """
    if not selected_name:
        return [], None, "Total Tests Available: —"
    dates = q.get_test_dates(selected_name)
    default_value = dates[0]["value"] if dates else None
    return dates, default_value, f"Total Tests Available: {len(dates)}"


@callback(
    [Output(f"gauge-{gauge_id}", "figure") for gauge_id, _, _ in GAUGE_CONFIG],
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_gauges(selected_name, selected_date):
    """Update all 5 gauge figures when athlete or date changes."""
    if not selected_name or not selected_date:
        return [create_gauge(50, title) for _, title, _ in GAUGE_CONFIG]

    test_data = q.get_test_data(selected_name, selected_date)
    if not test_data:
        return [create_gauge(50, title) for _, title, _ in GAUGE_CONFIG]

    # Get baseline (earliest test) for this athlete — independent of selected date
    baseline_data = q.get_baseline_data(selected_name)

    figures = []
    for _gauge_id, title, col in GAUGE_CONFIG:
        stats = population_stats.get(col, {"mean": 0, "std": 1})

        # Current test value
        raw_value = test_data.get(col)
        scaled = (
            scale_to_gauge(float(raw_value), stats["mean"], stats["std"])
            if raw_value is not None
            else 50
        )

        # Baseline value (earliest test)
        baseline_raw = baseline_data.get(col) if baseline_data else None
        baseline_scaled = (
            scale_to_gauge(float(baseline_raw), stats["mean"], stats["std"])
            if baseline_raw is not None
            else None
        )

        figures.append(create_gauge(scaled, title, baseline=baseline_scaled))

    return figures


@callback(
    [Output(f"bar-{bar_id}", "figure") for bar_id, _, _, _ in BAR_CONFIG],
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_bars(selected_name, selected_date):
    """Update all Movement Analysis bar charts when athlete or date changes."""
    if not selected_name or not selected_date:
        return [
            create_bar_chart(0, 0, 0, title, unit) for _, title, _, unit in BAR_CONFIG
        ]

    test_data = q.get_test_data(selected_name, selected_date)
    athlete_avg = q.get_athlete_average(selected_name)

    figures = []
    for _bar_id, title, col, unit in BAR_CONFIG:
        athlete_value = test_data.get(col)
        avg_value = athlete_avg.get(col)
        team_value = team_averages.get(col)

        figures.append(
            create_bar_chart(
                float(athlete_value) if athlete_value is not None else None,
                float(avg_value) if avg_value is not None else None,
                float(team_value) if team_value is not None else None,
                title,
                unit,
            )
        )

    return figures


@callback(
    Output("injury-date-dropdown", "options"),
    Output("injury-date-dropdown", "value"),
    Input("athlete-dropdown", "value"),
)
def update_injury_date_dropdown(selected_name):
    """Populate injury risk date dropdown from tests_cmj dates."""
    if not selected_name:
        return [], None
    dates = q.get_cmj_test_dates(selected_name)
    default_value = dates[0]["value"] if dates else None
    return dates, default_value


@callback(
    Output("injury-diverging-chart", "figure"),
    Input("athlete-dropdown", "value"),
    Input("injury-date-dropdown", "value"),
)
def update_injury_chart(selected_name, selected_date):
    """Update the injury risk diverging chart when athlete or date changes."""
    if not selected_name or not selected_date:
        return _default_diverging

    baseline_data = q.get_cmj_baseline_asymmetry(selected_name)
    if not baseline_data:
        return _default_diverging

    selected_data = q.get_cmj_date_asymmetry(selected_name, selected_date)
    return create_diverging_chart(baseline_data, selected_data)


@callback(
    Output("injury-data-display", "children"),
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_injury_data(selected_name, selected_date):
    """Update the injury data values below the diverging chart."""
    default = [
        html.P("Time to Stabilization: —"),
        html.P("Rebound CM Depth: —"),
        html.P("Relative Peak Landing Force: —"),
    ]
    if not selected_name or not selected_date:
        return default

    data = q.get_injury_data(selected_name, selected_date)
    if not data:
        return default

    tts = data.get("time_to_stabilization_ms")
    rcd = data.get("rebound_depth_m")
    rplf = data.get("relative_peak_landing_force")

    return [
        html.P(
            f"Time to Stabilization: {tts:.2f}"
            if tts is not None
            else "Time to Stabilization: —"
        ),
        html.P(
            f"Rebound CM Depth: {rcd:.2f}" if rcd is not None else "Rebound CM Depth: —"
        ),
        html.P(
            f"Relative Peak Landing Force: {rplf:.2f}"
            if rplf is not None
            else "Relative Peak Landing Force: —"
        ),
    ]


# ====================== Standalone App (for testing) ===================================
if __name__ == "__main__":
    app = Dash(__name__)
    app.layout = serve_layout()
    app.run(debug=True, port=8051)
