import os
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import textwrap
import plotly.graph_objects as go
from scipy import stats
from databricks import sql
from databricks.sdk.core import Config

st.set_page_config(page_title="Chapada Advanced Analytics - Grinding and Flotation", layout="wide")
st.title("Chapada Advanced Analytics - Grinding and Flotation")

with st.sidebar:
    st.title("➤ Navigation")
    st.markdown("---")
    
    st.markdown("### Quick Access")
    if st.sidebar.button("🏠︎ Home", use_container_width=True):
        st.switch_page("app.py")
    if st.sidebar.button("📈 Parallel Coordinates", use_container_width=True):
        st.switch_page("pages/parallel.py")
    if st.sidebar.button("🧠 AI Genie", use_container_width=True):
        st.switch_page("pages/chatbot.py")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This platform provides advanced analytics capabilities for data exploration and AI Genie-powered insights.
    
    **Features include:**
    - Interactive visualizations
    - AI-driven analysis
    - Real-time processing
    - Secure data handling
    """)

# --- Datetime controls ---
st.subheader("Datetime Filter")
col1, col2, _, _, _ = st.columns(5)
with col1:
    start_date = st.date_input("Start date", datetime.date(2024, 10, 1))
with col2:
    end_date = st.date_input("End date")

cfg = Config()  # Set the DATABRICKS_HOST environment variable when running locally
http_path_metric = os.getenv('HTTP_PATH_METRIC', '')
table_metric_name = os.getenv('TABLE_METRIC_NAME', '')
http_path_kpi_dict = os.getenv('HTTP_PATH_KPI_DICT', '')
table_kpi_name = os.getenv('TABLE_KPI_NAME', '')

def convert_datetime_safely(series):
    """Safely convert datetime series with multiple format attempts"""
    
    # If already datetime, return as is
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    
    # Try different approaches
    attempts = [
        # European format (day/month/year)
        lambda: pd.to_datetime(series, dayfirst=True, errors='coerce'),
        # US format (month/day/year)  
        lambda: pd.to_datetime(series, dayfirst=False, errors='coerce'),
        # Explicit format
        lambda: pd.to_datetime(series, format='%d/%m/%Y %H:%M:%S', errors='coerce'),
        # Mixed format inference
        lambda: pd.to_datetime(series, format='mixed', errors='coerce')
    ]
    
    for i, attempt in enumerate(attempts):
        try:
            result = attempt()
            # Check if conversion was successful (not all NaT)
            if not result.isna().all():
                return result
        except Exception:
            continue
    
    # If all attempts fail, return original with warning
    st.error("All datetime conversion attempts failed")
    return series

@st.cache_resource # connection is cached
def get_connection(http_path):
    return sql.connect(
        server_hostname=cfg.host,
        http_path=http_path,
        credentials_provider=lambda: cfg.authenticate,
    )

def read_table(start_date, end_date, table_metric, conn):
    with conn.cursor() as cursor:
        query = f"""
           SELECT
                `local_datetime`,
                CAST(metric_uid AS VARCHAR(50)) AS metric_uid,
                `unit`,
                `metric_value`
           FROM {table_metric}
           WHERE `local_datetime` >= '{start_date}'
           AND `local_datetime` <= '{end_date}'
        """
        cursor.execute(query)
        return cursor.fetchall_arrow().to_pandas()


def read_limits(table_master, conn):
    with conn.cursor() as cursor:
        query = f"""
            SELECT 
                CAST(metric_uid AS VARCHAR(50)) AS metric_uid,
                `chart_low_limit`,
                `chart_high_limit`,
                `metric_name`
            FROM {table_master}

        """
        cursor.execute(query)
        return cursor.fetchall_arrow().to_pandas()


def make_parallel_plot_html(df, variables, is_zscore, enable_data_filter, 
                            use_constrain, global_name, min_value, max_value, 
                            zscore_limit_min_value, zscore_limit_max_value, zscore_bar_min_value, 
                            zscore_bar_max_value, filter_min_value, filter_max_value, lower_bound, upper_bound,
                            width=1000):
    
    #print(df.columns)
    grouped = (
        df.sort_values(["local_datetime", "metric_name"])
        .groupby(["local_datetime", "metric_name"], as_index=False)
        .agg({
            "metric_value": "first",
            "metric_uid": "first",
            "unit": "first",
            "chart_low_limit": "first",
            "chart_high_limit": "first"
        })
    )

    
    def min_func(x):
        if x["metric_value"].isna().all():
            return np.nan
        elif x["chart_low_limit"].notna().all():
            return x["chart_low_limit"].mean(skipna=True)
        else:
            return x["metric_value"].min(skipna=True)
        
    def max_func(x):
        if x["metric_value"].isna().all():
            return np.nan
        elif x["chart_high_limit"].notna().all():
            return x["chart_high_limit"].mean(skipna=True)
        else:
            return x["metric_value"].max(skipna=True)
        
    #summary_dt = (
    #    grouped.loc[grouped["metric_name"].notna() & (grouped["metric_name"] != "")]
    #    .groupby("metric_name", as_index=False)
    #    .apply(lambda x: pd.Series({
    #        "Min_Value": min_func(x),
    #        "Max_Value": max_func(x),
    #        "Unit": x["unit"].iloc[0]
    #    }))
    #    .reset_index(drop=True)
    #)
    if is_zscore:
        # Calculate z-scores by group
        grouped['metric_value'] = grouped.groupby('metric_name')['metric_value'].transform(
            lambda x: stats.zscore(x, ddof=1)
        )
        #print(grouped)
        
        # Create summary dataframe
        summary_dt = (grouped[~grouped['metric_name'].isna() & (grouped['metric_name'] != "")]
                    .groupby('metric_name', as_index=False)
                    .agg(Min_Value=('metric_name', lambda x: zscore_limit_min_value),
                        Max_Value=('metric_name', lambda x: zscore_limit_max_value),
                        Unit=('unit', 'first'))
                    .reset_index(drop=True))
        
        min_value = zscore_bar_min_value
        max_value = zscore_bar_max_value

    else:
        summary_dt = (grouped[~grouped['metric_name'].isna() & (grouped['metric_name'] != "")]
                    .groupby('metric_name', as_index=False)
                    .apply(lambda x: pd.Series({
                        'Min_Value': min_func(x),
                        'Max_Value': max_func(x),
                        'Unit': x['unit'].iloc[0] if len(x) > 0 else np.nan
                    }))
                    .reset_index(drop=True))

    summary_dt = summary_dt[
        summary_dt["Min_Value"].replace([np.inf, -np.inf], np.nan).notna() &
        summary_dt["Max_Value"].replace([np.inf, -np.inf], np.nan).notna()
    ]

    dimension_columns = summary_dt["metric_name"].tolist()
    dimension_columns = [var for var in variables if var in dimension_columns]

    wide = grouped.pivot(index="local_datetime", columns="metric_name", values="metric_value").reset_index()

    if enable_data_filter and global_name in wide.columns and not is_zscore:
        wide = wide[
            wide[global_name].between(filter_min_value, filter_max_value)
        ]
    
    unit_map = summary_dt.set_index("metric_name")["Unit"].to_dict()
    min_map  = summary_dt.set_index("metric_name")["Min_Value"].to_dict()
    max_map  = summary_dt.set_index("metric_name")["Max_Value"].to_dict()

    n_count = len(dimension_columns)
    if n_count > 0:
        xs = np.linspace(0, 1, n_count)

        def create_annotation(i, y_pos, yshift, suffix, text="", yanchor="bottom"):
            return {
                "x": xs[i],
                "y": y_pos,
                "xref": "paper",
                "yref": "paper",
                "colname": f"{dimension_columns[i]}{suffix}",
                "text": text,
                "showarrow": False,
                "xanchor": "center",
                "yanchor": yanchor,
                "yshift": yshift,
                "font": {"size": 10}
            }
        
        # Use different yanchors for top and bottom annotations
        annotations = [
            *[create_annotation(i, 0.98, 40, "_label", yanchor="top") for i in range(n_count)],  # Top labels
            *[create_annotation(i, 0.02, -45, "_range", yanchor="top") for i in range(n_count)],   # Bottom ranges
        ]

        ann_index = {ann["colname"]: idx for idx, ann in enumerate(annotations)}
    else:
        annotations = []
        ann_index = {}

    # === Helper to build dimensions ===
    def build_dimensions(df, columns, color_column, annotations, min_value, max_value,
                        unit_map, min_map, max_map, is_zscore=False):

        color_values = df[color_column].copy()

        if color_values.notna().any() and color_values.max(skipna=True) <= 1:
            color_values *= 100

        line = dict(
            color=color_values,
            colorscale="Portland",
            cmin=min_value,
            cmax=max_value,
            showscale=True
        )
        
        dimensions = []
        for col in columns:
            if col not in df.columns:
                continue
            
            values = df[col].map(lambda x: 0 if x == [] else x).to_numpy(dtype=float)
            col_min = float(min_map.get(col, np.nan))
            col_max = float(max_map.get(col, np.nan))
            col_min = round(col_min, 0) if col_min >= 10 else round(col_min, 2)
            col_max = round(col_max, 0) if col_max >= 10 else round(col_max, 2)
            unit = unit_map.get(col, "")

            # Update label annotation
            label = col.replace("_", " ")
            full_label = f"{label} ({unit})" if unit else label

            label_key = f"{col}_label"
            if label_key in ann_index:
                annotations[ann_index[label_key]]["text"] = "<br>".join(
                    textwrap.wrap(full_label, width=20)
                )

            def safe_nanmax(arr, default=0):
                if len(arr) == 0:
                    return default
                return np.nanmax(arr)

            # percentage scaling
            unit = "" if pd.isna(unit) or str(unit).strip() == "" else str(unit)
            if "%" in unit and safe_nanmax(values) <= 1 and not is_zscore:
                values *= 100
                if col_min <= 1 and col_max <= 1:
                    col_min *= 100
                    col_max *= 100

            # no negative if not z-score
            if not is_zscore and col_min < 0:
                col_min = 0

            crange = None
            if use_constrain:
                crange = pd.Series(values).quantile([lower_bound / 100, upper_bound / 100])
                range_key = f"{col}_range"
                if range_key in ann_index:
                    annotations[ann_index[range_key]]["text"] = (
                        f"[{round(crange.iloc[0], 1)} - {round(crange.iloc[1], 1)}]"
                    )

            values = values.clip(col_min, col_max)

            dimensions.append(dict(
                label="",
                values=values,
                range=[col_min, col_max],
                constraintrange=crange.tolist() if crange is not None else None
            ))

        return dimensions, line, annotations

    
    dimensions, line, annotations = build_dimensions(
        df=wide,
        columns=dimension_columns,
        color_column=global_name,
        annotations=annotations,
        min_value=min_value,
        max_value=max_value,
        unit_map=unit_map,
        min_map=min_map,
        max_map=max_map,
        is_zscore=is_zscore
    )
    
    for ann in annotations:
        if "_label" in ann["colname"]:
            line_count = str(ann["text"]).count('<br>') + 1
            if line_count >= 4:
                ann["yshift"] = 102
            elif line_count == 3:
                ann["yshift"] = 88
            elif line_count == 2:
                ann["yshift"] = 74
            else:  # 1 line or empty
                ann["yshift"] = 60
        ann.pop("colname", None)

    # --- Plotly figure ---
    fig = go.Figure(
        data=[go.Parcoords(line=line, dimensions=dimensions)]
    )
    fig.update_layout(
        title=dict(text="", font=dict(family="Calibri", size=20)),
        font=dict(size=13),
        margin=dict(l=80, r=80, t=120, b=75),
        annotations=annotations,
        xaxis=dict(domain=[0.1, 0.9]),
        yaxis=dict(domain=[0.1, 0.9]),
        height=700,
        width=width,
        autosize=True
    )

    # --- Streamlit Output ---
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    wrapped = f"""
    <div style="overflow-x:auto; width:100%;">
    <div style="min-width:{width}px;">
        {plot_html}
    </div>
    </div>
    """
    return wrapped 


def get_parallel_plot_parameters(tab_key="", default_values=None):
    """
    Get parallel plot parameters in an expander
    Returns a dictionary with all parameter values
    
    Args:
        tab_key (str): Unique identifier for the tab
        default_values (dict): Dictionary with default values for parameters
    """
    if default_values is None:
        default_values = {}
    
    key_suffix = f"_{tab_key}" if tab_key else ""
    
    # Set default values with fallbacks
    defaults = {
        'metric_uid_name': "Cu Recovery Rate",
        'enable_filter': False,
        'is_zscore': False,
        'filter_min': 0.4,
        'filter_max': 1.0,
        'bar_min': 65,
        'bar_max': 95,
        'zscore_min': -3.0,
        'zscore_max': 3.0,
        'zbar_min': 40.0,
        'zbar_max': 100.0,
        'variables': [
            "Feeder 002 speed",
            "Feeder 003 speed",
            "Feeder 004 speed",
            "Cu Recovery Rate",
        ]
    }
    
    # Override defaults with provided values
    defaults.update(default_values)
    
    with st.expander("Parallel Plot Parameters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            global_name = st.text_input("Metric UID Name", value=defaults['metric_uid_name'], key=f"metric_uid_name{key_suffix}")
            enable_data_filter = st.checkbox("Enable filter overrides", key=f"filter1{key_suffix}", value=defaults['enable_filter'])
            is_zscore = st.checkbox("Enable z-score display", key=f"zscore{key_suffix}", value=defaults['is_zscore'])
        with col2:
            min_value = st.number_input("Bar Min Value", value=defaults['bar_min'], key=f"bar_min_value{key_suffix}")
            filter_min_value = st.number_input("Filter Min Value", value=defaults['filter_min'], key=f"filter_min_value{key_suffix}")
        with col3:
            max_value = st.number_input("Bar Max Value", value=defaults['bar_max'], key=f"bar_max_value{key_suffix}")
            filter_max_value = st.number_input("Filter Max Value", value=defaults['filter_max'], key=f"filter_max_value{key_suffix}")
        
        # Z-score parameters (enabled when is_zscore is True)
        if is_zscore:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                zscore_limit_min_value = st.number_input("Z-score Limit Min", value=defaults['zscore_min'], key=f"zscore_min{key_suffix}")
            with col2:
                zscore_limit_max_value = st.number_input("Z-score Limit Max", value=defaults['zscore_max'], key=f"zscore_max{key_suffix}")
            with col3:
                zscore_bar_min_value = st.number_input("Z-score Bar Min", value=defaults['zbar_min'], key=f"zbar_min{key_suffix}")
            with col4:
                zscore_bar_max_value = st.number_input("Z-score Bar Max", value=defaults['zbar_max'], key=f"zbar_max{key_suffix}")
        else:
            # Default values when not enabled
            zscore_limit_min_value = defaults['zscore_min']
            zscore_limit_max_value = defaults['zscore_max']
            zscore_bar_min_value = defaults['zbar_min']
            zscore_bar_max_value = defaults['zbar_max']
        
        # Variables editor
        variables = defaults['variables']
        
        # Initialize session state for this tab
        session_key = f'variables_df{key_suffix}'
        editor_key = f'editor_key{key_suffix}'
        
        if session_key not in st.session_state:
            st.session_state[session_key] = pd.DataFrame({
                'Variable Name': variables
            })

        if editor_key not in st.session_state:
            st.session_state[editor_key] = 0
        
        # Display editable dataframe
        col1, _, _ = st.columns(3)
        with col1:
            st.subheader("Edit Variables")
            edited_df = st.data_editor(
                st.session_state[session_key],
                num_rows="dynamic",
                use_container_width=True,
                key=f"variables_editor_{st.session_state[editor_key]}{key_suffix}"
            )
            if st.button("Reset Variables", key=f"reset{key_suffix}"):
                st.session_state[session_key] = pd.DataFrame({
                    'Variable Name': variables
                })
                st.session_state[editor_key] += 1
                st.rerun()
        
        variables = edited_df['Variable Name'].tolist()
    
    # Return all parameters as a dictionary
    return {
        'global_name': global_name,
        'enable_data_filter': enable_data_filter,
        'is_zscore': is_zscore,
        'min_value': min_value,
        'filter_min_value': filter_min_value,
        'max_value': max_value,
        'filter_max_value': filter_max_value,
        'zscore_limit_min_value': zscore_limit_min_value,
        'zscore_limit_max_value': zscore_limit_max_value,
        'zscore_bar_min_value': zscore_bar_min_value,
        'zscore_bar_max_value': zscore_bar_max_value,
        'variables': variables
    }



# Initialize session state
if 'df_metric' not in st.session_state:
    st.session_state.df_metric = None
if 'df_limits' not in st.session_state:
    st.session_state.df_limits = None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def read_table_cached(start_date, end_date, table_metric_name, _conn_1):
    return read_table(start_date, end_date, table_metric_name, _conn_1)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def read_limits_cached(table_kpi_name, _conn_2):
    return read_limits(table_kpi_name, _conn_2)

if st.session_state.df_metric is None or st.button("Reload Data"):
        with st.spinner("Loading data..."):
            conn_1 = get_connection(http_path_metric)
            st.session_state.df_metric = read_table_cached(start_date, end_date, table_metric_name, conn_1)
            conn_2 = get_connection(http_path_kpi_dict)
            st.session_state.df_limits = read_limits_cached(table_kpi_name, conn_2)
        st.success("Data loaded!")

if st.session_state.df_metric is not None:
    df_metric = st.session_state.df_metric
    df_limits = st.session_state.df_limits

start_dt = pd.to_datetime(start_date).normalize()
end_dt = pd.to_datetime(end_date).normalize()

if not pd.api.types.is_datetime64_any_dtype(df_metric['local_datetime']):
    df_metric['local_datetime'] = convert_datetime_safely(df_metric['local_datetime'])

# Filter by date range
df_metric = df_metric[
    df_metric['local_datetime'].dt.date.between(start_date, end_date)
]

# --- Parameters & controls ---
st.subheader("Constraint Parameters")
use_constrain = st.checkbox("Enable constraint range display", key="isconstrain", 
                           value=False)

# Constraint parameters (enabled when use_constrain is True)
if use_constrain:
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        lower_bound = st.number_input("Lower Bound", value=10.0, key="lower_bound")
    with col2:
        upper_bound = st.number_input("Upper Bound", value=90.0, key="upper_bound")
else:
    # Default values when not enabled
    lower_bound, upper_bound = 10, 90

merged = pd.merge(df_metric, df_limits, on='metric_uid', how='left')

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Grinding vs Throughput", "Grinding vs Recovery", 
                                  "Flotation I vs Recovery", "Flotation II vs Recovery",
                                  "Rougher + 1st scavenger vs Recovery"])

with tab1:
    variables = [
        "Tracked axb indicator",
        "Tracked work index",
        "IPC Power",
        "Intermediate ore stockpile level",
        "Feeder 002 speed",
        "Feeder 003 speed",
        "Feeder 004 speed",
        "BB-701's bin level",
        "Semi mobile crushing's dry throughput",
        "Pct < 1 inch in the SAG feed",
        "Pct < 2 inch in the SAG feed",
        "SAG mill's total power",
        "SAG mill's average bearing pressure",
        "Solids SAG",
        "Total water flow to SAG mill",
        "Generated pebbles throughput by CV-004",
        "Water flow to SAG box",
        "SAG box level",
        "Pulp flow towards cyclones battery",
        "Ball mill's sum of engine power",
        "Ball mill's average bearing pressure",
        "Ball mill's pond level",
        "SAG Mill Throughput",
    ]
    defaults = {
        'metric_uid_name': "SAG Mill Throughput",
        'enable_filter': False,
        'filter_min': 0.4,
        'filter_max': 1.0,
        'bar_min': 1000,
        'bar_max': 3700,
        'is_zscore': False,
        'zscore_min': -6.0,
        'zscore_max': 6.0,
        'zbar_min': -2.0,
        'zbar_max': 2.0,
        'variables': variables
    }

    st.markdown(
        "<h3 style='text-align: center;'>Grinding Circuit Metrics Impact on Throughput Performance</h3>", 
        unsafe_allow_html=True
    )
    
    params = get_parallel_plot_parameters("tab1", default_values=defaults)

    final_df = merged[merged['metric_name'].isin(params['variables'])]

    html_code = make_parallel_plot_html(
        final_df, 
        params['variables'], 
        params['is_zscore'], 
        params['enable_data_filter'], 
        use_constrain, 
        params['global_name'], 
        params['min_value'], 
        params['max_value'], 
        params['zscore_limit_min_value'], 
        params['zscore_limit_max_value'], 
        params['zscore_bar_min_value'], 
        params['zscore_bar_max_value'], 
        params['filter_min_value'], 
        params['filter_max_value'], 
        lower_bound, 
        upper_bound,
        width=len(params['variables'])*150
    )
    st.components.v1.html(html_code, height=800, scrolling=True)


with tab2:
    variables = [
        "Tracked axb indicator",
        "Tracked work index",
        "IPC Power",
        "Intermediate ore stockpile level",
        "Feeder 002 speed",
        "Feeder 003 speed",
        "Feeder 004 speed",
        "BB-701's bin level",
        "Semi mobile crushing's dry throughput",
        "Pct < 1 inch in the SAG feed",
        "Pct < 2 inch in the SAG feed",
        "SAG mill's total power",
        "SAG mill's average bearing pressure",
        "Solids SAG",
        "Total water flow to SAG mill",
        "Generated pebbles throughput by CV-004",
        "Water flow to SAG box",
        "SAG box level",
        "Pulp flow towards cyclones battery",
        "Ball mill's sum of engine power",
        "Ball mill's average bearing pressure",
        "Ball mill's pond level",
        "Cu Recovery Rate",
    ]
    defaults = {
        'metric_uid_name': "Cu Recovery Rate",
        'enable_filter': False,
        'filter_min': 0.85,
        'filter_max': 0.95,
        'bar_min': 65,
        'bar_max': 95,
        'is_zscore': False,
        'zscore_min': -6.0,
        'zscore_max': 6.0,
        'zbar_min': -2.0,
        'zbar_max': 2.0,
        'variables': variables
    }

    st.markdown(
        "<h3 style='text-align: center;'>Grinding Circuit Metrics Impact on Recovery Performance</h3>", 
        unsafe_allow_html=True
    )
    
    params = get_parallel_plot_parameters("tab2", default_values=defaults)

    final_df = merged[merged['metric_name'].isin(params['variables'])]

    html_code = make_parallel_plot_html(
        final_df, 
        params['variables'], 
        params['is_zscore'], 
        params['enable_data_filter'], 
        use_constrain, 
        params['global_name'], 
        params['min_value'], 
        params['max_value'], 
        params['zscore_limit_min_value'], 
        params['zscore_limit_max_value'], 
        params['zscore_bar_min_value'], 
        params['zscore_bar_max_value'], 
        params['filter_min_value'], 
        params['filter_max_value'], 
        lower_bound, 
        upper_bound,
        width=len(params['variables'])*150
    )
    st.components.v1.html(html_code, height=800, scrolling=True)

with tab3:
    variables = [
        "Fe/Cu ratio in ore feed",
        "SAG's sulphur grade",
        "Solids percentage of solids in SAG's cyclones overflow",
        "Feeding pressure of cyclones battery",
        "Product passing size in SAG's cyclones overflow",
        "Solids percentage of solids in ball mill's cyclones overflow",
        "Ball mill's cyclones battery no2 pressure",
        "Product passing size in ball mill's cyclones overflow",
        "Product size to flotation in microns",
        "Measured pH in rougher stage ag04 - line b",
        "Measured pH in rougher stage ag01 - line a",
        "Xanthate dosage in rougher stage FC 005 - line b",
        "Xanthate dosage in rougher stage FC 002 - line a",
        "Frother dosage in rougher stage FC 002 - line a",
        "Frother dosage in rougher stage FC 005 - line b",
        "MIBCOL dosage in db-001",
        "Froth level cells FC 001/002",
        "Froth level cells FC 004/005",
        "Froth level cells FC 003",
        "Froth level cells FC 006",
        "Air flow average cells FC 001/002",
        "Air flow average cells FC 004/005",
        "Air flow cell FC 003",
        "Air flow cell FC 006",
        "Froth level cells FC 009/010",
        "Froth level cells FC 007/008",
        "Air flow average cells FC 009/010",
        "Air flow average cells FC 007/008",
        "Cu Recovery Rate"
    ]

    defaults = {
        'metric_uid_name': "Cu Recovery Rate",
        'enable_filter': False,
        'filter_min': 0.85,
        'filter_max': 0.95,
        'bar_min': 65,
        'bar_max': 95,
        'is_zscore': False,
        'zscore_min': -6.0,
        'zscore_max': 6.0,
        'zbar_min': -2.0,
        'zbar_max': 2.0,
        'variables': variables
    }

    st.markdown(
        "<h3 style='text-align: center;'>Flotation I Circuit Metrics Impact on Recovery Performance</h3>", 
        unsafe_allow_html=True
    )
    
    params = get_parallel_plot_parameters("tab3", default_values=defaults)

    final_df = merged[merged['metric_name'].isin(params['variables'])]

    html_code = make_parallel_plot_html(
        final_df, 
        params['variables'], 
        params['is_zscore'], 
        params['enable_data_filter'], 
        use_constrain, 
        params['global_name'], 
        params['min_value'], 
        params['max_value'], 
        params['zscore_limit_min_value'], 
        params['zscore_limit_max_value'], 
        params['zscore_bar_min_value'], 
        params['zscore_bar_max_value'], 
        params['filter_min_value'], 
        params['filter_max_value'], 
        lower_bound, 
        upper_bound,
        width=len(params['variables'])*150
    )
    st.components.v1.html(html_code, height=800, scrolling=True)

with tab4:
    variables = [
        "Measured pH in rougher box ag013",
        "Cu grade for scalper concentrate",
        "Feeding pressure of scalper tank",
        "Froth level scalper tank 502",
        "Froth level scalper tank 501",
        "Solids percentage in cleaner column",
        "Froth level for bank fc 013/015",
        "Froth level for bank fc 016/018",
        "Air flow for cell FC 014",
        "Air flow for cell FC 015",
        "Air flow for cell FC 016",
        "Air flow for cell FC 017",
        "Air flow for cell FC 018",
        "Measured pH in cleaner column fc-201",
        "Water flow to column fc 201",
        "Cu Recovery Rate"
    ]
    
    defaults = {
        'metric_uid_name': "Cu Recovery Rate",
        'enable_filter': False,
        'filter_min': 0.85,
        'filter_max': 0.95,
        'bar_min': 65,
        'bar_max': 95,
        'is_zscore': False,
        'zscore_min': -6.0,
        'zscore_max': 6.0,
        'zbar_min': -2.0,
        'zbar_max': 2.0,
        'variables': variables
    }

    st.markdown(
        "<h3 style='text-align: center;'>Flotation II Circuit Metrics Impact on Recovery Performance</h3>", 
        unsafe_allow_html=True
    )
    
    params = get_parallel_plot_parameters("tab4", default_values=defaults)

    final_df = merged[merged['metric_name'].isin(params['variables'])]

    html_code = make_parallel_plot_html(
        final_df, 
        params['variables'], 
        params['is_zscore'], 
        params['enable_data_filter'], 
        use_constrain, 
        params['global_name'], 
        params['min_value'], 
        params['max_value'], 
        params['zscore_limit_min_value'], 
        params['zscore_limit_max_value'], 
        params['zscore_bar_min_value'], 
        params['zscore_bar_max_value'], 
        params['filter_min_value'], 
        params['filter_max_value'], 
        lower_bound, 
        upper_bound,
        width=len(params['variables'])*150
    )
    st.components.v1.html(html_code, height=800, scrolling=True)


with tab5:
    variables = [
        "Air flow average cells FC 001/002",
        "Air flow cell FC 003",
        "Air flow average cells FC 007/008",
        "Air flow average cells FC 004/005",
        "Air flow cell FC 006",
        "Air flow average cells FC 009/010",
        "Au global recov.",
        "Cu Recovery Rate"
    ]
    
    defaults = {
        'metric_uid_name': "Cu Recovery Rate",
        'enable_filter': True,
        'filter_min': 0.4,
        'filter_max': 1.0,
        'bar_min': 65,
        'bar_max': 95,
        'is_zscore': False,
        'zscore_min': -6.0,
        'zscore_max': 6.0,
        'zbar_min': -2.0,
        'zbar_max': 2.0,
        'variables': variables
    }

    st.markdown(
        "<h3 style='text-align: center;'>Rougher + 1st Scavenger Metrics Impact on Recovery Performance</h3>", 
        unsafe_allow_html=True
    )
    
    params = get_parallel_plot_parameters("tab5", default_values=defaults)

    pre_final_df = merged[merged['metric_name'].isin(params['variables'])]

    df_dup = merged[merged["metric_name"] == "Cu Recovery Rate"].copy()

    # Modify duplicated rows
    df_dup["metric_name"] = "Au global recov."
    df_dup["metric_value"] = 100* df_dup["metric_value"].clip(0.2, 0.9)
    df_dup["unit"] = "%"
    df_dup["chart_low_limit"] = 20
    df_dup["chart_high_limit"] = 90

    # Append to original DataFrame
    final_df = pd.concat([pre_final_df, df_dup], ignore_index=True)

    html_code = make_parallel_plot_html(
        final_df, 
        params['variables'], 
        params['is_zscore'], 
        params['enable_data_filter'], 
        use_constrain, 
        params['global_name'], 
        params['min_value'], 
        params['max_value'], 
        params['zscore_limit_min_value'], 
        params['zscore_limit_max_value'], 
        params['zscore_bar_min_value'], 
        params['zscore_bar_max_value'], 
        params['filter_min_value'], 
        params['filter_max_value'], 
        lower_bound, 
        upper_bound,
        width=len(params['variables'])*150
    )
    st.components.v1.html(html_code, height=800, scrolling=True)

