import streamlit as st
import duckdb
import pandas as pd
from groq import Groq
import re
import uuid
from datetime import datetime
from groq import RateLimitError

# ==========================================
# CẤU HÌNH & KẾT NỐI
# ==========================================
st.set_page_config(
    page_title="Trợ lý GenBI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

TOKEN = st.secrets["MOTHERDUCK_TOKEN"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]


@st.cache_resource
def get_duckdb_connection():
    return duckdb.connect(f"md:shopping_db?token={TOKEN}")


conn = get_duckdb_connection()
client = Groq(api_key=GROQ_API_KEY)


# ==========================================
# QUẢN LÝ DATABASE (MOTHERDUCK)
# ==========================================
def init_chat_db():
    conn.execute("""
        CREATE TABLE IF NOT EXISTS main.genbi_chat_history (
            chat_id VARCHAR,
            role VARCHAR,
            content TEXT,
            sql_query TEXT,
            created_at TIMESTAMP
        )
    """)


def load_all_conversations():
    df = conn.execute("SELECT * FROM main.genbi_chat_history ORDER BY created_at ASC").df()
    conversations = {}
    for _, row in df.iterrows():
        cid = row['chat_id']
        if cid not in conversations:
            conversations[cid] = []

        msg = {"role": row['role'], "content": row['content']}
        if pd.notna(row['sql_query']) and str(row['sql_query']).strip() != "":
            msg["sql"] = row['sql_query']

        conversations[cid].append(msg)
    return conversations


def save_message_to_db(chat_id, role, content, sql_query=""):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        "INSERT INTO main.genbi_chat_history VALUES (?, ?, ?, ?, ?)",
        [chat_id, role, content, sql_query, now]
    )


def delete_chat_from_db(chat_id):
    conn.execute("DELETE FROM main.genbi_chat_history WHERE chat_id = ?", [chat_id])


init_chat_db()

# ==========================================
# LƯỢC ĐỒ VÀ XỬ LÝ AI
# ==========================================
GOLD_SCHEMA = """
Tầng Gold của Data Warehouse gồm 3 bảng (schema 'main'):

1. main.fact_sessions:
- session_id: ID phiên (PK).
- visitor_key: ID khách truy cập.
- time_key: khóa ngoại nối tới dim_time.
- Administrative, Administrative_Duration, Informational, Informational_Duration, ProductRelated, ProductRelated_Duration: số lượt xem & thời gian xem.
- BounceRates, ExitRates: tỷ lệ thoát (0-1).
- PageValues: giá trị trang (0 nếu chưa từng dẫn tới mua hàng).
- has_page_value: TRUE nếu PageValues > 0.
- is_bad_rate: TRUE nếu bounce/exit rate cao bất thường.
- is_revenue: 1 = session dẫn tới mua hàng, 0 = không.

2. main.dim_time:
- time_key: khóa (PK).
- Month: tháng dạng text viết tắt.
- Weekend: TRUE/FALSE - session diễn ra vào cuối tuần.
- SpecialDay: hệ số gần ngày đặc biệt (0-1).
- holiday_proximity: "No holiday" / "Near holiday" / "Holiday or very close".

3. main.ai_predictions:
- source_index: tương ứng với fact_sessions.session_id.
- Month: tháng.
- VisitorType: "New_Visitor" / "Returning_Visitor" / "Other".
- predicted_probability: xác suất mua hàng dự đoán (0-1).
- prediction_label: "will_buy" / "will_not_buy".
- conversion_priority: "high_priority" / "medium_priority" / "low_priority".
- recommended_action: hành động đề xuất (text tiếng Việt).
- top_positive_shap_reasons, top_negative_shap_reasons, strongest_shap_reason: giải thích lý do dự đoán (SHAP).
- actual_revenue / predicted_revenue: 1 = có mua / dự đoán mua, 0 = không.

QUY TẮC CHỌN BẢNG & JOIN:
- Không tính toán doanh thu tiền tệ.
- Nếu hỏi về số liệu không có, trả về: SELECT 'NO_DATA' AS message;
- Data không có cột năm, nếu hỏi tháng gần nhất trả về query Group By Month.
"""

FEW_SHOT = """
Ví dụ:
Câu hỏi: "Tháng 5 có bao nhiêu lượt truy cập (session)?"
SQL: SELECT COUNT(*) AS total_sessions FROM main.fact_sessions f JOIN main.dim_time d ON f.time_key = d.time_key WHERE d.Month = 'May';

Câu hỏi: "Khách hàng nào sắp rời bỏ giỏ hàng / có rủi ro không mua?"
SQL: SELECT source_index, VisitorType, predicted_probability, recommended_action FROM main.ai_predictions WHERE prediction_label = 'will_not_buy' ORDER BY predicted_probability DESC;
"""


