import plotly.graph_objects as go
from dash import Dash, dcc, html


# ====================== Color Palette & Theme ===================================
COLORS = {
    "bg_primary": "#ffffff",
    "bg_card": "#f8f9fb",
    "bg_card_alt": "#f0f2f5",
    "accent_blue": "#2563eb",
    "accent_cyan": "#0891b2",
    "accent_green": "#16a34a",
    "accent_amber": "#d97706",
    "accent_red": "#dc2626",
    "accent_purple": "#7c3aed",
    "text_primary": "#1e293b",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "border": "#e2e8f0",
    "grid": "#f1f5f9",
    "right_bar": "#2563eb",
    "left_bar": "#ea580c",
}

FONT_HEADING = "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif"
FONT_BODY = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif"
FONT_MONO = "'DM Mono', 'Roboto Mono', monospace"

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Plus+Jakarta+Sans:wght@500;600;700;800"
    "&family=Inter:wght@400;500;600;700"
    "&family=DM+Mono:wght@400;500"
    "&display=swap"
)

PLOTLY_LAYOUT_BASE = dict(
    font=dict(family=FONT_BODY, color=COLORS["text_primary"]),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=50, r=20, t=45, b=40),
)


# ====================== Z-Score Scaling ===================================
def scale_to_zscore(value: float, mean: float, std: float, invert: bool = False) -> float:
    z = (value - mean) / std
    if invert:
        z = -z
    scaled = 50 + (z / 3) * 50
    return max(0.0, min(100.0, round(scaled, 1)))


# ====================== Mock Data ===================================
GRIP_DATA = {
    "Peak Force": {"right": 208.82, "left": 196.69, "unit": "N"},
    "Time to Peak Force": {"right": 2.857, "left": 0.703, "unit": "s"},
    "Avg. Net Force": {"right": 175.39, "left": 164.19, "unit": "N"},
    "Net Impulse": {"right": 877, "left": 821, "unit": "N·s"},
}

GRIP_POPULATION_STATS = {
    "Peak Force": {"mean": 195.0, "std": 25.0, "invert": False},
    "Time to Peak Force": {"mean": 1.8, "std": 0.9, "invert": True},
    "Avg. Net Force": {"mean": 160.0, "std": 22.0, "invert": False},
    "Net Impulse": {"mean": 840.0, "std": 60.0, "invert": False},
}

ASYMMETRY_DATA = {
    "CMJ Braking Impulse": -8.4,
    "CMJ Propulsive Impulse": 12.7,
    "Peak Landing Force": -6.2,
    "Rebound Braking Impulse": 18.3,
    "Rebound Propulsive Impulse": -3.1,
}

KPI_DATA = [
    {"label": "Peak Force (R)", "value": "208.82", "unit": "N", "delta": "+5.98%", "status": "normal"},
    {"label": "Peak Force (L)", "value": "196.69", "unit": "N", "delta": "—", "status": "normal"},
    {"label": "Side-Side Diff", "value": "5.98", "unit": "%", "delta": "", "status": "caution"},
    {"label": "Net Impulse (R)", "value": "877", "unit": "N·s", "delta": "+6.6%", "status": "normal"},
]


# ====================== Chart Builders ===================================
def create_grip_comparison_bar(metric: str, right_zscore: float, left_zscore: float) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=["Right", "Left"],
        y=[right_zscore, left_zscore],
        marker=dict(
            color=[COLORS["right_bar"], COLORS["left_bar"]],
            line=dict(width=0),
        ),
        text=[f"{right_zscore:.1f}", f"{left_zscore:.1f}"],
        textposition="outside",
        textfont=dict(size=14, color=COLORS["text_primary"], family=FONT_MONO),
        width=0.5,
    ))

    pct_diff = abs(right_zscore - left_zscore)
    diff_color = COLORS["accent_green"] if pct_diff < 10 else (
        COLORS["accent_amber"] if pct_diff < 25 else COLORS["accent_red"]
    )

    fig.add_hline(
        y=50, line_dash="dot", line_color=COLORS["text_muted"],
        line_width=1, opacity=0.5,
    )

    fig.update_layout(
        **PLOTLY_LAYOUT_BASE,
        title=dict(
            text=f"<b>{metric}</b>",
            x=0.5,
            xanchor="center",
            font=dict(size=14, color=COLORS["text_primary"]),
        ),
        height=260,
        yaxis=dict(
            title="Z-Score (0–100)",
            gridcolor=COLORS["grid"],
            zeroline=False,
            range=[0, 105],
            tickfont=dict(size=11, color=COLORS["text_secondary"]),
            title_font=dict(size=10, color=COLORS["text_muted"]),
        ),
        xaxis=dict(
            tickfont=dict(size=12, color=COLORS["text_secondary"]),
        ),
        showlegend=False,
        bargap=0.35,
        annotations=[
            dict(
                text=f"<b>{pct_diff:.1f} pt diff</b>",
                x=0.5,
                y=100,
                xref="paper",
                yref="y",
                showarrow=False,
                font=dict(size=11, color=diff_color),
            )
        ],
    )
    return fig


