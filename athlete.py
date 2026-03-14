import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, Patch, callback, dcc, html

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
    ("cmj-braking-impulse", "CMJ Braking Impulse", "cmj_lr_braking_impulse_index"),
    (
        "cmj-propulsive-impulse",
        "CMJ Propulsive Impulse",
        "cmj_lr_propulsive_impulse_index",
    ),
    ("peak-landing-force", "Peak Landing Force", "lr_peak_landing_force"),
    (
        "rebound-braking-impulse",
        "Rebound Braking Impulse",
        "rebound_lr_braking_impulse_index",
    ),
    (
        "rebound-propulsive-impulse",
        "Rebound Propulsive Impulse",
        "rebound_lr_propulsive_impulse_index",
    ),
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

    # Always include baseline overlay trace for consistent Patch structure
    baseline_val = baseline if baseline is not None else 0
    baseline_color = "orange" if baseline is not None else "rgba(0,0,0,0)"
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
                    "line": {"color": baseline_color, "width": 2},
                    "thickness": 0.75,
                    "value": baseline_val,
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


def scale_to_gauge(value: float, mean: float, std: float, invert: bool = False) -> float:
    """Convert a raw metric value to a 0-100 gauge score via z-score.

    z=0 maps to 50, z=±3 maps to 0/100, clamped to [0, 100].
    invert: if True, negate z so that lower raw values score higher on the gauge.
    """
    z = (value - mean) / std
    if invert:
        z = -z
    scaled = 50 + (z / 3) * 50
    return max(0.0, min(100.0, round(scaled, 1)))


