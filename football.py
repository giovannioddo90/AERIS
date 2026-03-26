import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, Patch, callback, dcc, html

import models.queries as q

from models.config import (
    FOOTBALL_INJURY_CONFIG,
    OUTPUT_METRICS_CONFIG,
    FOOTBALL_OUTPUT_METRICS,
    FOOTBALL_MOVEMENT_ANALYSIS_COLUMNS,
    FOOTBALL_MOVEMENT_ANALYSIS_CONFIG,
)


# ====================== Z-Score helper function =====================================
def scale_to_z_score(
    value: float, mean: float, std: float, invert: bool = False
) -> float:
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
                textfont=dict(size=16, color="white", family="Arial Black"),
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
        annotation_font_size=12,
        annotation_font_color="#d9534f",
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=13)),
        height=160,
        margin=dict(l=25, r=8, t=30, b=20),
        yaxis=dict(title=unit, gridcolor="lightgray", tickfont=dict(size=10)),
        xaxis=dict(tickfont=dict(size=10)),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.2,
    )
    return fig


_default_bar = create_bar_chart(0, 0, 0, 0, "—", "")
_default_bars = {
    bar_id: create_bar_chart(0, 0, 0, 0, title, unit)
    for bar_id, title, _col, unit in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG
}


# ====================== Z-Score Bar Chart Helper Function =================================
def create_zscore_bar(
    z_current: float | None,
    z_baseline: float | None,
    title: str,
) -> go.Figure:
    """Create a bar chart showing the current test z-score (0-100 scale)
    with a baseline z-score as an orange horizontal line."""
    bar_values = [z_current if z_current is not None else 0]
    bar_labels = ["Current Test"]
    bar_colors = ["#4a90d9"]

    baseline_val = z_baseline if z_baseline is not None else 0

    fig = go.Figure(
        data=[
            go.Bar(
                x=bar_labels,
                y=bar_values,
                marker_color=bar_colors,
                text=[f"{v:.1f}" for v in bar_values],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=16, color="white", family="Arial Black"),
                width=[0.4],
            )
        ]
    )

    # Baseline as an orange horizontal line
    fig.add_hline(
        y=baseline_val,
        line_dash="dash",
        line_color="#c07d20",
        line_width=2,
        annotation_text=f"Baseline: {baseline_val:.1f}",
        annotation_position="top right",
        annotation_font_size=12,
        annotation_font_color="#c07d20",
    )

    # Team average z-score is always 50 (population mean = team mean)
    fig.add_hline(
        y=50,
        line_dash="longdashdot",
        line_color="#d9534f",
        line_width=2,
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=12)),
        height=160,
        margin=dict(l=25, r=8, t=30, b=20),
        yaxis=dict(title="Z-Score", gridcolor="lightgray", range=[0, 100], tickfont=dict(size=10)),
        xaxis=dict(tickfont=dict(size=10), visible=False),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.2,
    )

    # Percentile reference bands (appended after hlines so shapes[0] and [1] stay intact)
    # Percentile boundaries converted to 0-100 scale via z-scores
    p2 = 15.8  # 2nd percentile  (z ≈ -2.05)
    p15 = 32.7  # 15th percentile (z ≈ -1.04)
    p85 = 67.3  # 85th percentile (z ≈  1.04)
    p98 = 84.2  # 98th percentile (z ≈  2.05)

    bands = [
        (0, p2, "rgba(217,83,79,0.3)"),  # 0-2nd: red
        (p2, p15, "rgba(255,235,59,0.3)"),  # 2-15th: yellow
        (p15, p85, "rgba(144,238,144,0.3)"),  # 16-84th: green
        (p85, p98, "rgba(60,179,113,0.35)"),  # 85-97th: darker green
        (p98, 100, "rgba(34,120,60,0.4)"),  # 98-100th: dark green
    ]
    for y0, y1, color in bands:
        fig.add_shape(
            type="rect",
            xref="paper",
            x0=0,
            x1=1,
            yref="y",
            y0=y0,
            y1=y1,
            fillcolor=color,
            line_width=0,
            layer="below",
        )

    return fig


