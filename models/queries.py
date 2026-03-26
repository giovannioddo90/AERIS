from sqlalchemy import text

from .config import (
    FOOTBALL_INJURY_DATA_POINTS,
    engine,
    GAUGE_COLUMNS,
    BAR_COLUMNS,
    ASYMMETRY_COLUMNS,
    INJURY_DATA,
    FOOTBALL_OUTPUT_METRICS,
    FOOTBALL_MOVEMENT_ANALYSIS_COLUMNS,
    FOOTBALL_ASYMMETRY_METRICS,
)


def get_athlete_names() -> list[str]:
    """Get all distinct athlete names from the CMJR tests."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT DISTINCT athlete_name FROM tests_cmjr ORDER BY athlete_name")
        )
        return [row[0] for row in result]


def get_test_dates(athlete_name: str) -> list[dict]:
    """Get distinct test dates for a given athlete, most recent first.

    Returns list of dicts with 'label' (MM-DD-YYYY) and 'value' (ISO date)
    so the dropdown displays friendly dates but stores queryable values.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT DISTINCT to_timestamp(timestamp)::date AS test_date "
                "FROM tests_cmjr "
                "WHERE athlete_name = :name ORDER BY test_date DESC"
            ),
            {"name": athlete_name},
        )
        return [
            {
                "label": row[0].strftime("%m-%d-%Y"),
                "value": row[0].isoformat(),
            }
            for row in result
        ]


def get_test_data(athlete_name: str, test_date_iso: str) -> dict:
    """Get averaged metric values for an athlete on a specific test date.

    Averages the 3 trials (rows) that share the same date.
    test_date_iso: ISO format date string like '2025-02-15'.
    """
    all_cols = GAUGE_COLUMNS + BAR_COLUMNS
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in all_cols)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmjr "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = :test_date"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name, "test_date": test_date_iso})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_baseline_data(athlete_name: str) -> dict:
    """Get averaged metric values from the athlete's earliest test date.

    This is the baseline (first test ever recorded for this athlete).
    Returns a dict like {"cmj_jump_height_m": 0.45, ...} or {} if none.
    """
    all_cols = GAUGE_COLUMNS + BAR_COLUMNS
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in all_cols)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmjr "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = ("
        "  SELECT MIN(to_timestamp(timestamp)::date) "
        "  FROM tests_cmjr WHERE athlete_name = :name"
        ")"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_population_stats(column_metrics: list, test_type: str) -> dict:
    """Get mean and stddev for each metric across all athletes/tests.

    test_type can be tests_cmj or tests_cmjr

    Used for z-score scaling. Returns:
        {"cmj_jump_height_m": {"mean": 0.4, "std": 0.05}, ...}
    """
    parts = []
    for col in column_metrics:
        parts.append(f"AVG({col}) AS {col}_mean")
        parts.append(f"STDDEV_POP({col}) AS {col}_std")
    select_clause = ", ".join(parts)

    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT {select_clause} FROM {test_type}"))
        row = result.mappings().fetchone()
        stats = {}
        for col in column_metrics:
            mean = row[f"{col}_mean"]
            std = row[f"{col}_std"]
            stats[col] = {
                "mean": float(mean) if mean is not None else None,
                "std": float(std) if std is not None and std > 0 else None,
            }
        return stats