# ====================== Bar Graph Helper Function ===================================
def create_bar_chart(
    athlete_value: float | None,
    athlete_avg: float | None,
    team_avg: float | None,
    baseline: float | None,
    title: str,
    unit: str,
) -> go.Figure:
    """Create a grouped bar chart with 3 bars and a team avg line overlay."""
    bar_values = [
        athlete_value if athlete_value is not None else 0,
        athlete_avg if athlete_avg is not None else 0,
        baseline if baseline is not None else 0,
    ]
    bar_labels = ["Current Test", "Last 5 Avg", "Baseline"]
    bar_colors = ["#4a90d9", "#7ec67e", "#f0ad4e"]

    team_avg_val = team_avg if team_avg is not None else 0

    fig = go.Figure(
        data=[
            go.Bar(
                x=bar_labels,
                y=bar_values,
                marker_color=bar_colors,
                text=[f"{v:.2f}" for v in bar_values],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=14, color="white", family="Arial Black"),
            )
        ]
    )

    # Team avg as a horizontal line spanning the full chart
    fig.add_hline(
        y=team_avg_val,
        line_dash="dash",
        line_color="#d9534f",
        line_width=2,
        annotation_text=f"Team Avg: {team_avg_val:.2f}",
        annotation_position="top right",
        annotation_font_size=11,
        annotation_font_color="#d9534f",
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


_default_bar = create_bar_chart(0, 0, 0, 0, "—", "")
_default_bars = {
    bar_id: create_bar_chart(0, 0, 0, 0, title, unit)
    for bar_id, title, _col, unit in BAR_CONFIG
}


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
                marker=dict(color="#f0ad4e", opacity=0.45),
                text=[f"{v:.2f}" for v in baseline_vals],
                textposition="auto",
                textfont=dict(size=14),
            )
        )
        # Selected test trace (solid, on top) — color by severity
        selected_colors = []
        for v in selected_vals:
            abs_v = abs(v)
            if abs_v < 11:
                selected_colors.append("#7ec67e")
            elif abs_v < 25:
                selected_colors.append("#f5e642")
            else:
                selected_colors.append("#d9534f")
        fig.add_trace(
            go.Bar(
                y=labels,
                x=selected_vals,
                orientation="h",
                name="Current Test",
                marker_color=selected_colors,
                text=[f"{v:.2f}" for v in selected_vals],
                textposition="auto",
                textfont=dict(size=14),
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
                marker_color="#f0ad4e",
                text=[f"{v:.2f}" for v in baseline_vals],
                textposition="auto",
                textfont=dict(size=14),
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
        height=450,
        xaxis=dict(
            range=[-x_range, x_range],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="black",
            gridcolor="lightgray",
            title="Asymmetry",
        ),
        yaxis=dict(autorange="reversed", tickfont=dict(size=14)),
        legend=dict(
            orientation="h", x=0.5, xanchor="center", yanchor="bottom", y=-0.55
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=50, b=60),
    )
    return fig


_default_diverging = create_diverging_chart({}, {})


# ====================== Trend Chart Helper Function ===================================
# Combines gauge and bar metrics for the Trends container
TREND_CONFIG = [
    (gid, title, col) for gid, title, col in GAUGE_CONFIG
] + [
    (bid, title, col) for bid, title, col, _unit in BAR_CONFIG
] + [
    ("rebound-cm-depth", "Rebound CM Depth", "rebound_depth_m"),
    ("time-to-stabilization", "Time to Stabilization", "time_to_stabilization_ms"),
    ("rel-peak-landing-force", "Relative Peak Landing Force", "relative_peak_landing_force"),
]


def create_trend_chart(dates, values, title: str) -> go.Figure:
    """Create a scatter plot with highlighted baseline/current and a trend line.

    dates: list of datetime.date objects (ascending)
    values: list of float metric values
    """
    fig = go.Figure()

    if not dates:
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor="center", font=dict(size=13)),
            height=250,
            margin=dict(l=40, r=20, t=50, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    n = len(dates)
    # Last 5 tests *before* the current (most recent) one
    last5_end = n - 1  # exclusive — stop before current
    last5_start = max(0, last5_end - 5)

    # Shaded band for last-5 test window (only if there are tests before current)
    if last5_end > last5_start:
        fig.add_vrect(
            x0=dates[last5_start],
            x1=dates[last5_end - 1],
            fillcolor="#4a90d9",
            opacity=0.08,
            line_width=0,
            annotation_text="Last 5",
            annotation_position="top left",
            annotation_font_size=9,
            annotation_font_color="#4a90d9",
        )

    # All data points (regular markers)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="markers",
            name="Tests",
            marker=dict(color="#4a90d9", size=7),
        )
    )

    # Baseline highlight (first point)
    fig.add_trace(
        go.Scatter(
            x=[dates[0]],
            y=[values[0]],
            mode="markers+text",
            name="Baseline",
            marker=dict(
                color="#f0ad4e", size=13, symbol="diamond",
                line=dict(color="white", width=1.5),
            ),
            text=["Baseline"],
            textposition="top center",
            textfont=dict(size=9, color="#f0ad4e"),
        )
    )

    # Most recent highlight (last point)
    if n > 1:
        fig.add_trace(
            go.Scatter(
                x=[dates[-1]],
                y=[values[-1]],
                mode="markers+text",
                name="Current",
                marker=dict(
                    color="#5cb85c", size=13, symbol="star",
                    line=dict(color="white", width=1.5),
                ),
                text=["Current"],
                textposition="top center",
                textfont=dict(size=9, color="#5cb85c"),
            )
        )

    # Linear trend line (needs at least 2 points)
    if n >= 2:
        x_numeric = np.arange(n, dtype=float)
        y_arr = np.array(values, dtype=float)
        coeffs = np.polyfit(x_numeric, y_arr, 1)
        trend_y = np.polyval(coeffs, x_numeric)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=trend_y.tolist(),
                mode="lines",
                name="Trend",
                line=dict(color="#d9534f", width=2, dash="dash"),
            )
        )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=13)),
        height=250,
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis=dict(tickformat="%m/%d/%Y", tickfont=dict(size=9)),
        yaxis=dict(gridcolor="lightgray"),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