_default_zscore_bars = {
    bar_id: create_zscore_bar(0, 0, title)
    for bar_id, title, _col in OUTPUT_METRICS_CONFIG
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
    labels = [title for _, title, _ in FOOTBALL_INJURY_CONFIG]
    cols = [col for _, _, col in FOOTBALL_INJURY_CONFIG]

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
                textfont=dict(size=18),
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
                textfont=dict(size=18),
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
                textfont=dict(size=18),
            )
        )

    # Determine symmetric x-axis range
    all_vals = baseline_vals + (
        [float(selected_data.get(c) or 0) for c in cols] if selected_data else []
    )
    max_abs = max(abs(v) for v in all_vals) if all_vals else 1
    x_range = max(max_abs * 1.3, 0.1)

    fig.update_layout(
        title=dict(text="Asymmetry Analysis", x=0.5, xanchor="center", font=dict(size=18)),
        barmode="group",
        height=360,
        xaxis=dict(
            range=[-x_range, x_range],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="black",
            gridcolor="lightgray",
            title="Asymmetry",
            tickfont=dict(size=14),
        ),
        yaxis=dict(autorange="reversed", tickfont=dict(size=16)),
        legend=dict(
            orientation="h", x=0.5, xanchor="center", yanchor="bottom", y=-0.35,
            font=dict(size=14),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=40, b=50),
    )
    return fig


_default_diverging = create_diverging_chart({}, {})


# =============== Startup data ==================================
dropdown_names = q.get_football_athlete_names()
team_averages = q.get_team_average(
    FOOTBALL_OUTPUT_METRICS + FOOTBALL_MOVEMENT_ANALYSIS_COLUMNS, "tests_cmj"
)
cmj_pop_stats = q.get_population_stats(FOOTBALL_OUTPUT_METRICS, "tests_cmj")

# ====================== Styling ===================================
CARD_STYLE = {
    "backgroundColor": "#e2efe2",
    "borderRadius": "12px",
    "padding": "10px",
    "boxShadow": "0 4px 10px rgba(0,0,0,0.08)",
}