def get_sql_from_llama(user_query, chat_history=None):
    system_prompt = f"Bạn là Data Analyst. Schema:\n{GOLD_SCHEMA}\n{FEW_SHOT}\nTrả về duy nhất mã SQL (DuckDB), tiền tố 'main.', không markdown."
    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        for msg in chat_history[-6:]:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant" and "sql" in msg:
                messages.append({"role": "assistant", "content": msg['sql']})

    messages.append({"role": "user", "content": user_query})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1
        )
    except RateLimitError:
        return None

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```[sS][qQ][lL]?\n|```", "", raw).strip()
    raw = re.sub(r"^(SQL\s*(đã dùng)?\s*:?\s*)+", "", raw, flags=re.IGNORECASE).strip()
    match = re.search(r"(SELECT|WITH)\b.*?;", raw, re.IGNORECASE | re.DOTALL)
    if match:
        raw = match.group(0)
    else:
        match2 = re.search(r"(SELECT|WITH)\b.*", raw, re.IGNORECASE | re.DOTALL)
        if match2:
            raw = match2.group(0).strip()
    return raw.strip()


def execute_query(sql_query):
    sql_clean = sql_query.strip()
    lines = sql_clean.split("\n")
    while lines and (lines[0].strip() == "" or lines[0].strip().startswith("--")):
        lines.pop(0)
    sql_clean = "\n".join(lines).strip()

    if not re.match(r"^\s*(SELECT|WITH)\s", sql_clean, re.IGNORECASE):
        return None, f"Chỉ cho phép câu lệnh SELECT. (SQL nhận được: {sql_clean[:100]})"
    try:
        return conn.execute(sql_clean).df(), None
    except Exception as e:
        return None, str(e)