_default_trend = create_trend_chart([], [], "—")


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
    "gap": "48px",
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
                    html.Img(src="assets/Images/profile.jpg", style={"width": "250px"}),
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
                    html.P(id="athlete-weight", children="Weight: —"),
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
                                        [
                                            dcc.Graph(
                                                id=f"gauge-{gauge_id}",
                                                figure=create_gauge(50, title),
                                                config={"displayModeBar": False},
                                            ),
                                            html.P(
                                                _col,
                                                style={
                                                    "textAlign": "center",
                                                    "fontSize": "12px",
                                                    "margin": "0",
                                                },
                                            ),
                                            html.P(
                                                id=f"raw-{gauge_id}",
                                                children="—",
                                                style={
                                                    "textAlign": "center",
                                                    "fontSize": "16px",
                                                    "margin": "0",
                                                },
                                            ),
                                            html.P(
                                                id=f"pct-diff-{gauge_id}",
                                                children="",
                                                style={
                                                    "textAlign": "center",
                                                    "fontSize": "14px",
                                                    "margin": "4px auto 0",
                                                    "padding": "2px 8px",
                                                    "borderRadius": "4px",
                                                    "display": "inline-block",
                                                },
                                            ),
                                        ],
                                        style={"width": "200px", "textAlign": "center"},
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
                                                "Current Test",
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
                                                "Last 5 Avg",
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
                                                    "backgroundColor": "#f0ad4e",
                                                    "borderRadius": "2px",
                                                }
                                            ),
                                            html.Span(
                                                "Baseline",
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
                                                    "width": "20px",
                                                    "height": "0px",
                                                    "borderTop": "2px dashed #d9534f",
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
                                        [
                                            dcc.Graph(
                                                id=f"bar-{bar_id}",
                                                figure=_default_bars[bar_id],
                                                config={"displayModeBar": False},
                                            ),
                                            html.P(
                                                id=f"bar-pct-diff-{bar_id}",
                                                children="",
                                                style={
                                                    "textAlign": "center",
                                                    "fontSize": "14px",
                                                    "margin": "4px auto 0",
                                                    "padding": "2px 8px",
                                                    "borderRadius": "4px",
                                                    "display": "inline-block",
                                                },
                                            ),
                                        ],
                                        style={"textAlign": "center"},
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
                                    html.P("Relative Peak Landing Force: —"),
                                ],
                            ),
                        ],
                    ),
                    # ====================== Trends ===================================
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "16px"},
                        children=[
                            html.H3(
                                "Trends",
                                style={"textAlign": "center", "marginBottom": "8px"},
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
                                            id=f"trend-{trend_id}",
                                            figure=_default_trend,
                                            config={"displayModeBar": False},
                                        ),
                                    )
                                    for trend_id, _title, _col in TREND_CONFIG
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
    [Output(f"gauge-{gauge_id}", "figure") for gauge_id, _, _ in GAUGE_CONFIG]
    + [Output(f"raw-{gauge_id}", "children") for gauge_id, _, _ in GAUGE_CONFIG]
    + [Output(f"pct-diff-{gauge_id}", "children") for gauge_id, _, _ in GAUGE_CONFIG]
    + [Output(f"pct-diff-{gauge_id}", "style") for gauge_id, _, _ in GAUGE_CONFIG],
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_gauges(selected_name, selected_date):
    """Update all 5 gauge figures when athlete or date changes."""
    default_figs = [create_gauge(50, title) for _, title, _ in GAUGE_CONFIG]
    default_texts = ["—" for _ in GAUGE_CONFIG]
    default_pct_texts = ["" for _ in GAUGE_CONFIG]
    default_pct_styles = [{"display": "none"} for _ in GAUGE_CONFIG]

    if not selected_name or not selected_date:
        return default_figs + default_texts + default_pct_texts + default_pct_styles

    test_data = q.get_test_data(selected_name, selected_date)
    if not test_data:
        return default_figs + default_texts + default_pct_texts + default_pct_styles

    # Get baseline (earliest test) for this athlete — independent of selected date
    baseline_data = q.get_baseline_data(selected_name)

    figures = []
    raw_texts = []
    pct_texts = []
    pct_styles = []
    # Metrics where lower raw values are better (inverted z-score)
    INVERT_GAUGE = set()

    for _gauge_id, title, col in GAUGE_CONFIG:
        stats = population_stats.get(col, {"mean": 0, "std": 1})
        invert = col in INVERT_GAUGE

        # Current test value
        raw_value = test_data.get(col)
        scaled = (
            scale_to_gauge(float(raw_value), stats["mean"], stats["std"], invert=invert)
            if raw_value is not None
            else 50
        )

        # Baseline value (earliest test)
        baseline_raw = baseline_data.get(col) if baseline_data else None
        baseline_scaled = (
            scale_to_gauge(float(baseline_raw), stats["mean"], stats["std"], invert=invert)
            if baseline_raw is not None
            else None
        )

        figures.append(create_gauge(scaled, title, baseline=baseline_scaled))
        raw_texts.append(f"{float(raw_value):.2f}" if raw_value is not None else "—")

        # % difference: selected test vs baseline
        if raw_value is not None and baseline_raw is not None and float(baseline_raw) != 0:
            pct_signed = ((float(raw_value) - float(baseline_raw)) / abs(float(baseline_raw))) * 100
            pct_texts.append(f"{pct_signed:+.1f}%")

            base_style = {
                "textAlign": "center",
                "fontSize": "14px",
                "margin": "4px auto 0",
                "padding": "2px 8px",
                "borderRadius": "4px",
                "display": "inline-block",
                "fontWeight": "bold",
            }

            if pct_signed >= 5:
                pct_styles.append({**base_style, "backgroundColor": "#4a90d9", "color": "white"})
            elif pct_signed <= -10:
                pct_styles.append({**base_style, "backgroundColor": "#d9534f", "color": "white"})
            elif pct_signed <= -5:
                pct_styles.append({**base_style, "backgroundColor": "#f5e642", "color": "black"})
            else:
                # -4.99 to 4.99: no background
                pct_styles.append({**base_style, "color": "#666"})
        else:
            pct_texts.append("")
            pct_styles.append({"display": "none"})

    return figures + raw_texts + pct_texts + pct_styles