def create_asymmetry_chart(data: dict) -> go.Figure:
    metrics = list(data.keys())
    values = list(data.values())

    bar_colors = []
    for v in values:
        abs_v = abs(v)
        if abs_v < 10:
            bar_colors.append(COLORS["accent_green"])
        elif abs_v < 25:
            bar_colors.append(COLORS["accent_amber"])
        else:
            bar_colors.append(COLORS["accent_red"])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=metrics,
        x=values,
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(width=0),
        ),
        text=[f"{v:.1f}%" for v in values],
        textposition="outside",
        textfont=dict(size=13, color=COLORS["text_primary"], family=FONT_MONO),
    ))

    max_abs = max(abs(v) for v in values) if values else 1
    x_range = max(max_abs * 1.4, 15)

    fig.add_vline(x=10, line_dash="dot", line_color=COLORS["accent_amber"], line_width=1, opacity=0.5)
    fig.add_vline(x=-10, line_dash="dot", line_color=COLORS["accent_amber"], line_width=1, opacity=0.5)
    fig.add_vline(x=25, line_dash="dot", line_color=COLORS["accent_red"], line_width=1, opacity=0.4)
    fig.add_vline(x=-25, line_dash="dot", line_color=COLORS["accent_red"], line_width=1, opacity=0.4)

    fig.add_vrect(x0=-10, x1=10, fillcolor=COLORS["accent_green"], opacity=0.08, line_width=0)

    base_layout = {**PLOTLY_LAYOUT_BASE, "margin": dict(l=140, r=60, t=50, b=50)}
    fig.update_layout(
        **base_layout,
        title=dict(
            text="<b>CMJ Bilateral Leg Asymmetry</b>",
            x=0.5,
            xanchor="center",
            font=dict(size=16, color=COLORS["text_primary"]),
        ),
        height=320,
        xaxis=dict(
            range=[-x_range, x_range],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor=COLORS["text_muted"],
            gridcolor=COLORS["grid"],
            title="Asymmetry (%)",
            title_font=dict(size=12, color=COLORS["text_secondary"]),
            tickfont=dict(size=11, color=COLORS["text_secondary"]),
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=13, color=COLORS["text_primary"]),
        ),
        showlegend=False,
        annotations=[
            dict(
                text="<i>Normal</i>",
                x=0,
                y=-0.18,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=10, color=COLORS["accent_green"]),
            ),
            dict(
                text="<i>Monitor</i>",
                x=0.85,
                y=-0.18,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=10, color=COLORS["accent_amber"]),
            ),
            dict(
                text="<i>Flag</i>",
                x=1.0,
                y=-0.18,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=10, color=COLORS["accent_red"]),
            ),
        ],
    )
    return fig


# ====================== Layout Component Builders ===================================
CARD_STYLE = {
    "backgroundColor": COLORS["bg_card"],
    "borderRadius": "10px",
    "padding": "20px",
    "border": f"1px solid {COLORS['border']}",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
}

CARD_STYLE_ALT = {
    **CARD_STYLE,
    "backgroundColor": COLORS["bg_card_alt"],
}