def serve_layout():
    """Returns the page layout"""
    return html.Div(
        className="card-container",
        style={
            "display": "grid",
            "gridTemplateColumns": "280px 1fr",
            "gridTemplateRows": "auto",
            "gridTemplateAreas": """
                'profile metrics'
            """,
            "gap": "10px",
            "padding": "10px",
            "minHeight": "auto",
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
                    html.P("Sport: Football"),
                    html.P("Position: OL"),
                    html.P("Team: UPHS"),
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
            # ====================== Metric's Grid ===================================
            html.Div(
                style={"gridArea": "metrics"},
                children=[
                    # ==================== Performance Outputs ===================================
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "8px"},
                        children=[
                            html.H3(
                                "Performance Outputs",
                                style={"textAlign": "center", "marginBottom": "8px"},
                            ),
                            # Shared legend
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
                                                    "width": "20px",
                                                    "height": "0px",
                                                    "borderTop": "2px dashed #c07d20",
                                                }
                                            ),
                                            html.Span(
                                                "Baseline", style={"fontSize": "12px"}
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
                                    "gridTemplateColumns": "repeat(5, 1fr)",
                                    "gap": "4px",
                                },
                                children=[
                                    html.Div(
                                        dcc.Graph(
                                            id=f"zscore-bar-{bar_id}",
                                            figure=_default_zscore_bars[bar_id],
                                            config={"displayModeBar": False},
                                        ),
                                        style={"textAlign": "center"},
                                    )
                                    for bar_id, _title, _col in OUTPUT_METRICS_CONFIG
                                ],
                            ),
                        ],
                    ),
                    # ====================== Movement Analysis ===================================
                    html.Div(
                        style={**CARD_STYLE, "marginBottom": "8px"},
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
                                    for bar_id, _title, _col, _unit in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG
                                ],
                            ),
                        ],
                    ),
                    # ====================== Injury Risk Assesment ===================================
                    html.Div(
                        style={**CARD_STYLE},
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
    dates = q.get_cmj_test_dates(selected_name)
    default_value = dates[0]["value"] if dates else None
    return dates, default_value, f"Total Tests Available: {len(dates)}"


@callback(
    [
        Output(f"zscore-bar-{bar_id}", "figure")
        for bar_id, _, _ in OUTPUT_METRICS_CONFIG
    ],
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_zscore_bars(selected_name, selected_date):
    """Update Performance Output z-score bars when athlete or date changes."""
    defaults = [_default_zscore_bars[bar_id] for bar_id, _, _ in OUTPUT_METRICS_CONFIG]
    if not selected_name or not selected_date:
        return defaults

    test_data = q.get_cmj_test_data(selected_name, selected_date)
    baseline_data = q.get_cmj_baseline_data(selected_name)
    if not test_data:
        return defaults

    figures = []
    for bar_id, title, col in OUTPUT_METRICS_CONFIG:
        raw_value = test_data.get(col)
        raw_baseline = baseline_data.get(col) if baseline_data else None
        stats = cmj_pop_stats.get(col, {})
        mean = stats.get("mean")
        std = stats.get("std")

        if raw_value is not None and mean is not None and std is not None:
            z_current = scale_to_z_score(float(raw_value), mean, std)
        else:
            z_current = 0

        if raw_baseline is not None and mean is not None and std is not None:
            z_baseline = scale_to_z_score(float(raw_baseline), mean, std)
        else:
            z_baseline = 0

        patched = Patch()
        patched["data"][0]["y"] = [z_current]
        patched["data"][0]["text"] = [f"{z_current:.1f}"]
        # Update baseline hline
        patched["layout"]["shapes"][0]["y0"] = z_baseline
        patched["layout"]["shapes"][0]["y1"] = z_baseline
        patched["layout"]["annotations"][0]["text"] = f"Baseline: {z_baseline:.1f}"
        figures.append(patched)

    return figures


@callback(
    [
        Output(f"bar-{bar_id}", "figure")
        for bar_id, _, _, _ in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG
    ]
    + [
        Output(f"bar-pct-diff-{bar_id}", "children")
        for bar_id, _, _, _ in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG
    ]
    + [
        Output(f"bar-pct-diff-{bar_id}", "style")
        for bar_id, _, _, _ in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG
    ],
    Input("athlete-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_bars(selected_name, selected_date):
    """Update all Movement Analysis bar charts when athlete or date changes."""
    default_pct_texts = ["" for _ in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG]
    default_pct_styles = [
        {"display": "none"} for _ in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG
    ]

    if not selected_name or not selected_date:
        return (
            [
                _default_bars[bar_id]
                for bar_id, _, _, _ in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG
            ]
            + default_pct_texts
            + default_pct_styles
        )

    test_data = q.get_cmj_test_data(selected_name, selected_date)
    athlete_avg = q.get_cmj_athlete_average(selected_name)
    baseline_data = q.get_cmj_baseline_data(selected_name)
    figures = []
    pct_texts = []
    pct_styles = []
    for _bar_id, title, col, unit in FOOTBALL_MOVEMENT_ANALYSIS_CONFIG:
        athlete_value = float(test_data.get(col) or 0)
        avg_value = float(athlete_avg.get(col) or 0)
        team_value = float(team_averages.get(col) or 0)
        baseline_value = float(baseline_data.get(col) or 0) if baseline_data else 0

        bar_values = [athlete_value, avg_value, baseline_value]

        # Patch only the changed values instead of rebuilding the full figure
        patched = Patch()
        patched["data"][0]["y"] = bar_values
        patched["data"][0]["text"] = [f"{v:.2f}" for v in bar_values]
        # Update team avg hline position and annotation
        patched["layout"]["shapes"][0]["y0"] = team_value
        patched["layout"]["shapes"][0]["y1"] = team_value
        patched["layout"]["annotations"][0]["text"] = f"Team Avg: {team_value:.2f}"
        figures.append(patched)

        # % difference: selected test vs baseline
        # Invert for "lower is better" metrics
        raw_athlete = test_data.get(col)
        raw_baseline = baseline_data.get(col) if baseline_data else None
        lower_is_better = False
        if (
            raw_athlete is not None
            and raw_baseline is not None
            and float(raw_baseline) != 0
        ):
            pct_signed = (
                (float(raw_athlete) - float(raw_baseline)) / float(raw_baseline)
            ) * 100
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
                pct_styles.append(
                    {**base_style, "backgroundColor": "#4a90d9", "color": "white"}
                )
            elif pct_signed <= -10:
                pct_styles.append(
                    {**base_style, "backgroundColor": "#d9534f", "color": "white"}
                )
            elif pct_signed <= -5:
                pct_styles.append(
                    {**base_style, "backgroundColor": "#f5e642", "color": "black"}
                )
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
        return default

    data = q.get_football_injury_data(selected_name, selected_date)

    tts = data.get("time_to_stabilization_ms")
    rplf = data.get("relative_peak_landing_force")

    return [
        html.P(
            f"Time to Stabilization: {tts:.2f}"
            if tts is not None
            else "Time to Stabilization: —"
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