@callback(
    [Output(f"bar-{bar_id}", "figure") for bar_id, _, _, _ in BAR_CONFIG]
    + [Output(f"bar-pct-diff-{bar_id}", "children") for bar_id, _, _, _ in BAR_CONFIG]
    + [Output(f"bar-pct-diff-{bar_id}", "style") for bar_id, _, _, _ in BAR_CONFIG],
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_bars(selected_name, selected_date):
    """Update all Movement Analysis bar charts when athlete or date changes."""
    default_pct_texts = ["" for _ in BAR_CONFIG]
    default_pct_styles = [{"display": "none"} for _ in BAR_CONFIG]

    if not selected_name or not selected_date:
        return [
            create_bar_chart(0, 0, 0, 0, title, unit) for _, title, _, unit in BAR_CONFIG
        ] + default_pct_texts + default_pct_styles

    test_data = q.get_test_data(selected_name, selected_date)
    athlete_avg = q.get_athlete_average(selected_name)
    baseline_data = q.get_baseline_data(selected_name)
    figures = []
    pct_texts = []
    pct_styles = []
    for _bar_id, title, col, unit in BAR_CONFIG:
        athlete_value = test_data.get(col)
        avg_value = athlete_avg.get(col)
        team_value = team_averages.get(col)
        baseline_value = baseline_data.get(col) if baseline_data else None

        figures.append(
            create_bar_chart(
                float(athlete_value) if athlete_value is not None else None,
                float(avg_value) if avg_value is not None else None,
                float(team_value) if team_value is not None else None,
                float(baseline_value) if baseline_value is not None else None,
                title,
                unit,
            )
        )

        # % difference: selected test vs baseline
        # Invert for "lower is better" metrics
        lower_is_better = col == "rebound_contact_time_ms"
        if athlete_value is not None and baseline_value is not None and float(baseline_value) != 0:
            pct_signed = ((float(athlete_value) - float(baseline_value)) / float(baseline_value)) * 100
            if lower_is_better:
                pct_signed *= -1
            pct_texts.append(f"{pct_signed:+.1f}%")

            base_style = {
                "textAlign": "center",
                "fontSize": "14px",
                "margin": "4px auto 0",
                "padding": "2px 8px",
                "borderRadius": "4px",
                "display": "inline-block",
                "fontWeight": "bold",
            }

            if pct_signed >= 5:
                pct_styles.append({**base_style, "backgroundColor": "#4a90d9", "color": "white"})
            elif pct_signed <= -10:
                pct_styles.append({**base_style, "backgroundColor": "#d9534f", "color": "white"})
            elif pct_signed <= -5:
                pct_styles.append({**base_style, "backgroundColor": "#f5e642", "color": "black"})
            else:
                pct_styles.append({**base_style, "color": "#666"})
        else:
            pct_texts.append("")
            pct_styles.append({"display": "none"})

    return figures + pct_texts + pct_styles



@callback(
    Output("injury-diverging-chart", "figure"),
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
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
    Output("athlete-weight", "children"),
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_injury_data(selected_name, selected_date):
    """Update the injury data values below the diverging chart."""
    default = [
        html.P("Time to Stabilization: —"),
        html.P("Relative Peak Landing Force: —"),
    ]
    if not selected_name or not selected_date:
        return default, "Weight: —"

    data = q.get_injury_data(selected_name, selected_date)
    if not data:
        return default, "Weight: —"

    tts = data.get("time_to_stabilization_ms")
    rplf = data.get("relative_peak_landing_force")
    system_weight_n = data.get("system_weight_n")

    # Convert system weight from Newtons to kg and lbs
    weight_kg = float(system_weight_n) / 9.81 if system_weight_n is not None else None
    weight_lbs = weight_kg * 2.20462 if weight_kg is not None else None

    # Normalize peak landing force by body weight in kg
    rplf_normalized = (
        float(rplf) / weight_kg if rplf is not None and weight_kg else None
    )

    weight_text = f"Weight: {weight_lbs:.1f} lbs" if weight_lbs is not None else "Weight: —"

    return [
        html.P(
            f"Time to Stabilization: {tts:.2f}"
            if tts is not None
            else "Time to Stabilization: —"
        ),
        html.P(
            f"Relative Peak Landing Force: {rplf_normalized:.2f}"
            if rplf_normalized is not None
            else "Relative Peak Landing Force: —"
        ),
    ], weight_text


@callback(
    [Output(f"trend-{tid}", "figure") for tid, _, _ in TREND_CONFIG],
    Input("athlete-dropdown", "value"),
)
def update_trends(selected_name):
    """Update all Trend scatter plots when athlete changes."""
    defaults = [_default_trend for _ in TREND_CONFIG]
    if not selected_name:
        return defaults

    trend_rows = q.get_trend_data(selected_name)
    if not trend_rows:
        return defaults

    # Filter to: baseline (first), last 5 before current, and current (last)
    all_dates = [row["test_date"] for row in trend_rows]
    n = len(all_dates)

    if n <= 7:
        # 7 or fewer tests — keep all (baseline + up to 5 middle + current)
        filtered_rows = trend_rows
    else:
        # baseline (index 0) + last 5 before current (indices -6 to -2) + current (-1)
        filtered_rows = [trend_rows[0]] + trend_rows[-6:-1] + [trend_rows[-1]]

    dates = [row["test_date"] for row in filtered_rows]

    figures = []
    for _tid, title, col in TREND_CONFIG:
        values = [float(row.get(col) or 0) for row in filtered_rows]
        figures.append(create_trend_chart(dates, values, title))

    return figures


# ====================== Standalone App (for testing) ===================================
if __name__ == "__main__":
    app = Dash(__name__)
    app.layout = serve_layout()
    app.run(debug=True, port=8051)
