import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


# ====================== Query Metrics for queries.py ========================================


# Metric columns from database used for CMJRE gauges
GAUGE_COLUMNS = [
    "cmj_jump_height_m",
    "rebound_jump_momentum_kg_m_s",
    "rebound_modified_rsi",
    "rebound_peak_relative_braking_power_w_kg",
    "rebound_peak_relative_propulsive_power_w_kg",
]


# Metric columns from database used for Movement Analysis bar graphs
BAR_COLUMNS = [
    "rebound_relative_braking_impulse_n_s_kg",
    "rebound_relative_propulsive_impulse_n_s_kg",
    "rebound_impulse_ratio",
    "rebound_contact_time_ms",
    "rebound_force_at_min_displacement_n",
]


# Metrics for db query for divergent asymmetry graphs
ASYMMETRY_COLUMNS = [
    "cmj_lr_braking_impulse_index",
    "cmj_lr_propulsive_impulse_index",
    "lr_peak_landing_force",
    "rebound_lr_braking_impulse_index",
    "rebound_lr_propulsive_impulse_index",
]


# Metrics for db query for injury data points and trend graph
INJURY_DATA = [
    "time_to_stabilization_ms",
    "rebound_depth_m",
    "relative_peak_landing_force",
    "system_weight_n",
]

# ================ Graph Data Constants for athlete.py ===========================
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

# Combines gauge and bar metrics for the Trends container
TREND_CONFIG = (
    [(gid, title, col) for gid, title, col in GAUGE_CONFIG]
    + [(bid, title, col) for bid, title, col, _unit in BAR_CONFIG]
    + [
        ("rebound-cm-depth", "Rebound CM Depth", "rebound_depth_m"),
        ("time-to-stabilization", "Time to Stabilization", "time_to_stabilization_ms"),
        (
            "rel-peak-landing-force",
            "Relative Peak Landing Force",
            "relative_peak_landing_force",
        ),
    ]
)


# ================================== Union Pines Football Queries ==================================================
FOOTBALL_OUTPUT_METRICS = [
    "jump_height_m",
    "jump_momentum_kg_m_s",
    "mrsi",
    "peak_relative_braking_power_w_kg",
    "peak_relative_propulsive_power_w_kg",
]

# Metric columns from database used for Movement Analysis bar graphs
FOOTBALL_MOVEMENT_ANALYSIS_COLUMNS = [
    "relative_braking_impulse_n_s_kg",
    "relative_propulsive_impulse_n_s_kg",
    "impulse_ratio",
    "takeoff_velocity_m_s",
    "relative_force_at_min_displacement",
]

FOOTBALL_ASYMMETRY_METRICS = [
    "lr_peak_braking_force",
    "lr_peak_propulsive_force",
    "lr_peak_landing_force",
    "lr_braking_impulse_index",
    "lr_propulsive_impulse_index",
]

FOOTBALL_INJURY_DATA_POINTS = [
    "time_to_stabilization_ms",
    "relative_peak_landing_force",
]

OUTPUT_METRICS_CONFIG = [
    ("explosive-vertical", "Explosive Vertical", "jump_height_m"),
    (
        "explosive-acceleration",
        "Explosive Acceleration",
        "jump_momentum_kg_m_s",
    ),
    ("explosive-capacity", "Explosive Capacity", "mrsi"),
    (
        "change-of-direction",
        "Change of Direction",
        "peak_relative_braking_power_w_kg",
    ),
    ("takeoff-power", "Take-Off Power", "peak_relative_propulsive_power_w_kg"),
]

FOOTBALL_MOVEMENT_ANALYSIS_CONFIG = [
    (
        "sustained-braking",
        "Sustained Force Braking",
        "relative_braking_impulse_n_s_kg",
        "N·s/kg",
    ),
    (
        "sustained-propulsive",
        "Sustained Force Propulsive",
        "relative_propulsive_impulse_n_s_kg",
        "N·s/kg",
    ),
    ("force-strategy", "Force Strategy", "impulse_ratio", "ratio"),
    ("takeoff-velocity", "Takeoff Velocity", "takeoff_velocity_m_s", "ms"),
    (
        "relative-force-min-disp",
        "Relative Force at Min Displacement",
        "relative_force_at_min_displacement",
        "N",
    ),
]

FOOTBALL_INJURY_CONFIG = [
    ("peak-braking-force", "L|R Peak Braking Force", "lr_peak_braking_force"),
    (
        "peak-propulsive-force",
        "L|R Peak Propulsive Force",
        "lr_peak_propulsive_force",
    ),
    ("peak-landing-force", "L|R Peak Landing Force", "lr_peak_landing_force"),
    (
        "braking-impulse-index",
        "L|R Braking Impulse Index",
        "lr_braking_impulse_index",
    ),
    (
        "propulsive-impulse-index",
        "L|R Propulsive Impulse Index",
        "lr_propulsive_impulse_index",
    ),
]