def get_athlete_average(athlete_name: str) -> dict:
    """Get the athlete's average for each bar metric across their last 5 test dates.

    If the athlete has fewer than 5 test dates, all available dates are used.
    Returns: {"rebound_impulse_ratio": 1.23, ...} or {} if none.
    """
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in BAR_COLUMNS)
    query = text(
        f"SELECT {avg_cols} FROM tests_cmjr "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date IN ("
        "  SELECT DISTINCT to_timestamp(timestamp)::date AS test_date "
        "  FROM tests_cmjr WHERE athlete_name = :name "
        "  ORDER BY test_date DESC LIMIT 5"
        ")"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_athlete_alltime_average(athlete_name: str) -> dict:
    """Get the athlete's all-time average for each gauge metric.

    Returns: {"cmj_jump_height_m": 1.23, ...} or {} if none.
    """
    all_cols = GAUGE_COLUMNS + BAR_COLUMNS
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in all_cols)
    query = text(f"SELECT {avg_cols} FROM tests_cmjr " "WHERE athlete_name = :name")
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


# ================ Injury Container ==========================================
def get_cmjr_baseline_asymmetry(athlete_name: str) -> dict:
    """Get averaged asymmetry metrics from the athlete's earliest CMJR test date.

    Averages the 3 trials on the baseline date.
    Returns dict like {"cmj_lr_braking_impulse_index": -0.05, ...} or {}.
    """
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in ASYMMETRY_COLUMNS)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmjr "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = ("
        "  SELECT MIN(to_timestamp(timestamp)::date) "
        "  FROM tests_cmjr WHERE athlete_name = :name"
        ")"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


# Dupe func refactor to accept test_type param
def get_cmj_baseline_asymmetry(athlete_name: str) -> dict:
    """Get averaged asymmetry metrics from the athlete's earliest CMJ test date.

    Averages the 3 trials on the baseline date.
    Returns dict like {"cmj_lr_braking_impulse_index": -0.05, ...} or {}.
    """
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in FOOTBALL_ASYMMETRY_METRICS)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmj "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = ("
        "  SELECT MIN(to_timestamp(timestamp)::date) "
        "  FROM tests_cmj WHERE athlete_name = :name"
        ")"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_cmjr_date_asymmetry(athlete_name: str, test_date_iso: str) -> dict:
    """Get averaged asymmetry metrics for a specific CMJR test date.

    Averages the 3 trials on the given date.
    Returns dict like {"cmj_lr_braking_impulse_index": -0.05, ...} or {}.
    """
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in ASYMMETRY_COLUMNS)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmjr "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = :test_date"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name, "test_date": test_date_iso})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


# Dupe refactor to accept param test_date
def get_cmj_date_asymmetry(athlete_name: str, test_date_iso: str) -> dict:
    """Get averaged asymmetry metrics for a specific CMJ test date.

    Averages the 3 trials on the given date.
    Returns dict like {"cmj_lr_braking_impulse_index": -0.05, ...} or {}.
    """
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in FOOTBALL_ASYMMETRY_METRICS)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmj "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = :test_date"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name, "test_date": test_date_iso})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_team_average(metrics: list, test_type: str) -> dict:
    """Get the team-wide average for each bar metric across all athletes/tests.

    Returns: {"rebound_impulse_ratio": 1.15, ...}
    """
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in metrics)
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT {avg_cols} FROM {test_type}"))
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_trend_data(athlete_name: str) -> list[dict]:
    """Get per-date averaged metrics for all test dates of an athlete.

    Returns a list of dicts ordered by date ascending:
        [{"test_date": datetime.date, "col1": float, ...}, ...]
    Covers both gauge and bar metrics for the Trends container.
    """
    all_cols = (
        GAUGE_COLUMNS
        + BAR_COLUMNS
        + [
            "rebound_depth_m",
            "time_to_stabilization_ms",
            "relative_peak_landing_force",
        ]
    )
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in all_cols)
    query = text(
        f"SELECT to_timestamp(timestamp)::date AS test_date, {avg_cols} "
        "FROM tests_cmjr "
        "WHERE athlete_name = :name "
        "GROUP BY test_date "
        "ORDER BY test_date ASC"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name})
        return [dict(row) for row in result.mappings()]


def get_injury_data(athlete_name: str, test_date_iso: str) -> dict:
    """Get the raw data values for data below divergent graph.

    gets the average of the selected athlete and date from athlete profile
    Returns dict like {"rebound_depth_m": 0.5} or {}
    """
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in INJURY_DATA)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmjr "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = :test_date"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name, "test_date": test_date_iso})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_football_injury_data(athlete_name: str, test_date_iso: str) -> dict:
    """Get the raw data values for data below divergent graph.

    gets the average of the selected athlete and date from athlete profile
    Returns dict like {"rebound_depth_m": 0.5} or {}
    """
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in FOOTBALL_INJURY_DATA_POINTS)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmj "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = :test_date"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name, "test_date": test_date_iso})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