def kpi_card(label: str, value: str, unit: str, delta: str, status: str) -> html.Div:
    status_colors = {
        "good": COLORS["accent_green"],
        "caution": COLORS["accent_amber"],
        "bad": COLORS["accent_red"],
        "normal": COLORS["accent_blue"],
    }
    accent = status_colors.get(status, COLORS["accent_blue"])

    children = [
        html.P(label, style={
            "margin": "0",
            "fontSize": "11px",
            "fontWeight": "500",
            "color": COLORS["text_secondary"],
            "textTransform": "uppercase",
            "letterSpacing": "0.05em",
        }),
        html.Div(style={"display": "flex", "alignItems": "baseline", "gap": "4px", "marginTop": "6px"}, children=[
            html.Span(value, style={
                "fontSize": "28px",
                "fontWeight": "700",
                "fontFamily": FONT_MONO,
                "color": COLORS["text_primary"],
                "lineHeight": "1",
            }),
            html.Span(unit, style={
                "fontSize": "13px",
                "color": COLORS["text_muted"],
                "fontWeight": "400",
            }),
        ]),
    ]

    if delta:
        children.append(
            html.Span(delta, style={
                "fontSize": "12px",
                "fontWeight": "600",
                "color": accent,
                "marginTop": "4px",
                "display": "inline-block",
            })
        )

    return html.Div(
        style={
            **CARD_STYLE,
            "borderTop": f"3px solid {accent}",
            "minWidth": "160px",
            "flex": "1",
        },
        children=children,
    )


def section_header(title: str, subtitle: str = "") -> html.Div:
    children = [
        html.H3(title, style={
            "margin": "0",
            "fontSize": "18px",
            "fontWeight": "700",
            "fontFamily": FONT_HEADING,
            "color": COLORS["text_primary"],
        }),
    ]
    if subtitle:
        children.append(
            html.P(subtitle, style={
                "margin": "4px 0 0 0",
                "fontSize": "13px",
                "color": COLORS["text_secondary"],
            })
        )
    return html.Div(style={"marginBottom": "16px"}, children=children)


def legend_item(color: str, label: str) -> html.Div:
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "8px"},
        children=[
            html.Div(style={
                "width": "12px",
                "height": "12px",
                "backgroundColor": color,
                "borderRadius": "3px",
            }),
            html.Span(label, style={"fontSize": "12px", "color": COLORS["text_secondary"]}),
        ],
    )


def severity_legend() -> html.Div:
    return html.Div(
        style={"display": "flex", "gap": "20px", "justifyContent": "center", "marginTop": "8px"},
        children=[
            legend_item(COLORS["accent_green"], "< 10% Normal"),
            legend_item(COLORS["accent_amber"], "10–25% Monitor"),
            legend_item(COLORS["accent_red"], "> 25% Flag"),
        ],
    )


# ====================== Build Charts ===================================
grip_chart_data = []
for metric, d in GRIP_DATA.items():
    stats = GRIP_POPULATION_STATS[metric]
    r_z = scale_to_zscore(d["right"], stats["mean"], stats["std"], stats["invert"])
    l_z = scale_to_zscore(d["left"], stats["mean"], stats["std"], stats["invert"])
    fig = create_grip_comparison_bar(metric, r_z, l_z)
    grip_chart_data.append({
        "figure": fig,
        "right_raw": d["right"],
        "left_raw": d["left"],
        "unit": d["unit"],
    })

asymmetry_chart = create_asymmetry_chart(ASYMMETRY_DATA)


