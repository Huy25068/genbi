import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# =====================
# CONFIG
# =====================
st.set_page_config(
    page_title="Shopping Behavior Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================
# STYLE ĐỒNG BỘ VỚI TRANG CHỦ
# =====================
st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(circle at 10% 8%, rgba(0,194,212,0.12), transparent 26%),
            radial-gradient(circle at 90% 0%, rgba(26,58,107,0.16), transparent 28%),
            linear-gradient(135deg, #f8fbff 0%, #eef3f8 45%, #e8f6f8 100%);
    }

    .block-container {
        max-width: 100% !important;
        padding: 1.2rem 4rem 2.5rem 4rem !important;
    }

    [data-testid="stSidebar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"] {
        display: none !important;
    }

    .dashboard-hero {
        position: relative;
        overflow: hidden;
        width: 100%;
        min-height: 285px;
        background: linear-gradient(
            90deg,
            #1A3A6B 0%,
            #00C2D4 25%,
            #1A3A6B 50%,
            #00C2D4 75%,
            #1A3A6B 100%
        );
        background-size: 200% 100%;
        border-radius: 32px;
        padding: 56px 72px;
        color: white;
        box-shadow: 0 24px 70px rgba(26, 58, 107, 0.28);
        display: flex;
        flex-direction: column;
        justify-content: center;
        animation: heroFade 0.9s ease both, gradientMove 10s linear infinite;
        margin-bottom: 34px;
    }

    .dashboard-hero::after {
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 85% 20%, rgba(255,255,255,0.22), transparent 24%),
            radial-gradient(circle at 12% 80%, rgba(0,194,212,0.22), transparent 28%);
        pointer-events: none;
    }

    .hero-content {
        position: relative;
        z-index: 2;
    }

    .hero-badge {
        width: fit-content;
        padding: 10px 16px;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(0,194,212,0.42);
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 22px;
        backdrop-filter: blur(12px);
    }

    .hero-title {
        font-size: 58px;
        font-weight: 850;
        letter-spacing: -2px;
        margin-bottom: 16px;
        line-height: 1.05;
    }

    .hero-subtitle {
        font-size: 20px;
        color: #d9fbff;
        max-width: 980px;
        line-height: 1.6;
    }

    .section-label {
        font-size: 28px;
        font-weight: 850;
        color: #1A3A6B;
        margin: 34px 0 18px 0;
    }

    h1, h2, h3 {
        color: #1A3A6B !important;
        font-weight: 850 !important;
        letter-spacing: -0.4px;
    }

    h2 {
        padding-top: 18px !important;
        border-top: 1px solid rgba(0,194,212,0.18);
    }

    h3 {
        color: #111827 !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.95);
        border: 1px solid rgba(0,194,212,0.18);
        border-radius: 24px;
        padding: 26px 28px;
        box-shadow: 0 18px 45px rgba(26, 58, 107, 0.10);
        min-height: 135px;
    }

    [data-testid="stMetric"] label {
        color: #64748b !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricValue"] {
        color: #1A3A6B !important;
        font-weight: 850 !important;
    }

    /* KHUNG XEM 10 SESSION: đồng bộ card trắng/xanh giống toàn dashboard */
    [data-testid="stExpander"] {
        background:
            linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,251,255,0.96));
        border: 1px solid rgba(0,194,212,0.18);
        border-radius: 24px;
        box-shadow: 0 16px 42px rgba(26, 58, 107, 0.10);
        overflow: hidden;
        margin: 18px 0 32px 0;
    }

    [data-testid="stExpander"] details {
        border-radius: 24px;
    }

    [data-testid="stExpander"] summary {
        padding: 18px 22px !important;
        background:
            linear-gradient(90deg, rgba(26,58,107,0.08), rgba(0,194,212,0.12));
        border-bottom: 1px solid rgba(0,194,212,0.14);
    }

    [data-testid="stExpander"] summary p {
        color: #1A3A6B !important;
        font-size: 16px !important;
        font-weight: 850 !important;
    }

    [data-testid="stExpanderDetails"] {
        padding: 20px 22px 24px 22px !important;
        background: rgba(255,255,255,0.76);
    }

    [data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid rgba(0,194,212,0.14);
        box-shadow: 0 10px 28px rgba(26, 58, 107, 0.06);
    }

    .preview-caption {
        color: #64748B;
        font-size: 13px;
        margin: -4px 0 12px 0;
        line-height: 1.5;
    }

    .preview-table-shell {
        width: 100%;
        max-height: 360px;
        overflow: auto;
        border: 1px solid rgba(0,194,212,0.16);
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(26, 58, 107, 0.06);
    }

    .preview-table {
        border-collapse: separate;
        border-spacing: 0;
        width: max-content;
        min-width: 100%;
        font-size: 12px;
        color: #1E293B;
        background: #ffffff;
    }

    .preview-table thead th {
        position: sticky;
        top: 0;
        z-index: 3;
        background: linear-gradient(180deg, #E8F6F8, #D9FBFF);
        color: #1A3A6B;
        font-weight: 850;
        padding: 12px 14px;
        border-bottom: 1px solid rgba(0,194,212,0.20);
        border-right: 1px solid rgba(0,194,212,0.12);
        white-space: nowrap;
    }

    .preview-table tbody th,
    .preview-table tbody td {
        padding: 11px 14px;
        border-bottom: 1px solid rgba(26,58,107,0.08);
        border-right: 1px solid rgba(26,58,107,0.06);
        white-space: nowrap;
        background: #ffffff;
        color: #0F172A;
        font-weight: 650;
    }

    .preview-table tbody tr:nth-child(even) th,
    .preview-table tbody tr:nth-child(even) td {
        background: #F8FBFF;
    }

    .preview-table tbody tr:hover th,
    .preview-table tbody tr:hover td {
        background: #E8F6F8;
    }

    /* CARD BIỂU ĐỒ: cố định, không sinh scrollbar riêng, toolbar nằm gọn trong card */
    [data-testid="stPlotlyChart"] {
        position: relative;
        box-sizing: border-box !important;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,251,255,0.96));
        border: 1px solid rgba(0,194,212,0.16);
        border-radius: 28px;
        padding: 0 !important;
        box-shadow: 0 18px 45px rgba(26, 58, 107, 0.10);
        margin: 14px 0 34px 0;
        overflow: hidden !important;
    }

    [data-testid="stPlotlyChart"] > div,
    [data-testid="stPlotlyChart"] iframe,
    [data-testid="stPlotlyChart"] .js-plotly-plot,
    [data-testid="stPlotlyChart"] .plot-container,
    [data-testid="stPlotlyChart"] .svg-container,
    [data-testid="stPlotlyChart"] .main-svg {
        box-sizing: border-box !important;
        border-radius: 28px;
        background: transparent !important;
        overflow: hidden !important;
    }

    /* Ép không hiện thanh trượt trong khu vực biểu đồ */
    [data-testid="stPlotlyChart"],
    [data-testid="stPlotlyChart"] *,
    [data-testid="stPlotlyChart"] iframe {
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }

    [data-testid="stPlotlyChart"]::-webkit-scrollbar,
    [data-testid="stPlotlyChart"] *::-webkit-scrollbar,
    [data-testid="stPlotlyChart"] iframe::-webkit-scrollbar {
        width: 0 !important;
        height: 0 !important;
        display: none !important;
    }

    /* Toolbar VISTA: gọn, đủ icon, không bị cắt mép phải */
    [data-testid="stPlotlyChart"] .modebar-container {
        top: 18px !important;
        right: 28px !important;
        left: auto !important;
        width: auto !important;
        overflow: visible !important;
        z-index: 1000 !important;
    }

    [data-testid="stPlotlyChart"] .modebar {
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 4px !important;
        opacity: 0 !important;
        width: max-content !important;
        max-width: none !important;
        padding: 7px 10px !important;
        border-radius: 999px !important;
        background: rgba(255,255,255,0.96) !important;
        border: 1px solid rgba(0,194,212,0.34) !important;
        box-shadow: 0 14px 30px rgba(26, 58, 107, 0.16) !important;
        backdrop-filter: blur(12px) !important;
        transition: opacity 0.22s ease, transform 0.22s ease !important;
        transform: translateY(-4px) !important;
        overflow: visible !important;
    }

    [data-testid="stPlotlyChart"]:hover .modebar {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }

    [data-testid="stPlotlyChart"] .modebar-group {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        background: transparent !important;
        padding: 0 !important;
    }

    [data-testid="stPlotlyChart"] .modebar-btn {
        width: 28px !important;
        height: 28px !important;
        padding: 5px !important;
        border-radius: 999px !important;
        background: transparent !important;
        transition: 0.18s ease !important;
    }

    [data-testid="stPlotlyChart"] .modebar-btn svg {
        width: 16px !important;
        height: 16px !important;
    }

    [data-testid="stPlotlyChart"] .modebar-btn svg path {
        fill: #1A3A6B !important;
    }

    [data-testid="stPlotlyChart"] .modebar-btn:hover {
        background: rgba(0,194,212,0.14) !important;
        transform: translateY(-1px) !important;
    }

    [data-testid="stPlotlyChart"] .modebar-btn:hover svg path {
        fill: #00C2D4 !important;
    }

    /* ĐỒNG BỘ NÚT BẤM VỚI GENBI */
    div.stButton > button {
        width: auto;
        min-width: 150px;
        height: 44px;
        border-radius: 999px !important;
        border: 1px solid rgba(0,194,212,0.28) !important;
        background: rgba(255,255,255,0.92) !important;
        color: #1A3A6B !important;
        font-size: 15px;
        font-weight: 800;
        padding: 8px 18px;
        box-shadow: 0 12px 28px rgba(26, 58, 107, 0.10) !important;
        transition: 0.25s ease;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        border-color: #00C2D4 !important;
        color: #1A3A6B !important;
        box-shadow: 0 18px 38px rgba(26, 58, 107, 0.18) !important;
    }

    /* Ép text bên trong nút đậm lên y hệt bên GenBI */
    div.stButton > button p {
        color: #1A3A6B !important;
        font-weight: 800 !important;
    }

    hr {
        border: none;
        height: 1px;
        background: rgba(0,194,212,0.22);
        margin: 36px 0;
    }

    .footer-card {
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(0,194,212,0.16);
        border-radius: 24px;
        padding: 24px 30px;
        color: #64748b;
        box-shadow: 0 14px 38px rgba(26, 58, 107, 0.08);
        line-height: 1.7;
        margin-top: 20px;
    }

    @keyframes heroFade {
        from {
            opacity: 0;
            transform: translateY(26px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes gradientMove {
        from {
            background-position: 0% 50%;
        }
        to {
            background-position: 200% 50%;
        }
    }
</style>
""", unsafe_allow_html=True)

# =====================
# BACK BUTTON
# =====================
if st.button("← Về trang chủ"):
    st.switch_page("app.py")

# =====================
# KẾT NỐI DATABASE
# =====================
TOKEN = st.secrets["MOTHERDUCK_TOKEN"]

conn = duckdb.connect(
    f"md:shopping_db?motherduck_token={TOKEN}"
)

# =====================
# CHART DESIGN SYSTEM
# =====================
# Palette VISTA: chỉ dùng xanh navy / xanh cyan / xanh dương / xám, không dùng cam
VISTA_COLORS = [
    "#1A3A6B",
    "#00C2D4",
    "#2563EB",
    "#14B8A6",
    "#38BDF8",
    "#64748B",
    "#94A3B8",
    "#0F172A"
]

VISTA_DARK_COLORS = [
    "#1A3A6B",
    "#2563EB",
    "#0F766E",
    "#334155",
    "#0F172A"
]

# Thang màu vẫn theo style chung nhưng bỏ các màu quá nhạt để cột thấp vẫn nhìn rõ
VISTA_CONTINUOUS_SCALE = [
    [0.0, "#A7F3F8"],
    [0.25, "#67E8F9"],
    [0.5, "#00C2D4"],
    [0.75, "#2563EB"],
    [1.0, "#1A3A6B"]
]

AI_PREDICTION_COLORS = {
    "will_buy": "#00C2D4",
    "will_not_buy": "#1A3A6B",
    "Will Buy": "#00C2D4",
    "Will Not Buy": "#1A3A6B",
    "will buy": "#00C2D4",
    "will not buy": "#1A3A6B",
    "Sẽ mua": "#00C2D4",
    "Không mua": "#1A3A6B"
}


def style_chart(fig, height=430, showlegend=False):
    fig.update_layout(
        template="plotly_white",
        height=height,
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, Segoe UI, Arial, sans-serif",
            size=14,
            color="#334155"
        ),
        title=dict(
            font=dict(
                size=20,
                color="#1A3A6B",
                family="Inter, Segoe UI, Arial, sans-serif"
            ),
            x=0.02,
            xanchor="left",
            y=0.96
        ),
        margin=dict(t=86, r=140, b=96, l=72),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#00C2D4",
            font_size=13,
            font_family="Inter, Segoe UI, Arial, sans-serif",
            font_color="#0F172A"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0)",
            font=dict(size=13, color="#334155")
        ),
        showlegend=showlegend,
        uniformtext_minsize=11,
        uniformtext_mode="show",
        dragmode=False
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="rgba(26,58,107,0.18)",
        tickfont=dict(color="#64748B", size=12),
        title_font=dict(color="#1A3A6B", size=13),
        title_standoff=14,
        automargin=True
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(26,58,107,0.08)",
        zeroline=False,
        linecolor="rgba(26,58,107,0.18)",
        tickfont=dict(color="#64748B", size=12),
        title_font=dict(color="#1A3A6B", size=13),
        title_standoff=14,
        automargin=True
    )

    # Text trên cột luôn đặt ra ngoài để không bị đen-chìm-trên-nền-đậm
    for trace in fig.data:
        if trace.type == "bar":
            trace.update(
                textposition="outside",
                textfont=dict(color="#0F172A", size=12),
                cliponaxis=False,
                marker_line=dict(color="rgba(255,255,255,0.9)", width=1)
            )
        elif trace.type == "histogram":
            trace.update(
                marker_line=dict(color="rgba(255,255,255,0.9)", width=1)
            )
        elif trace.type == "scatter":
            trace.update(
                marker=dict(
                    line=dict(width=0.8, color="white")
                )
            )

    return fig


def style_pie_chart(fig, height=450):
    fig.update_traces(
        marker=dict(
            line=dict(color="white", width=3)
        ),
        textposition="outside",
        textinfo="label+percent+value",
        textfont=dict(color="#0F172A", size=13),
        outsidetextfont=dict(color="#0F172A", size=13),
        pull=0.015,
        hole=0.45,
        sort=False
    )

    fig.update_layout(
        template="plotly_white",
        height=height,
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, Segoe UI, Arial, sans-serif",
            size=14,
            color="#334155"
        ),
        title=dict(
            font=dict(size=20, color="#1A3A6B"),
            x=0.02,
            xanchor="left"
        ),
        margin=dict(t=86, r=140, b=104, l=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=13, color="#334155")
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#00C2D4",
            font_color="#0F172A"
        ),
        dragmode=False
    )

    return fig


def style_heatmap(fig, height=460):
    fig.update_layout(
        template="plotly_white",
        height=height,
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, Segoe UI, Arial, sans-serif",
            size=14,
            color="#334155"
        ),
        title=dict(
            font=dict(size=20, color="#1A3A6B"),
            x=0.02,
            xanchor="left"
        ),
        margin=dict(t=86, r=140, b=96, l=110),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#00C2D4",
            font_color="#0F172A"
        ),
        dragmode=False
    )

    fig.update_layout(coloraxis_showscale=False)

    fig.update_coloraxes(
        colorscale=VISTA_CONTINUOUS_SCALE,
        colorbar=dict(
            title="",
            thickness=14,
            outlinewidth=0,
            tickfont=dict(color="#64748B")
        )
    )

    fig.update_xaxes(
        tickfont=dict(color="#64748B", size=12),
        title_font=dict(color="#1A3A6B", size=13),
        title_standoff=14,
        automargin=True
    )

    fig.update_yaxes(
        tickfont=dict(color="#64748B", size=12),
        title_font=dict(color="#1A3A6B", size=13),
        title_standoff=14,
        automargin=True
    )

    fig.update_traces(
        textfont=dict(color="#0F172A", size=14)
    )

    return fig


def show_chart(fig, key):
    # Biểu đồ cố định: không scroll bằng chuột, không kéo pan; toolbar chỉ còn các nút cần thiết.
    st.plotly_chart(
        fig,
        use_container_width=True,
        key=key,
        config={
            "displayModeBar": "hover",
            "displaylogo": False,
            "responsive": True,
            "scrollZoom": False,
            "doubleClick": "reset",
            "modeBarButtonsToRemove": [
                "zoom2d",
                "pan2d",
                "select2d",
                "lasso2d",
                "autoScale2d",
                "toggleSpikelines",
                "hoverClosestCartesian",
                "hoverCompareCartesian"
            ],
            "toImageButtonOptions": {
                "format": "png",
                "filename": key,
                "height": 650,
                "width": 1200,
                "scale": 2
            }
        }
    )


def render_preview_table(df, caption):
    st.markdown(f'<div class="preview-caption">{caption}</div>', unsafe_allow_html=True)
    table_html = df.to_html(
        classes="preview-table",
        border=0,
        index=True,
        escape=True
    )
    st.markdown(
        f'<div class="preview-table-shell">{table_html}</div>',
        unsafe_allow_html=True
    )


# =====================
# HERO DASHBOARD
# =====================
st.markdown("""
<div class="dashboard-hero">
    <div class="hero-content">
        <div class="hero-badge">📊 Executive Dashboard</div>
        <div class="hero-title">Shopping Behavior Dashboard</div>
        <div class="hero-subtitle">
            Lakehouse • MotherDuck • Streamlit • AI Prediction<br>
            Theo dõi hành vi truy cập, tỷ lệ chuyển đổi và kết quả dự báo AI trên cùng một không gian trực quan.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =====================
# KPI
# =====================
st.markdown('<div class="section-label">Tổng quan hệ thống</div>', unsafe_allow_html=True)

query = """
SELECT
COUNT(*) total_session,
SUM(is_revenue) total_purchase,
ROUND(AVG(is_revenue)*100,2) conversion_rate
FROM main.fact_sessions
"""

kpi = conn.execute(query).df()

c1, c2, c3 = st.columns(3)

c1.metric(
    "Phiên truy cập",
    f"{kpi.iloc[0, 0]:,}"
)

c2.metric(
    "Số đơn mua",
    f"{kpi.iloc[0, 1]:,}"
)

c3.metric(
    "Conversion",
    f"{kpi.iloc[0, 2]}%"
)

# =====================
# PREVIEW DATA
# =====================
with st.expander("Xem dữ liệu Fact Sessions (10 dòng đầu)"):
    df_preview = conn.execute("SELECT * FROM main.fact_sessions LIMIT 10").df()
    render_preview_table(df_preview, "Preview nhanh 10 dòng đầu từ bảng fact_sessions.")

# ============================================================
# PHẦN 1: GOLD LAYER — FACT + DIMENSION
# ============================================================
st.header("🥇 Gold Layer — Phân tích từ Fact & Dimension")

# --- CHART 1: Tỷ lệ mua hàng theo tháng ---
st.subheader("Tỷ lệ mua hàng theo tháng")

query = """
SELECT
    t.Month,
    COUNT(*) AS total_sessions,
    SUM(f.is_revenue) AS purchases,
    ROUND(AVG(f.is_revenue) * 100, 2) AS conversion_rate
FROM main.fact_sessions f
JOIN main.dim_time t ON f.time_key = t.time_key
GROUP BY t.Month
ORDER BY conversion_rate DESC
"""
month_df = conn.execute(query).df()

fig1 = px.bar(
    month_df,
    x="Month",
    y="conversion_rate",
    title="Tỷ lệ chuyển đổi (%) theo tháng",
    text="conversion_rate",
    color="conversion_rate",
    color_continuous_scale=VISTA_CONTINUOUS_SCALE
)
fig1.update_traces(texttemplate="%{text}%", textposition="outside")
fig1.update_layout(coloraxis_showscale=False, yaxis_title="Conversion Rate (%)")
fig1 = style_chart(fig1)
show_chart(fig1, key="chart_1")

# --- CHART 2: Doanh thu theo trình duyệt ---
st.subheader("Số đơn mua theo trình duyệt")

query = """
SELECT
    s.Browser,
    COUNT(*) AS orders
FROM main.fact_sessions f
JOIN main.dim_system s ON f.system_key = s.system_key
WHERE f.is_revenue = 1
GROUP BY s.Browser
ORDER BY orders DESC
"""
browser_df = conn.execute(query).df()

fig2 = px.bar(
    browser_df,
    x="Browser",
    y="orders",
    title="Số đơn mua theo mã trình duyệt",
    text_auto=True,
    color="orders",
    color_continuous_scale=VISTA_CONTINUOUS_SCALE
)
fig2.update_layout(coloraxis_showscale=False, yaxis_title="Số đơn mua")
fig2 = style_chart(fig2)
show_chart(fig2, key="chart_2")

# --- CHART 3: Tỷ lệ chuyển đổi theo loại khách ---
st.subheader("Tỷ lệ chuyển đổi theo loại khách truy cập")

query = """
SELECT
    v.VisitorType,
    COUNT(*) AS total_sessions,
    SUM(f.is_revenue) AS purchases,
    ROUND(AVG(f.is_revenue) * 100, 2) AS conversion_rate
FROM main.fact_sessions f
JOIN main.dim_visitor v ON f.visitor_key = v.visitor_key
GROUP BY v.VisitorType
ORDER BY conversion_rate DESC
"""
visitor_df = conn.execute(query).df()

fig3 = px.bar(
    visitor_df,
    x="VisitorType",
    y="conversion_rate",
    title="Tỷ lệ chuyển đổi (%) theo loại khách",
    text="conversion_rate",
    color="VisitorType",
    color_discrete_sequence=VISTA_COLORS
)
fig3.update_traces(texttemplate="%{text}%", textposition="outside")
fig3.update_layout(showlegend=False, yaxis_title="Conversion Rate (%)")
fig3 = style_chart(fig3)
show_chart(fig3, key="chart_3")

# --- CHART 4: Cuối tuần vs Ngày thường ---
st.subheader("Tỷ lệ chuyển đổi: Ngày thường vs Cuối tuần")

query = """
SELECT
    CASE WHEN t.Weekend = 1 THEN 'Cuối tuần' ELSE 'Ngày thường' END AS day_type,
    COUNT(*) AS total_sessions,
    SUM(f.is_revenue) AS purchases,
    ROUND(AVG(f.is_revenue) * 100, 2) AS conversion_rate
FROM main.fact_sessions f
JOIN main.dim_time t ON f.time_key = t.time_key
GROUP BY t.Weekend
"""
weekend_df = conn.execute(query).df()

fig4 = px.bar(
    weekend_df,
    x="day_type",
    y="conversion_rate",
    title="Tỷ lệ mua hàng: Ngày thường vs Cuối tuần",
    text="conversion_rate",
    color="day_type",
    color_discrete_sequence=VISTA_COLORS
)
fig4.update_traces(texttemplate="%{text}%", textposition="outside")
fig4.update_layout(showlegend=False, yaxis_title="Conversion Rate (%)")
fig4 = style_chart(fig4)
show_chart(fig4, key="chart_4")

# --- CHART 5: Tỷ lệ chuyển đổi theo Holiday Proximity ---
st.subheader("Tỷ lệ chuyển đổi theo mức độ gần ngày lễ")

query = """
SELECT
    t.holiday_proximity,
    COUNT(*) AS total_sessions,
    ROUND(AVG(f.is_revenue) * 100, 2) AS conversion_rate
FROM main.fact_sessions f
JOIN main.dim_time t ON f.time_key = t.time_key
GROUP BY t.holiday_proximity
ORDER BY conversion_rate DESC
"""
holiday_df = conn.execute(query).df()

fig5 = px.bar(
    holiday_df,
    x="holiday_proximity",
    y="conversion_rate",
    title="Tỷ lệ mua hàng theo mức độ gần ngày lễ",
    text="conversion_rate",
    color="holiday_proximity",
    color_discrete_sequence=VISTA_COLORS
)
fig5.update_traces(texttemplate="%{text}%", textposition="outside")
fig5.update_layout(showlegend=False, yaxis_title="Conversion Rate (%)")
fig5 = style_chart(fig5)
show_chart(fig5, key="chart_5")

# ============================================================
# PHẦN 2: AI PREDICTIONS LAYER
# ============================================================
st.header("🤖 AI Prediction Layer — Phân tích từ bảng ai_predictions")

with st.expander("Xem dữ liệu AI Predictions (10 dòng đầu)"):
    df_ai_preview = conn.execute("SELECT * FROM main.ai_predictions LIMIT 10").df()
    render_preview_table(df_ai_preview, "Preview nhanh 10 dòng đầu từ bảng ai_predictions.")

# KPI AI
query = """
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN predicted_revenue = 1 THEN 1 ELSE 0 END) AS predicted_buy,
    SUM(CASE WHEN actual_revenue = 1 AND predicted_revenue = 1 THEN 1 ELSE 0 END) AS true_positive,
    SUM(CASE WHEN actual_revenue = 0 AND predicted_revenue = 0 THEN 1 ELSE 0 END) AS true_negative
FROM main.ai_predictions
"""
kpi_ai = conn.execute(query).df()

a1, a2, a3, a4 = st.columns(4)
a1.metric("📋 Tổng phiên dự báo", f"{kpi_ai.iloc[0, 0]:,}")
a2.metric("✅ AI dự báo sẽ mua", f"{kpi_ai.iloc[0, 1]:,}")
a3.metric("🎯 True Positive", f"{kpi_ai.iloc[0, 2]:,}")
a4.metric("🎯 True Negative", f"{kpi_ai.iloc[0, 3]:,}")

# --- CHART 6: Phân loại khách theo AI dự báo (Pie) ---
st.subheader("Phân loại khách hàng theo AI dự báo")

query = """
SELECT
    prediction_label,
    COUNT(*) AS total
FROM main.ai_predictions
GROUP BY prediction_label
"""
ai_pie_df = conn.execute(query).df()

fig7 = px.pie(
    ai_pie_df,
    names="prediction_label",
    values="total",
    title="Tỷ lệ khách AI dự báo sẽ mua vs không mua",
    color="prediction_label",
    color_discrete_map=AI_PREDICTION_COLORS,
    color_discrete_sequence=VISTA_COLORS
)
fig7 = style_pie_chart(fig7)
show_chart(fig7, key="chart_7")

# --- CHART 7: Cảnh báo khách rớt phễu theo loại người dùng ---
st.subheader("Cảnh báo khách hàng rớt phễu theo loại người dùng")

query = """
SELECT
    VisitorType,
    COUNT(*) AS lost_customer
FROM main.ai_predictions
WHERE predicted_revenue = 0
GROUP BY VisitorType
ORDER BY lost_customer DESC
"""
drop_df = conn.execute(query).df()

fig8 = px.bar(
    drop_df,
    x="VisitorType",
    y="lost_customer",
    title="Số khách hàng rớt phễu theo loại người dùng (AI dự báo không mua)",
    text_auto=True,
    color="VisitorType",
    color_discrete_sequence=VISTA_COLORS
)
fig8.update_layout(showlegend=False, yaxis_title="Số khách rớt phễu")
fig8 = style_chart(fig8)
show_chart(fig8, key="chart_8")

# --- CHART 8: Phân bố xác suất mua hàng ---
st.subheader("📊 Phân bố xác suất mua hàng dự đoán")

query = """
SELECT predicted_probability
FROM main.ai_predictions
"""
prob_df = conn.execute(query).df()

fig9 = px.histogram(
    prob_df,
    x="predicted_probability",
    nbins=30,
    title="Phân bố xác suất mua hàng (predicted_probability)",
    color_discrete_sequence=["#00C2D4"]
)
fig9.update_layout(xaxis_title="Xác suất mua hàng", yaxis_title="Số phiên")
fig9 = style_chart(fig9)
show_chart(fig9, key="chart_9")

# --- CHART 9: Đề xuất hành động từ AI ---
st.subheader("Đề xuất hành động từ AI")

query = """
SELECT
    recommended_action,
    COUNT(*) AS total
FROM main.ai_predictions
GROUP BY recommended_action
ORDER BY total DESC
"""
action_df = conn.execute(query).df()

fig10 = px.bar(
    action_df,
    x="total",
    y="recommended_action",
    orientation="h",
    title="Phân bổ hành động AI đề xuất cho từng nhóm khách",
    text_auto=True,
    color="total",
    color_continuous_scale=VISTA_CONTINUOUS_SCALE
)
fig10.update_layout(coloraxis_showscale=False, xaxis_title="Số khách hàng", yaxis_title="")
fig10 = style_chart(fig10, height=500)
show_chart(fig10, key="chart_10")

# --- CHART 10: Phân tầng khách theo Conversion Priority ---
st.subheader("Phân tầng khách hàng theo mức độ ưu tiên chuyển đổi")

query = """
SELECT
    conversion_priority,
    COUNT(*) AS total,
    ROUND(AVG(predicted_probability) * 100, 2) AS avg_prob
FROM main.ai_predictions
GROUP BY conversion_priority
ORDER BY avg_prob DESC
"""
priority_df = conn.execute(query).df()

fig11 = px.bar(
    priority_df,
    x="conversion_priority",
    y="total",
    title="Số lượng khách theo nhóm ưu tiên chuyển đổi",
    text="total",
    color="avg_prob",
    color_continuous_scale=VISTA_CONTINUOUS_SCALE,
    hover_data=["avg_prob"]
)
fig11.update_traces(textposition="outside")
fig11.update_layout(
    coloraxis_colorbar_title="Avg Prob (%)",
    yaxis_title="Số khách hàng"
)
fig11 = style_chart(fig11)
show_chart(fig11, key="chart_11")

# --- CHART 12: Confusion Matrix ---
st.subheader("Confusion Matrix — Actual vs Predicted")

query = """
SELECT
    actual_revenue,
    predicted_revenue,
    COUNT(*) AS total
FROM main.ai_predictions
GROUP BY actual_revenue, predicted_revenue
ORDER BY actual_revenue, predicted_revenue
"""
cm_df = conn.execute(query).df()

cm_pivot = cm_df.pivot(
    index="actual_revenue",
    columns="predicted_revenue",
    values="total"
).fillna(0).astype(int)

cm_pivot.index = ["Thực tế: Không mua (0)", "Thực tế: Có mua (1)"]
cm_pivot.columns = ["Dự báo: Không mua (0)", "Dự báo: Có mua (1)"]

fig12 = px.imshow(
    cm_pivot,
    text_auto=True,
    color_continuous_scale=VISTA_CONTINUOUS_SCALE,
    title="Confusion Matrix — So sánh kết quả thực tế và dự báo AI",
    aspect="auto"
)
fig12.update_layout(
    xaxis_title="Dự báo của mô hình",
    yaxis_title="Thực tế"
)
fig12 = style_heatmap(fig12)
show_chart(fig12, key="chart_12")

# --- CHART 13: Top lý do SHAP khiến khách không mua ---
st.subheader("Top lý do AI giải thích khách KHÔNG mua (SHAP)")

query = """
SELECT
    REGEXP_REPLACE(
        TRIM(SPLIT_PART(top_negative_shap_reasons, ';', 1)),
        ':.*', ''
    ) AS feature_name,
    COUNT(*) AS frequency
FROM main.ai_predictions
WHERE predicted_revenue = 0
GROUP BY feature_name
ORDER BY frequency DESC
LIMIT 10
"""
shap_neg_df = conn.execute(query).df()

fig13 = px.bar(
    shap_neg_df,
    x="frequency",
    y="feature_name",
    orientation="h",
    title="Top 10 yếu tố kéo GIẢM khả năng mua (nhóm không mua)",
    text_auto=True,
    color_discrete_sequence=["#38BDF8"]
)
fig13.update_layout(
    xaxis_title="Số lần là yếu tố âm mạnh nhất",
    yaxis_title=""
)
fig13 = style_chart(fig13, height=500)
show_chart(fig13, key="chart_13")

# --- CHART 14: Top lý do SHAP khiến khách SẼ mua ---
st.subheader("Top lý do AI giải thích khách SẼ mua (SHAP)")

query = """
SELECT
    REGEXP_REPLACE(
        TRIM(SPLIT_PART(top_positive_shap_reasons, ';', 1)),
        ':.*', ''
    ) AS feature_name,
    COUNT(*) AS frequency
FROM main.ai_predictions
WHERE predicted_revenue = 1
GROUP BY feature_name
ORDER BY frequency DESC
LIMIT 10
"""
shap_pos_df = conn.execute(query).df()

fig14 = px.bar(
    shap_pos_df,
    x="frequency",
    y="feature_name",
    orientation="h",
    title="Top 10 yếu tố kéo TĂNG khả năng mua (nhóm sẽ mua)",
    text_auto=True,
    color_discrete_sequence=["#00C2D4"]
)
fig14.update_layout(
    xaxis_title="Số lần là yếu tố dương mạnh nhất",
    yaxis_title=""
)
fig14 = style_chart(fig14, height=500)
show_chart(fig14, key="chart_14")

# --- CHART 15: Scatter PageValues vs Xác suất mua ---
st.subheader("PageValues vs Xác suất mua hàng dự đoán")

query = """
SELECT
    PageValues,
    predicted_probability,
    conversion_priority,
    VisitorType
FROM main.ai_predictions
WHERE PageValues <= 200
LIMIT 500
"""
scatter_df = conn.execute(query).df()

fig15 = px.scatter(
    scatter_df,
    x="PageValues",
    y="predicted_probability",
    color="conversion_priority",
    symbol="VisitorType",
    title="Mối quan hệ giữa PageValues và xác suất mua hàng (AI dự báo)",
    color_discrete_sequence=VISTA_COLORS,
    opacity=0.75
)
fig15.update_traces(
    marker=dict(
        size=9,
        line=dict(width=0.6, color="white")
    )
)
fig15.update_layout(
    xaxis_title="Page Values",
    yaxis_title="Xác suất mua hàng"
)
fig15 = style_chart(fig15, showlegend=True)
show_chart(fig15, key="chart_15")

st.divider()

st.markdown("""

""", unsafe_allow_html=True)