# =============================== CMJ Queries ====================================


def get_football_athlete_names() -> list[str]:
    """Get all distinct football athlete names from the CMJ tests."""
    with engine.connect() as conn:
        result = conn.execute(
            # teamID used in where statement
            text(
                "SELECT DISTINCT athlete_name "
                "FROM tests_cmj "
                "WHERE 'ajTD7FpSJgRIjXzEBu3E' IN (SELECT json_array_elements_text(athlete_teams)) "  # expands JSON array into a set of text rows
                "ORDER BY athlete_name"
            )
        )
        return [row[0] for row in result]


def get_cmj_test_dates(athlete_name: str) -> list[dict]:
    """Get distinct test dates from tests_cmj for a given athlete, most recent first.

    Returns list of dicts with 'label' (MM-DD-YYYY) and 'value' (ISO date).
    """
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT DISTINCT to_timestamp(timestamp)::date AS test_date "
                "FROM tests_cmj "
                "WHERE athlete_name = :name ORDER BY test_date DESC"
            ),
            {"name": athlete_name},
        )
        return [
            {
                "label": row[0].strftime("%m-%d-%Y"),
                "value": row[0].isoformat(),
            }
            for row in result
        ]


def get_cmj_test_data(athlete_name: str, test_date_iso: str) -> dict:
    """Get averaged metric values for an athlete on a specific test date.

    Averages the 3 trials (rows) that share the same date.
    test_date_iso: ISO format date string like '2025-02-15'.
    """
    all_cols = FOOTBALL_OUTPUT_METRICS + FOOTBALL_MOVEMENT_ANALYSIS_COLUMNS
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in all_cols)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmj "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = :test_date"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name, "test_date": test_date_iso})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_cmj_baseline_data(athlete_name: str) -> dict:
    """Get averaged metric values from the athlete's earliest test date.

    This is the baseline (first test ever recorded for this athlete).
    Returns a dict like {"jump_height_m": 0.45, ...} or {} if none.
    """
    all_cols = (
        FOOTBALL_OUTPUT_METRICS
        + FOOTBALL_MOVEMENT_ANALYSIS_COLUMNS
        + FOOTBALL_ASYMMETRY_METRICS
    )
    avg_cols = ", ".join(f"AVG({col}) AS {col}" for col in all_cols)
    query = text(
        f"SELECT {avg_cols} "
        "FROM tests_cmj "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date = ("
        "  SELECT MIN(to_timestamp(timestamp)::date) "
        "  FROM tests_cmj WHERE athlete_name = :name"
        ")"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)


def get_cmj_athlete_average(athlete_name: str) -> dict:
    """Get the athlete's average for each movement analysis metric across their last 5 test dates.

    If the athlete has fewer than 5 test dates, all available dates are used.
    Returns: {"relative_braking_impulse_n_s_kg": 1.23, ...} or {} if none.
    """
    avg_cols = ", ".join(
        f"AVG({col}) AS {col}"
        for col in FOOTBALL_MOVEMENT_ANALYSIS_COLUMNS + FOOTBALL_ASYMMETRY_METRICS
    )
    query = text(
        f"SELECT {avg_cols} FROM tests_cmj "
        "WHERE athlete_name = :name "
        "AND to_timestamp(timestamp)::date IN ("
        "  SELECT DISTINCT to_timestamp(timestamp)::date AS test_date "
        "  FROM tests_cmj WHERE athlete_name = :name "
        "  ORDER BY test_date DESC LIMIT 5"
        ")"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"name": athlete_name})
        row = result.mappings().fetchone()
        if row is None:
            return {}
        return dict(row)
