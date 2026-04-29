"""
ui/components.py
Widget dùng chung cho toàn bộ ứng dụng Asset Tracker
"""
import streamlit as st
import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)


def inject_custom_css():
    """Inject CSS tùy chỉnh giao diện."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
        --navy: #1E3A5F;
        --blue: #2563EB;
        --teal: #0EA5E9;
        --amber: #F59E0B;
        --red: #EF4444;
        --green: #10B981;
        --bg: #F8FAFC;
        --surface: #FFFFFF;
        --border: #E2E8F0;
        --text: #1E293B;
        --muted: #64748B;
    }

    html, body, [class*="css"] {
        font-family: 'Be Vietnam Pro', sans-serif !important;
        color: var(--text);
    }

    .stApp { background: var(--bg); }

    /* Header */
    .app-header {
        background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 60%, #0EA5E9 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 4px 20px rgba(37,99,235,0.25);
    }
    .app-header h1 {
        color: white !important;
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .app-header p { color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem; }

    /* Metric Cards */
    .metric-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .metric-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
    .metric-card .accent {
        position: absolute; top: 0; left: 0; width: 4px;
        height: 100%; border-radius: 12px 0 0 12px;
    }
    .metric-card .label { font-size: 0.78rem; color: var(--muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: var(--navy); line-height: 1.1; margin-top: 4px; }
    .metric-card .sub { font-size: 0.8rem; color: var(--muted); margin-top: 4px; }

    /* Status badges */
    .badge {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 3px 10px; border-radius: 100px;
        font-size: 0.75rem; font-weight: 600; white-space: nowrap;
    }
    .badge-green { background: #DCFCE7; color: #15803D; }
    .badge-blue  { background: #DBEAFE; color: #1D4ED8; }
    .badge-amber { background: #FEF3C7; color: #D97706; }
    .badge-red   { background: #FEE2E2; color: #DC2626; }
    .badge-gray  { background: #F1F5F9; color: #475569; }

    /* Alert boxes */
    .alert-warning {
        background: #FFFBEB; border: 1px solid #FDE68A;
        border-left: 4px solid var(--amber);
        border-radius: 8px; padding: 0.9rem 1rem; margin: 0.5rem 0;
    }
    .alert-danger {
        background: #FEF2F2; border: 1px solid #FECACA;
        border-left: 4px solid var(--red);
        border-radius: 8px; padding: 0.9rem 1rem; margin: 0.5rem 0;
    }
    .alert-success {
        background: #F0FDF4; border: 1px solid #BBF7D0;
        border-left: 4px solid var(--green);
        border-radius: 8px; padding: 0.9rem 1rem; margin: 0.5rem 0;
    }
    .alert-info {
        background: #EFF6FF; border: 1px solid #BFDBFE;
        border-left: 4px solid var(--blue);
        border-radius: 8px; padding: 0.9rem 1rem; margin: 0.5rem 0;
    }

    /* Section headers */
    .section-header {
        display: flex; align-items: center; gap: 0.5rem;
        font-size: 1.05rem; font-weight: 700; color: var(--navy);
        border-bottom: 2px solid var(--border);
        padding-bottom: 0.5rem; margin-bottom: 1rem;
    }

    /* Ticket card */
    .ticket-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 10px; padding: 1rem; margin-bottom: 0.7rem;
    }
    .ticket-id { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--muted); }

    /* Form styling */
    .stSelectbox label, .stTextInput label, .stDateInput label,
    .stNumberInput label, .stTextArea label {
        font-weight: 500 !important; font-size: 0.87rem !important; color: var(--navy) !important;
    }

    /* Button */
    .stButton > button {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        color: white !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important;
        padding: 0.5rem 1.2rem !important; transition: all 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 0.9rem; }
    .stTabs [aria-selected="true"] { color: var(--blue) !important; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: var(--navy) !important; }
    [data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
    [data-testid="stSidebar"] .stSelectbox label { color: rgba(255,255,255,0.7) !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #F1F5F9; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render header ứng dụng."""
    st.markdown("""
    <div class="app-header">
        <div style="font-size:2.2rem">📦</div>
        <div>
            <h1>Asset Tracker</h1>
            <p>Hệ thống quản lý tài sản & thiết bị văn phòng</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value, sub: str = "", color: str = "#2563EB"):
    """Hiển thị metric card."""
    return f"""
    <div class="metric-card">
        <div class="accent" style="background:{color}"></div>
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """


def status_badge(status: str) -> str:
    """Trả về HTML badge theo trạng thái."""
    mapping = {
        "Đang sử dụng": ("badge-green", "●"),
        "Kho dự phòng": ("badge-blue", "◉"),
        "Đang bảo hành": ("badge-amber", "⚙"),
        "Hỏng / Chờ xử lý": ("badge-red", "✕"),
        "Đã thanh lý": ("badge-gray", "—"),
    }
    cls, icon = mapping.get(status, ("badge-gray", "?"))
    return f'<span class="badge {cls}">{icon} {status}</span>'


def warranty_days_remaining(warranty_end_date) -> int:
    """Tính số ngày còn lại của bảo hành."""
    try:
        if isinstance(warranty_end_date, str):
            warranty_end_date = date.fromisoformat(warranty_end_date)
        return (warranty_end_date - date.today()).days
    except Exception:
        return -999


def format_currency(amount) -> str:
    """Định dạng tiền tệ VNĐ."""
    try:
        return f"{float(amount):,.0f} ₫"
    except Exception:
        return "—"


def format_date(d) -> str:
    """Định dạng ngày tháng."""
    try:
        if isinstance(d, str):
            d = date.fromisoformat(d)
        return d.strftime("%d/%m/%Y")
    except Exception:
        return str(d) if d else "—"


def show_error(msg: str = "Hệ thống đang xử lý, vui lòng thử lại."):
    st.markdown(f'<div class="alert-danger">⚠️ {msg}</div>', unsafe_allow_html=True)


def show_success(msg: str):
    st.markdown(f'<div class="alert-success">✅ {msg}</div>', unsafe_allow_html=True)


def show_warning(msg: str):
    st.markdown(f'<div class="alert-warning">⚠️ {msg}</div>', unsafe_allow_html=True)


def show_info(msg: str):
    st.markdown(f'<div class="alert-info">ℹ️ {msg}</div>', unsafe_allow_html=True)


def section_header(icon: str, title: str):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)


def render_db_status():
    """Hiển thị trạng thái kết nối DB ở sidebar."""
    from tools.db import is_connected
    if is_connected():
        st.sidebar.markdown(
            '<div style="background:rgba(16,185,129,0.15);border-radius:6px;padding:6px 10px;font-size:0.8rem;">🟢 Neon DB: Đã kết nối</div>',
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            '<div style="background:rgba(245,158,11,0.15);border-radius:6px;padding:6px 10px;font-size:0.8rem;">🟡 DB: Bộ nhớ tạm</div>',
            unsafe_allow_html=True
        )


def render_llm_status():
    """Hiển thị trạng thái LLM ở sidebar."""
    from core.llm import check_llm_available
    if check_llm_available():
        st.sidebar.markdown(
            '<div style="background:rgba(37,99,235,0.15);border-radius:6px;padding:6px 10px;font-size:0.8rem;">🤖 AI: Gemini sẵn sàng</div>',
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            '<div style="background:rgba(239,68,68,0.15);border-radius:6px;padding:6px 10px;font-size:0.8rem;">⚪ AI: Chưa cấu hình API key</div>',
            unsafe_allow_html=True
        )