def get_natural_answer(user_query, sql_query, df_result, chat_history=None):
    data_preview = df_result.head(20).to_string(index=False)
    context_text = ""
    if chat_history:
        recent = chat_history[-4:]
        lines = []
        for msg in recent:
            if msg["role"] == "user":
                lines.append(f"- Người dùng đã hỏi trước đó: {msg['content']}")
            elif msg["role"] == "assistant":
                lines.append(f"- Bạn đã trả lời: {msg['content']}")
        if lines:
            context_text = "Bối cảnh hội thoại trước đó:\n" + "\n".join(lines) + "\n\n"

    prompt = f"""{context_text}Người dùng hỏi: "{user_query}"\nSQL đã chạy: {sql_query}\nKết quả trả về:\n{data_preview}\n\nDựa vào kết quả trên, hãy trả lời ngắn gọn 1-3 câu, nêu số liệu. Chỉ dùng số liệu có trong kết quả."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        return "⚠️ Hệ thống đã đạt giới hạn sử dụng AI. Dưới đây là bảng kết quả thô."


# ==========================================
# GIAO DIỆN (UI/UX) - ĐỒNG BỘ DASHBOARD
# ==========================================
custom_css = """
<style>
    /* 1. Ẩn Sidebar và Header rác của Streamlit */
    [data-testid="stSidebar"], 
    [data-testid="collapsedControl"],
    .stAppDeployButton,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"] {
        display: none !important;
    }

    /* 2. Nền tảng tổng thể & Container chuẩn Dashboard */
    .stApp {
        background:
            radial-gradient(circle at 10% 8%, rgba(0,194,212,0.12), transparent 26%),
            radial-gradient(circle at 90% 0%, rgba(26,58,107,0.16), transparent 28%),
            linear-gradient(135deg, #f8fbff 0%, #eef3f8 45%, #e8f6f8 100%);
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        max-width: 100% !important;
        padding: 1.2rem 4rem 2.5rem 4rem !important; 
    }

    /* 3. NÚT BẤM CHUNG - ĐÃ FIX ALIGNMENT VÀ MOBILE */
    div.stButton > button {
        width: auto;
        /* Đã xóa min-width: 150px để nút không bị ép dài ra trên điện thoại */
        height: 44px;
        border-radius: 999px !important;
        border: 1px solid rgba(0,194,212,0.28) !important;
        background: rgba(255,255,255,0.92) !important;
        color: #1A3A6B !important;
        font-size: 15px;
        font-weight: 800;
        padding: 0 24px; /* Tăng padding ngang để nhìn cân đối thay cho min-width */
        box-shadow: 0 12px 28px rgba(26, 58, 107, 0.10) !important;
        transition: 0.25s ease;

        /* FIX LỆCH: Ép tất cả các nút cùng 1 kiểu hiển thị để thẳng hàng nhau */
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        border-color: #00C2D4 !important;
        color: #1A3A6B !important;
        box-shadow: 0 18px 38px rgba(26, 58, 107, 0.18) !important;
    }

    div.stButton > button p {
        color: #1A3A6B !important;
        font-weight: 800 !important;
        margin: 0 !important; /* Xóa margin thừa của text bên trong */
    }

    /* Nút Primary */
    div.stButton > button[kind="primary"],
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #1A3A6B 0%, #00C2D4 100%) !important;
        border: none !important;
        box-shadow: 0 4px 18px rgba(0,194,212,0.25) !important;
    }
    div.stButton > button[kind="primary"] p,
    div.stButton > button[data-testid="baseButton-primary"] p {
        color: white !important;
    }

    /* 4. KHUNG MENU SIDEBAR */
    @keyframes slideRight {
        from { opacity: 0; transform: translateX(-16px); }
        to   { opacity: 1; transform: translateX(0); }
    }

    [data-testid="column"]:has(.menu-identifier) {
        background: linear-gradient(170deg, #ffffff 0%, #f0f7ff 100%) !important;
        border: 1px solid rgba(0,194,212,0.28) !important;
        border-radius: 24px !important;
        padding: 20px 14px !important;
        box-shadow: 0 8px 32px rgba(26,58,107,0.10) !important;
        animation: slideRight 0.3s ease forwards;
    }

    [data-testid="column"]:has(.menu-identifier) div.stButton > button {
        min-width: 0 !important;
        font-size: 13px !important;
    }

    .menu-section-divider {
        border: none;
        border-top: 1.5px solid rgba(0,194,212,0.22);
        margin: 14px 0 10px 0;
    }

    /* Ép text nút Lịch sử sang trái */
    [data-testid="column"]:has(.menu-identifier) [data-testid="column"]:first-child div.stButton > button {
        justify-content: flex-start !important;
        padding-left: 18px !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
    }

    /* 5. GIAO DIỆN CHAT */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0,194,212,0.18);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 18px 45px rgba(26, 58, 107, 0.08);
        margin-bottom: 24px;
    }

    [data-testid="stChatInput"] {
        border-radius: 24px !important;
        border: 1px solid rgba(0,194,212,0.4) !important;
        box-shadow: 0 14px 38px rgba(26, 58, 107, 0.12) !important;
        background: rgba(255,255,255,0.95) !important;
    }

    [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
        padding-bottom: 30px !important;
    }

    [data-testid="stExpander"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,251,255,0.96));
        border: 1px solid rgba(0,194,212,0.18);
        border-radius: 24px;
        box-shadow: 0 16px 42px rgba(26, 58, 107, 0.10);
        margin-top: 15px;
    }

    /* 6. BANNER HERO */
    .dashboard-hero {
        position: relative;
        overflow: hidden;
        width: 100%;
        min-height: 285px; 
        background: linear-gradient(
            90deg, #1A3A6B 0%, #00C2D4 25%, #1A3A6B 50%, #00C2D4 75%, #1A3A6B 100%
        );
        background-size: 200% 100%;
        border-radius: 32px;
        padding: clamp(32px, 4vw, 56px) clamp(24px, 5vw, 72px); 
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
    .hero-badge {
        width: fit-content;
        padding: 10px 16px;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(0,194,212,0.42);
        font-size: clamp(12px, 1.5vw, 14px);
        font-weight: 700;
        margin-bottom: 22px;
        backdrop-filter: blur(12px);
    }
    .hero-title {
        font-size: clamp(32px, 5vw, 58px); 
        font-weight: 850;
        letter-spacing: -2px;
        margin-bottom: 16px;
        line-height: 1.05;
    }
    .hero-subtitle {
        font-size: clamp(15px, 2vw, 20px); 
        color: #d9fbff;
        max-width: 980px;
        line-height: 1.6;
    }

    /* ĐẢM BẢO KHÔNG VỠ TRÊN ĐIỆN THOẠI */
    @media (max-width: 992px) {
        .block-container {
            padding: 1rem 2rem 2rem 2rem !important;
        }
        .dashboard-hero {
            border-radius: 24px;
            min-height: auto;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 0.8rem 1rem 1.5rem 1rem !important;
        }
        .dashboard-hero {
            border-radius: 20px;
        }
    }

    @keyframes heroFade {
        from { opacity: 0; transform: translateY(26px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes gradientMove {
        from { background-position: 0% 50%; }
        to { background-position: 200% 50%; }
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# JS inject để chỉnh kích thước cụ thể cho nút icon (☰ và ✕)
# Chú ý: display đã được cấu hình trong CSS ở trên, không bị đá nhau nữa.
st.markdown("""
<script>
(function patchUI() {
    function applyPatches() {
        document.querySelectorAll('button').forEach(function(btn) {
            var title = btn.getAttribute('title') || '';
            var txt = btn.innerText.trim();

            if (title === 'Toggle Menu' || txt === '☰') {
                btn.style.cssText += [
                    'min-width:44px!important',
                    'max-width:44px!important',
                    'width:44px!important',
                    'height:44px!important',
                    'padding:0!important',
                    'border-radius:14px!important'
                ].join(';');
            }

            if (title === 'Xóa' || txt === '✕') {
                btn.style.cssText += [
                    'min-width:30px!important',
                    'max-width:30px!important',
                    'width:30px!important',
                    'height:30px!important',
                    'padding:0!important',
                    'border-radius:50%!important',
                    'background:rgba(220,50,50,0.08)!important',
                    'border:1.5px solid rgba(220,50,50,0.32)!important',
                    'box-shadow:none!important',
                    'font-size:12px!important',
                    'color:#bb2222!important'
                ].join(';');
                var p = btn.querySelector('p');
                if (p) p.style.color = '#bb2222';
            }
        });
    }

    applyPatches();
    var observer = new MutationObserver(function() { applyPatches(); });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

# ==========================================
# KHỞI TẠO STATE
# ==========================================
if "conversations" not in st.session_state:
    loaded_chats = load_all_conversations()
    if not loaded_chats:
        default_id = str(uuid.uuid4())
        st.session_state.conversations = {default_id: []}
        st.session_state.current_chat_id = default_id
    else:
        st.session_state.conversations = loaded_chats
        st.session_state.current_chat_id = list(loaded_chats.keys())[-1]

if "show_custom_menu" not in st.session_state:
    st.session_state.show_custom_menu = True

# ==========================================
# HAI NÚT TRÊN CÙNG BÊN TRÁI
# ==========================================
# Căn giữa vertical và tùy chỉnh tỷ lệ an toàn
nav_col1, nav_col2, nav_empty = st.columns([0.4, 2.0, 7.6], vertical_alignment="center")

with nav_col1:
    # LƯU Ý: KHÔNG dùng use_container_width=True ở đây để nút không dài ra trên đt
    if st.button("☰", help="Toggle Menu"):
        st.session_state.show_custom_menu = not st.session_state.show_custom_menu
        st.rerun()

with nav_col2:
    if st.button("← Về trang chủ", use_container_width=True):
        st.switch_page("app.py")

st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

# ==========================================
# BỐ CỤC CHÍNH
# ==========================================
if st.session_state.show_custom_menu:
    menu_col, main_col = st.columns([1.1, 4.9], gap="large")
else:
    main_col = st.container()
    menu_col = None

# --- VÙNG 1: FAKE SIDEBAR MENU ---
if menu_col is not None:
    with menu_col:
        st.markdown("<div class='menu-identifier'></div>", unsafe_allow_html=True)

        if st.button("➕ Cuộc trò chuyện mới", use_container_width=True, type="primary"):
            new_id = str(uuid.uuid4())
            st.session_state.conversations[new_id] = []
            st.session_state.current_chat_id = new_id
            st.rerun()

        st.markdown(
            "<hr class='menu-section-divider'><h4 style='color:#1A3A6B;font-weight:800;font-size:12px;letter-spacing:0.8px;margin:0 0 10px 0;opacity:0.75;'>LỊCH SỬ HỘI THOẠI</h4>",
            unsafe_allow_html=True)

        chats_to_delete = []
        for chat_id, messages in st.session_state.conversations.items():
            chat_title = "Đoạn chat mới"
            if len(messages) > 0 and messages[0]["role"] == "user":
                chat_title = messages[0]["content"][:32] + "…"

            is_active = (chat_id == st.session_state.current_chat_id)

            # Căn giữa thẳng hàng nút Lịch sử và nút Xóa
            c1, c2 = st.columns([4.5, 1], vertical_alignment="center")

            with c1:
                if st.button(chat_title, key=f"btn_{chat_id}", type="primary" if is_active else "secondary",
                             use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with c2:
                # LƯU Ý: KHÔNG dùng use_container_width=True để nút Xóa không bị kéo giãn
                if st.button("✕", key=f"del_{chat_id}", help="Xóa"):
                    chats_to_delete.append(chat_id)

        for cid in chats_to_delete:
            delete_chat_from_db(cid)
            del st.session_state.conversations[cid]
            if cid == st.session_state.current_chat_id:
                if st.session_state.conversations:
                    st.session_state.current_chat_id = list(st.session_state.conversations.keys())[-1]
                else:
                    new_id = str(uuid.uuid4())
                    st.session_state.conversations = {new_id: []}
                    st.session_state.current_chat_id = new_id
            st.rerun()

# --- VÙNG 2: MAIN CONTENT (CHAT AREA) ---
with main_col:
    st.markdown("""
    <div class="dashboard-hero">
        <div class="hero-content">
            <div class="hero-badge">🤖 AI Data Assistant</div>
            <div class="hero-title">Trợ lý Phân tích GenBI</div>
            <div class="hero-subtitle">
                Khám phá dữ liệu truy cập, phân tích chuyển đổi và dự báo hành vi mua hàng tự động.<br>
                Đặt câu hỏi bằng ngôn ngữ tự nhiên để truy xuất trực tiếp từ Lakehouse.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    current_chat_id = st.session_state.current_chat_id
    current_messages = st.session_state.conversations[current_chat_id]

    # Khởi tạo container để gom toàn bộ tin nhắn vào một khối
    chat_container = st.container()

    # Render lịch sử tin nhắn vào container
    with chat_container:
        for msg in current_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "sql" in msg:
                    with st.expander("🔍 Xem mã SQL DuckDB"):
                        st.code(msg["sql"], language="sql")
                        df_old, _ = execute_query(msg["sql"])
                        if df_old is not None:
                            st.dataframe(df_old, use_container_width=True)

    # Khung nhập chat
    if user_input := st.chat_input("Nhập câu hỏi phân tích dữ liệu của bạn tại đây..."):
        save_message_to_db(current_chat_id, "user", user_input)
        current_messages.append({"role": "user", "content": user_input})

        # Render tin nhắn MỚI
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Đang phân tích cấu trúc dữ liệu..."):
                    sql_generated = get_sql_from_llama(user_input, current_messages)

                if sql_generated is None:
                    err_msg = "⚠️ Hệ thống đã đạt giới hạn sử dụng AI. Vui lòng thử lại sau."
                    st.error(err_msg)
                    save_message_to_db(current_chat_id, "assistant", err_msg)
                    current_messages.append({"role": "assistant", "content": err_msg})
                else:
                    with st.spinner("Đang truy vấn Data Warehouse..."):
                        df_result, error = execute_query(sql_generated)

                    if error:
                        err_msg = f"Lỗi truy vấn: `{error}`"
                        st.error(err_msg)
                        save_message_to_db(current_chat_id, "assistant", err_msg, sql_generated)
                        current_messages.append({"role": "assistant", "content": err_msg, "sql": sql_generated})
                    else:
                        with st.spinner("Đang tổng hợp câu trả lời..."):
                            if df_result.empty:
                                answer_text = "Không tìm thấy dữ liệu phù hợp với câu hỏi của bạn."
                            elif "message" in df_result.columns and len(df_result) == 1 and df_result.iloc[0][
                                "message"] == "NO_DATA":
                                answer_text = "Xin lỗi, Data Warehouse hiện không có dữ liệu để trả lời câu hỏi này (ví dụ: doanh thu, thông tin cá nhân khách hàng). Hệ thống chỉ lưu dữ liệu hành vi truy cập và dự đoán chuyển đổi."
                            else:
                                answer_text = get_natural_answer(user_input, sql_generated, df_result, current_messages)

                        st.markdown(answer_text)

                        if not df_result.empty and not (
                                "message" in df_result.columns and len(df_result) == 1 and df_result.iloc[0][
                            "message"] == "NO_DATA"):
                            st.dataframe(df_result, use_container_width=True)

                        with st.expander("🔍 Xem mã SQL DuckDB"):
                            st.code(sql_generated, language="sql")

                        save_message_to_db(current_chat_id, "assistant", answer_text, sql_generated)
                        current_messages.append({
                            "role": "assistant",
                            "content": answer_text,
                            "sql": sql_generated
                        })