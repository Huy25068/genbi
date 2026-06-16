import streamlit as st

st.set_page_config(
    page_title="Shopping GenBI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 1. Khởi tạo Session State để kiểm soát Intro
if "intro_played" not in st.session_state:
    st.session_state.intro_played = False

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "content": "Chào bạn, tôi là GenBI. Bạn cần phân tích chỉ số kinh doanh nào hôm nay?"
        }
    ]

# 2. CSS và Màn hình Intro
if not st.session_state.intro_played:
    st.markdown("""
    <style>
    .intro-screen {
        position: fixed;
        inset: 0;
        z-index: 999999;
        background: radial-gradient(circle at center, rgba(0,194,212,0.22), transparent 34%),
                    linear-gradient(135deg, #061527 0%, #1A3A6B 55%, #00C2D4 140%);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: introHide 3.6s ease forwards;
        overflow: hidden;
    }

    .intro-screen::before {
        content: "";
        position: absolute;
        inset: 0;
        background-image: url('https://www.transparenttextures.com/patterns/stardust.png');
        opacity: 0.15;
        pointer-events: none;
    }

    .intro-content {
        text-align: center;
        color: white;
        animation: introZoom 2.4s ease forwards;
    }

    .intro-logo {
        font-size: 70px;
        font-weight: 900;
        letter-spacing: -2px;
        text-shadow: 0 0 10px #00C2D4, 0 0 20px #00C2D4, 0 0 40px rgba(0,194,212,0.6);
        animation: glowPulse 2s infinite alternate;
    }

    .intro-line {
        width: 0;
        height: 3px;
        margin: 22px auto;
        border-radius: 99px;
        background: linear-gradient(90deg, transparent, #00C2D4, white, #00C2D4, transparent);
        box-shadow: 0 0 15px #ffffff;
        animation: lineRun 1.7s ease forwards;
    }

    .intro-sub {
        font-size: 15px;
        letter-spacing: 4px;
        text-transform: uppercase;
        opacity: 0;
        animation: subFade 1.2s ease 0.8s forwards;
    }

    @keyframes glowPulse {
        from {
            text-shadow: 0 0 10px #00C2D4, 0 0 20px #00C2D4;
        }
        to {
            text-shadow: 0 0 20px #00C2D4, 0 0 40px #00C2D4, 0 0 60px #ffffff;
        }
    }

    @keyframes introHide {
        0%, 75% {
            opacity: 1;
            visibility: visible;
        }
        100% {
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }
    }

    @keyframes introZoom {
        0% {
            opacity: 0;
            transform: scale(0.9);
            filter: blur(10px);
        }
        100% {
            opacity: 1;
            transform: scale(1);
            filter: blur(0);
        }
    }

    @keyframes lineRun {
        from {
            width: 0;
        }
        to {
            width: min(420px, 80vw);
        }
    }

    @keyframes subFade {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 0.82;
            transform: translateY(0);
        }
    }
    </style>

    <div class="intro-screen">
        <div class="intro-content">
            <div class="intro-logo">Shopping GenBI</div>
            <div class="intro-line"></div>
            <div class="intro-sub">Initializing Business Intelligence System</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.intro_played = True

# 3. CSS Giao diện chính
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
        padding: 0rem 2rem 1rem 2rem !important;
    }

    [data-testid="stSidebar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"] {
        display: none !important;
    }

    .hero {
        position: relative;
        overflow: hidden;
        width: 100%;
        min-height: 280px;
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
        padding: clamp(24px, 4vw, 64px)
                 clamp(20px, 5vw, 76px);
        color: white;
        box-shadow: 0 24px 70px rgba(26, 58, 107, 0.28);
        display: flex;
        flex-direction: column;
        justify-content: center;
        animation: heroFade 0.9s ease both,
                   gradientMove 10s linear infinite;
    }

    .hero-badge {
        width: fit-content;
        padding: 10px 16px;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(0,194,212,0.42);
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
    }

    .hero-title {
        font-size: clamp(34px, 5vw, 68px);
        font-weight: 850;
        letter-spacing: -2px;
        margin-bottom: 18px;
        line-height: 1.05;
    }

    .hero-subtitle {
        font-size: clamp(15px, 2vw, 21px);
        color: #d9fbff;
        max-width: 980px;
        line-height: 1.65;
    }

    .section-title {
        font-size: 28px;
        font-weight: 800;
        color: #1A3A6B;
        margin: 38px 0 18px 0;
    }

    .business-card-link {
        display: block;
        text-decoration: none !important;
        color: inherit !important;
    }

    .business-card-link:hover {
        text-decoration: none !important;
        color: inherit !important;
    }

    .business-card {
        position: relative;
        background: rgba(255,255,255,0.95);
        padding: 42px;
        border-radius: 28px;
        border: 1px solid rgba(0,194,212,0.18);
        min-height: 310px;
        transition: all 0.28s ease;
        margin-bottom: 16px;
        cursor: pointer;
    }

    .business-card:hover {
        transform: translateY(-10px);
        background: #ffffff;
        border-color: #00C2D4;
        box-shadow: 0 22px 55px rgba(26, 58, 107, 0.18);
    }

    .card-icon {
        width: 64px;
        height: 64px;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(0,194,212,0.17), rgba(26,58,107,0.12));
        color: #1A3A6B;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        margin-bottom: 28px;
    }

    .card-title {
        font-size: 30px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 16px;
    }

    .card-desc {
        color: #64748b;
        font-size: 18px;
        line-height: 1.65;
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

    /* Các Media Queries được chuyển xuống đây để không bị mất khi kết thúc Intro */
    @media (max-width: 992px) {
        .hero {
            min-height: auto;
        }

        .business-card {
            min-height: auto;
            padding: 28px;
        }

        .card-title {
            font-size: 24px;
        }

        .card-desc {
            font-size: 16px;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 0rem 1rem 1rem 1rem !important;
        }

        .hero {
            border-radius: 20px;
        }

        .section-title {
            font-size: 22px;
        }

        .card-icon {
            width: 52px;
            height: 52px;
            font-size: 24px;
        }

        .card-title {
            font-size: 20px;
        }

        .card-desc {
            font-size: 14px;
        }
    }
</style>
""", unsafe_allow_html=True)

# 4. Giao diện chính
st.markdown("""
<div class="hero">
    <div class="hero-badge">⚡ AI-Powered Business Intelligence Platform</div>
    <div class="hero-title">Shopping GenBI</div>
    <div class="hero-subtitle">
        Nền tảng phân tích kinh doanh hiện đại, kết hợp Data Warehouse, Dashboard trực quan
        và Trợ lý AI để hỗ trợ doanh nghiệp ra quyết định nhanh hơn.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">Workspace</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("""
    <a href="/Dashboard" target="_self" class="business-card-link">
        <div class="business-card">
            <div class="card-icon">📊</div>
            <div class="card-title">Executive Dashboard</div>
            <div class="card-desc">
                Theo dõi doanh thu, hành vi người dùng, lượt truy cập và tỷ lệ chuyển đổi
                thông qua hệ thống biểu đồ trực quan.
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <a href="/Tro_Ly_GenBI" target="_self" class="business-card-link">
        <div class="business-card">
            <div class="card-icon">🤖</div>
            <div class="card-title">GenBI Assistant</div>
            <div class="card-desc">
                Đặt câu hỏi bằng ngôn ngữ tự nhiên. Trợ lý AI tự động sinh SQL,
                truy vấn dữ liệu và trả về insight.
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)