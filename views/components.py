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


# ============ Scale gauge function to z-score ====================
def scale_to_gauge(
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


# =========== Line charts to show trends helper function ====================
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
                color="#f0ad4e",
                size=13,
                symbol="diamond",
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
                    color="#5cb85c",
                    size=13,
                    symbol="star",
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