# ====================== Page Layout ===================================
def serve_layout():
    return html.Div(
        className="main-container",
        style={
            "backgroundColor": COLORS["bg_primary"],
            "minHeight": "100vh",
            "fontFamily": FONT_BODY,
            "padding": "12px",
            "maxWidth": "100%",
            "margin": "0",
            "color": COLORS["text_primary"],
        },
        children=[
            # Header
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "marginBottom": "24px",
                    "paddingBottom": "16px",
                    "borderBottom": f"1px solid {COLORS['border']}",
                },
                children=[
                    html.Div(children=[
                        html.H1("Athlete Report", style={
                            "margin": "0",
                            "fontSize": "24px",
                            "fontWeight": "800",
                            "fontFamily": FONT_HEADING,
                            "color": COLORS["text_primary"],
                        }),
                        html.P("Bilateral Comparison Report", style={
                            "margin": "4px 0 0 0",
                            "fontSize": "14px",
                            "color": COLORS["text_secondary"],
                        }),
                    ]),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "16px"},
                        children=[
                            html.Div(children=[
                                html.P("Athlete", style={
                                    "margin": "0",
                                    "fontSize": "11px",
                                    "color": COLORS["text_muted"],
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.05em",
                                }),
                                html.P("Last, First", style={
                                    "margin": "2px 0 0 0",
                                    "fontSize": "15px",
                                    "fontWeight": "600",
                                    "fontFamily": FONT_HEADING,
                                    "color": COLORS["text_primary"],
                                }),
                            ]),
                            html.Div(style={
                                "width": "1px",
                                "height": "32px",
                                "backgroundColor": COLORS["border"],
                            }),
                            html.Div(children=[
                                html.P("Test Date", style={
                                    "margin": "0",
                                    "fontSize": "11px",
                                    "color": COLORS["text_muted"],
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.05em",
                                }),
                                html.P("04/01/2026", style={
                                    "margin": "2px 0 0 0",
                                    "fontSize": "15px",
                                    "fontWeight": "600",
                                    "color": COLORS["text_primary"],
                                }),
                            ]),
                            html.Div(style={
                                "width": "1px",
                                "height": "32px",
                                "backgroundColor": COLORS["border"],
                            }),
                            html.Div(children=[
                                html.P("Protocol", style={
                                    "margin": "0",
                                    "fontSize": "11px",
                                    "color": COLORS["text_muted"],
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.05em",
                                }),
                                html.P("Arm at Side, Best 2/3", style={
                                    "margin": "2px 0 0 0",
                                    "fontSize": "15px",
                                    "fontWeight": "600",
                                    "color": COLORS["text_primary"],
                                }),
                            ]),
                        ],
                    ),
                ],
            ),

            # Main Content Grid
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "20px",
                    "marginBottom": "24px",
                },
                children=[
                    # Left: Grip Comparison Charts (2x2 grid)
                    html.Div(
                        style=CARD_STYLE,
                        children=[
                            section_header(
                                "Left vs Right Comparison",
                                "Isometric grip strength by metric",
                            ),
                            html.Div(
                                style={
                                    "display": "flex",
                                    "gap": "16px",
                                    "justifyContent": "center",
                                    "marginBottom": "12px",
                                },
                                children=[
                                    legend_item(COLORS["right_bar"], "Right"),
                                    legend_item(COLORS["left_bar"], "Left"),
                                ],
                            ),
                            html.Div(
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "1fr 1fr",
                                    "gap": "8px",
                                },
                                children=[
                                    html.Div([
                                        dcc.Graph(
                                            figure=gd["figure"],
                                            config={"displayModeBar": False},
                                        ),
                                        html.Div(
                                            style={
                                                "display": "flex",
                                                "justifyContent": "space-around",
                                                "padding": "0 20px",
                                                "marginTop": "-4px",
                                            },
                                            children=[
                                                html.Div(style={"textAlign": "center"}, children=[
                                                    html.Span(f"{gd['right_raw']:.2f}", style={
                                                        "fontSize": "16px",
                                                        "fontWeight": "500",
                                                        "fontFamily": FONT_MONO,
                                                        "color": COLORS["right_bar"],
                                                    }),
                                                    html.Span(f" {gd['unit']}", style={
                                                        "fontSize": "11px",
                                                        "color": COLORS["text_muted"],
                                                    }),
                                                ]),
                                                html.Div(style={"textAlign": "center"}, children=[
                                                    html.Span(f"{gd['left_raw']:.2f}", style={
                                                        "fontSize": "16px",
                                                        "fontWeight": "500",
                                                        "fontFamily": FONT_MONO,
                                                        "color": COLORS["left_bar"],
                                                    }),
                                                    html.Span(f" {gd['unit']}", style={
                                                        "fontSize": "11px",
                                                        "color": COLORS["text_muted"],
                                                    }),
                                                ]),
                                            ],
                                        ),
                                    ])
                                    for gd in grip_chart_data
                                ],
                            ),
                        ],
                    ),

                    # Right: Asymmetry Analysis
                    html.Div(
                        style=CARD_STYLE,
                        children=[
                            section_header(
                                "CMJ Leg Asymmetry",
                                "L|R bilateral index (%) — positive = right dominant",
                            ),
                            dcc.Graph(
                                figure=asymmetry_chart,
                                config={"displayModeBar": False},
                            ),
                            severity_legend(),
                            html.Div(
                                style={
                                    **CARD_STYLE_ALT,
                                    "marginTop": "16px",
                                    "padding": "14px 18px",
                                },
                                children=[
                                    html.P("CMJ Clinical Note", style={
                                        "margin": "0 0 6px 0",
                                        "fontSize": "12px",
                                        "fontWeight": "600",
                                        "color": COLORS["accent_amber"],
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.05em",
                                    }),
                                    html.P(
                                        "Rebound Braking Impulse at 18.3% — placed on monitoring. "
                                        "CMJ Propulsive Impulse at 12.7% right-dominant. "
                                        "May indicate compensation pattern worth tracking across sessions.",
                                        style={
                                            "margin": "0",
                                            "fontSize": "13px",
                                            "color": COLORS["text_secondary"],
                                            "lineHeight": "1.5",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),

            # Grip Summary Table
            html.Div(
                style=CARD_STYLE,
                children=[
                    section_header("Grip Strength Summary", "Right vs Left hand comparison"),
                    html.Table(
                        style={
                            "width": "100%",
                            "borderCollapse": "separate",
                            "borderSpacing": "0",
                            "fontSize": "14px",
                        },
                        children=[
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th(col, style={
                                            "textAlign": "left" if i == 0 else "center",
                                            "padding": "12px 16px",
                                            "borderBottom": f"2px solid {COLORS['border']}",
                                            "color": COLORS["text_secondary"],
                                            "fontSize": "11px",
                                            "fontWeight": "600",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.05em",
                                        })
                                        for i, col in enumerate(["Metric", "Right", "Left", "% Difference", "Total Difference"])
                                    ]
                                )
                            ),
                            html.Tbody([
                                html.Tr(
                                    [
                                        html.Td(metric, style={
                                            "padding": "12px 16px",
                                            "borderBottom": f"1px solid {COLORS['grid']}",
                                            "fontWeight": "500",
                                            "color": COLORS["text_primary"],
                                        }),
                                        html.Td(f"{d['right']:.2f} {d['unit']}", style={
                                            "padding": "12px 16px",
                                            "borderBottom": f"1px solid {COLORS['grid']}",
                                            "textAlign": "center",
                                            "color": COLORS["right_bar"],
                                            "fontWeight": "500",
                                            "fontFamily": FONT_MONO,
                                        }),
                                        html.Td(f"{d['left']:.2f} {d['unit']}", style={
                                            "padding": "12px 16px",
                                            "borderBottom": f"1px solid {COLORS['grid']}",
                                            "textAlign": "center",
                                            "color": COLORS["left_bar"],
                                            "fontWeight": "500",
                                            "fontFamily": FONT_MONO,
                                        }),
                                        html.Td(
                                            f"{abs(d['right'] - d['left']) / max(d['right'], d['left']) * 100:.1f}%",
                                            style={
                                                "padding": "12px 16px",
                                                "borderBottom": f"1px solid {COLORS['grid']}",
                                                "textAlign": "center",
                                                "fontWeight": "600",
                                                "color": COLORS["text_secondary"],
                                            },
                                        ),
                                        html.Td(
                                            f"{abs(d['right'] - d['left']):.2f} {d['unit']}",
                                            style={
                                                "padding": "12px 16px",
                                                "borderBottom": f"1px solid {COLORS['grid']}",
                                                "textAlign": "center",
                                                "color": COLORS["text_secondary"],
                                            },
                                        ),
                                    ]
                                )
                                for metric, d in GRIP_DATA.items()
                            ]),
                        ],
                    ),
                ],
            ),

            # CMJ Asymmetry Summary Table
            html.Div(
                style={**CARD_STYLE, "marginTop": "20px"},
                children=[
                    section_header("CMJ Asymmetry Summary", "Left|Right bilateral index from CMJ testing"),
                    html.Table(
                        style={
                            "width": "100%",
                            "borderCollapse": "separate",
                            "borderSpacing": "0",
                            "fontSize": "14px",
                        },
                        children=[
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th(col, style={
                                            "textAlign": "left" if i == 0 else "center",
                                            "padding": "12px 16px",
                                            "borderBottom": f"2px solid {COLORS['border']}",
                                            "color": COLORS["text_secondary"],
                                            "fontSize": "11px",
                                            "fontWeight": "600",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.05em",
                                        })
                                        for i, col in enumerate(["Metric", "Asymmetry Index (%)", "Dominant Side", "Status"])
                                    ]
                                )
                            ),
                            html.Tbody([
                                html.Tr(
                                    [
                                        html.Td(metric, style={
                                            "padding": "12px 16px",
                                            "borderBottom": f"1px solid {COLORS['grid']}",
                                            "fontWeight": "500",
                                            "color": COLORS["text_primary"],
                                        }),
                                        html.Td(
                                            f"{val:+.1f}%",
                                            style={
                                                "padding": "12px 16px",
                                                "borderBottom": f"1px solid {COLORS['grid']}",
                                                "textAlign": "center",
                                                "fontWeight": "500",
                                                "fontFamily": FONT_MONO,
                                                "color": (
                                                    COLORS["accent_green"] if abs(val) < 10
                                                    else (COLORS["accent_amber"] if abs(val) < 25
                                                          else COLORS["accent_red"])
                                                ),
                                            },
                                        ),
                                        html.Td(
                                            "Right" if val > 0 else ("Left" if val < 0 else "Symmetric"),
                                            style={
                                                "padding": "12px 16px",
                                                "borderBottom": f"1px solid {COLORS['grid']}",
                                                "textAlign": "center",
                                                "color": COLORS["text_secondary"],
                                            },
                                        ),
                                        html.Td(
                                            html.Span(
                                                "FLAG" if abs(val) >= 25 else (
                                                    "MONITOR" if abs(val) >= 10 else "NORMAL"
                                                ),
                                                style={
                                                    "padding": "3px 10px",
                                                    "borderRadius": "4px",
                                                    "fontSize": "11px",
                                                    "fontWeight": "700",
                                                    "letterSpacing": "0.05em",
                                                    "backgroundColor": (
                                                        f"{COLORS['accent_red']}22" if abs(val) >= 25
                                                        else (f"{COLORS['accent_amber']}22" if abs(val) >= 10
                                                              else f"{COLORS['accent_green']}22")
                                                    ),
                                                    "color": (
                                                        COLORS["accent_red"] if abs(val) >= 25
                                                        else (COLORS["accent_amber"] if abs(val) >= 10
                                                              else COLORS["accent_green"])
                                                    ),
                                                },
                                            ),
                                            style={
                                                "padding": "12px 16px",
                                                "borderBottom": f"1px solid {COLORS['grid']}",
                                                "textAlign": "center",
                                            },
                                        ),
                                    ]
                                )
                                for metric, val in ASYMMETRY_DATA.items()
                            ]),
                        ],
                    ),
                ],
            ),

            # Footer
            html.Div(
                style={
                    "textAlign": "center",
                    "marginTop": "24px",
                    "paddingTop": "16px",
                    "borderTop": f"1px solid {COLORS['border']}",
                },
                children=[
                    html.P(
                        "Aeris Performance Concepts",
                        style={
                            "margin": "0",
                            "fontSize": "13px",
                            "fontWeight": "600",
                            "color": COLORS["text_secondary"],
                        },
                    ),
                    html.P(
                        "315 Rose Dale Court, Pinehurst, NC 28374",
                        style={
                            "margin": "4px 0 0 0",
                            "fontSize": "12px",
                            "color": COLORS["text_muted"],
                        },
                    ),
                ],
            ),
        ],
    )


# ====================== Standalone App ===================================
if __name__ == "__main__":
    app = Dash(__name__, external_stylesheets=[GOOGLE_FONTS_URL])
    app.layout = serve_layout
    app.run(debug=True, port=8052)
