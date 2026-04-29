"""
app.py — Asset Tracker Entry Point
Tab 1: Danh sách tài sản
Tab 2: Bàn giao & Thu hồi
Tab 3: Theo dõi bảo hành
Tab 4: Dashboard & Báo cáo + AI Trợ lý
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path

# ── Setup paths ───────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# ── Logging setup ─────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)

def _setup_logging():
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    app_h = logging.handlers.RotatingFileHandler(
        "logs/app.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
    )
    app_h.setLevel(logging.INFO)
    app_h.setFormatter(fmt)

    err_h = logging.handlers.RotatingFileHandler(
        "logs/error.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
    )
    err_h.setLevel(logging.ERROR)
    err_h.setFormatter(fmt)

    root.addHandler(app_h)
    root.addHandler(err_h)

_setup_logging()
logger = logging.getLogger(__name__)

# ── Imports ───────────────────────────────────────────────
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from ui.components import (
    inject_custom_css, render_header, metric_card, status_badge,
    warranty_days_remaining, format_currency, format_date,
    show_error, show_success, show_warning, show_info,
    section_header, render_db_status, render_llm_status
)
from tools import db
from tools.file_handler import (
    parse_assets_from_excel, export_assets_to_excel,
    generate_qr_code, generate_asset_label_pdf, export_warranty_report
)

# ── Streamlit config ──────────────────────────────────────
st.set_page_config(
    page_title="Asset Tracker",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()

# ── Session state defaults ────────────────────────────────
if "selected_asset_id" not in st.session_state:
    st.session_state.selected_asset_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ══════════════════════════════════════════════════════════
# TAB 1 · DANH SÁCH TÀI SẢN
# ══════════════════════════════════════════════════════════

def render_tab_asset_list():
    col_filter, col_main = st.columns([1, 3])

    with col_filter:
        section_header("🔍", "Bộ lọc")
        import yaml
        with open("config/settings.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        cats = ["Tất cả"] + cfg["asset"]["categories"]
        depts = ["Tất cả"] + cfg["asset"]["departments"]
        statuses = ["Tất cả"] + cfg["asset"]["statuses"]

        cat_filter = st.selectbox("Loại tài sản", cats, key="f_cat")
        dept_filter = st.selectbox("Phòng ban", depts, key="f_dept")
        stat_filter = st.selectbox("Trạng thái", statuses, key="f_stat")
        search = st.text_input("🔎 Tìm kiếm", placeholder="Tên, serial, người dùng...", key="f_search")

        st.divider()
        section_header("📥", "Nhập từ Excel")
        uploaded = st.file_uploader("Tải file danh sách tài sản", type=["xlsx"], key="ul_assets")
        if uploaded and st.button("📤 Nhập tài sản", use_container_width=True):
            try:
                assets_data = parse_assets_from_excel(uploaded.read())
                if assets_data:
                    count = 0
                    for a in assets_data:
                        if db.create_asset(a):
                            count += 1
                    show_success(f"Nhập thành công {count} tài sản!")
                    logger.info(f"Import {count} assets from Excel")
                    st.rerun()
                else:
                    show_warning("Không đọc được dữ liệu từ file. Kiểm tra lại định dạng cột.")
            except Exception as e:
                logger.error(f"Import Excel error: {e}")
                st.error(str(e))
                #show_error()

    with col_main:
        # Action buttons
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            section_header("📋", "Danh sách tài sản")
        with c2:
            if st.button("➕ Thêm tài sản", use_container_width=True):
                st.session_state.show_add_form = True
        with c3:
            assets_all = db.get_all_assets()
            excel_bytes = export_assets_to_excel(assets_all)
            st.download_button(
                "📥 Xuất Excel",
                data=excel_bytes,
                file_name="danh_sach_tai_san.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        # Add form
        if st.session_state.get("show_add_form"):
            _render_add_asset_form(cfg)

        # Filter
        assets = db.get_all_assets()
        if cat_filter != "Tất cả":
            assets = [a for a in assets if a.get("category") == cat_filter]
        if dept_filter != "Tất cả":
            assets = [a for a in assets if a.get("department") == dept_filter]
        if stat_filter != "Tất cả":
            assets = [a for a in assets if a.get("status") == stat_filter]
        if search:
            q = search.lower()
            assets = [a for a in assets if
                      q in (a.get("name") or "").lower() or
                      q in (a.get("serial_number") or "").lower() or
                      q in (a.get("assigned_to") or "").lower() or
                      q in (a.get("id") or "").lower()]

        if not assets:
            show_info("Không có tài sản nào phù hợp. Thêm tài sản mới hoặc nhập từ Excel.")
            return

        # Table header
        st.markdown(f"<p style='color:#64748B;font-size:0.85rem;'>Tìm thấy <b>{len(assets)}</b> tài sản</p>", unsafe_allow_html=True)

        for asset in assets:
            _render_asset_row(asset, cfg)


def _render_add_asset_form(cfg):
    """Form thêm tài sản mới."""
    with st.expander("➕ THÊM TÀI SẢN MỚI", expanded=True):
        with st.form("form_add_asset"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Tên tài sản *", placeholder="VD: Laptop Dell XPS 13")
                category = st.selectbox("Loại tài sản", cfg["asset"]["categories"])
                serial = st.text_input("Số Serial", placeholder="VD: SN-2024-001")
                purchase_price = st.number_input("Giá mua (VNĐ)", min_value=0, step=100000)
            with c2:
                purchase_date = st.date_input("Ngày mua")
                warranty_end = st.date_input("Hết bảo hành")
                status = st.selectbox("Trạng thái", cfg["asset"]["statuses"])
                location = st.text_input("Vị trí", placeholder="VD: Tầng 3, Phòng IT")
            dept = st.selectbox("Phòng ban", cfg["asset"]["departments"])
            assigned_to = st.text_input("Người dùng", placeholder="Để trống nếu chưa bàn giao")
            notes = st.text_area("Ghi chú", height=80)

            if st.form_submit_button("💾 Lưu tài sản", use_container_width=True):
                if not name:
                    show_warning("Vui lòng nhập tên tài sản.")
                else:
                    try:
                        result = db.create_asset({
                            "name": name, "category": category, "serial_number": serial,
                            "purchase_date": purchase_date.isoformat(),
                            "warranty_end_date": warranty_end.isoformat(),
                            "status": status, "department": dept, "assigned_to": assigned_to,
                            "location": location, "purchase_price": purchase_price, "notes": notes,
                        })
                        if result:
                            show_success(f"Đã thêm tài sản: {name} (ID: {result['id']})")
                            st.session_state.show_add_form = False
                            logger.info(f"Created asset: {result['id']} - {name}")
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Add asset error: {e}")
                        show_error()


def _render_asset_row(asset: dict, cfg: dict):
    """Render một hàng tài sản."""
    days = warranty_days_remaining(asset.get("warranty_end_date"))
    warranty_icon = "🔴" if days < 0 else ("🟡" if days <= 30 else "🟢")

    with st.container():
        st.markdown(f"""
        <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;
                    padding:0.8rem 1rem;margin-bottom:0.5rem;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;">
                <div style="flex:1;min-width:200px;">
                    <div style="font-weight:700;font-size:0.95rem;color:#1E3A5F;">{asset.get('name','')}</div>
                    <div style="font-size:0.78rem;color:#64748B;margin-top:2px;">
                        🏷️ {asset.get('id','')} &nbsp;|&nbsp;
                        📁 {asset.get('category','')} &nbsp;|&nbsp;
                        📟 {asset.get('serial_number') or '—'}
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
                    {status_badge(asset.get('status',''))}
                    <span style="font-size:0.78rem;color:#64748B;">
                        {warranty_icon} BH: {format_date(asset.get('warranty_end_date'))}
                        ({days} ngày)
                    </span>
                </div>
            </div>
            <div style="display:flex;gap:1.5rem;margin-top:0.5rem;flex-wrap:wrap;font-size:0.8rem;color:#475569;">
                <span>🏢 {asset.get('department') or '—'}</span>
                <span>👤 {asset.get('assigned_to') or 'Chưa bàn giao'}</span>
                <span>📍 {asset.get('location') or '—'}</span>
                <span>💰 {format_currency(asset.get('purchase_price',0))}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c2:
            qr_bytes = generate_qr_code(asset["id"], asset["name"])
            if qr_bytes:
                st.download_button(
                    "🔲 QR Code",
                    data=qr_bytes,
                    file_name=f"qr_{asset['id']}.png",
                    mime="image/png",
                    key=f"qr_{asset['id']}",
                    use_container_width=True,
                )
        with c3:
            pdf_bytes = generate_asset_label_pdf(asset)
            if pdf_bytes:
                st.download_button(
                    "🏷️ Nhãn PDF",
                    data=pdf_bytes,
                    file_name=f"label_{asset['id']}.pdf",
                    mime="application/pdf",
                    key=f"lbl_{asset['id']}",
                    use_container_width=True,
                )
        with c4:
            if st.button("✏️ Sửa", key=f"edit_{asset['id']}", use_container_width=True):
                st.session_state[f"edit_{asset['id']}"] = True

        if st.session_state.get(f"edit_{asset['id']}"):
            _render_edit_form(asset, cfg)


def _render_edit_form(asset: dict, cfg: dict):
    """Form chỉnh sửa tài sản."""
    with st.expander(f"✏️ Chỉnh sửa: {asset['name']}", expanded=True):
        with st.form(f"edit_form_{asset['id']}"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Tên tài sản", value=asset.get("name", ""))
                cat_idx = cfg["asset"]["categories"].index(asset.get("category", cfg["asset"]["categories"][0])) if asset.get("category") in cfg["asset"]["categories"] else 0
                category = st.selectbox("Loại", cfg["asset"]["categories"], index=cat_idx)
                serial = st.text_input("Serial", value=asset.get("serial_number", ""))
            with c2:
                stat_idx = cfg["asset"]["statuses"].index(asset.get("status", cfg["asset"]["statuses"][0])) if asset.get("status") in cfg["asset"]["statuses"] else 0
                status = st.selectbox("Trạng thái", cfg["asset"]["statuses"], index=stat_idx)
                dept_idx = cfg["asset"]["departments"].index(asset.get("department", cfg["asset"]["departments"][0])) if asset.get("department") in cfg["asset"]["departments"] else 0
                dept = st.selectbox("Phòng ban", cfg["asset"]["departments"], index=dept_idx)
                assigned_to = st.text_input("Người dùng", value=asset.get("assigned_to", ""))
            notes = st.text_area("Ghi chú", value=asset.get("notes", ""), height=80)

            col_save, col_del = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 Lưu thay đổi", use_container_width=True):
                    try:
                        db.update_asset(asset["id"], {
                            "name": name, "category": category, "serial_number": serial,
                            "status": status, "department": dept, "assigned_to": assigned_to, "notes": notes,
                        })
                        show_success("Đã cập nhật tài sản!")
                        st.session_state[f"edit_{asset['id']}"] = False
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Update asset error: {e}")
                        show_error()
            with col_del:
                if st.form_submit_button("🗑️ Xóa tài sản", use_container_width=True):
                    try:
                        db.delete_asset(asset["id"])
                        show_success("Đã xóa tài sản.")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Delete asset error: {e}")
                        show_error()


# ══════════════════════════════════════════════════════════
# TAB 2 · BÀN GIAO & THU HỒI
# ══════════════════════════════════════════════════════════

def render_tab_assignment():
    import yaml
    with open("config/settings.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    assets = db.get_all_assets()
    if not assets:
        show_info("Chưa có tài sản nào. Vui lòng thêm tài sản ở Tab 1.")
        return

    col_form, col_history = st.columns([1, 1])

    with col_form:
        section_header("📋", "Tạo phiếu bàn giao / thu hồi")

        asset_options = {f"{a['id']} — {a['name']}": a["id"] for a in assets}
        selected_label = st.selectbox("Chọn tài sản", list(asset_options.keys()))
        asset_id = asset_options[selected_label]
        asset = next((a for a in assets if a["id"] == asset_id), {})

        # Show asset info
        if asset:
            st.markdown(f"""
            <div class="alert-info" style="font-size:0.82rem;">
                🏷️ <b>{asset.get('name')}</b> &nbsp;|&nbsp;
                {status_badge(asset.get('status',''))} &nbsp;|&nbsp;
                👤 Hiện tại: <b>{asset.get('assigned_to') or 'Chưa bàn giao'}</b>
            </div>
            """, unsafe_allow_html=True)

        with st.form("form_assignment"):
            action = st.selectbox("Hành động", ["Bàn giao", "Thu hồi", "Chuyển phòng ban"])
            employee_name = st.text_input("Tên nhân viên *", placeholder="Nguyễn Văn A")
            dept = st.selectbox("Phòng ban", cfg["asset"]["departments"])
            action_date = st.date_input("Ngày thực hiện")
            notes = st.text_area("Ghi chú", height=80, placeholder="Lý do bàn giao, tình trạng thiết bị...")
            created_by = st.text_input("Người lập phiếu", value="Admin")

            if st.form_submit_button("📝 Tạo phiếu", use_container_width=True):
                if not employee_name:
                    show_warning("Vui lòng nhập tên nhân viên.")
                else:
                    try:
                        record = db.create_assignment({
                            "asset_id": asset_id,
                            "employee_name": employee_name,
                            "department": dept,
                            "action": action,
                            "action_date": action_date.isoformat(),
                            "notes": notes,
                            "created_by": created_by,
                        })

                        # Cập nhật trạng thái tài sản
                        new_status = "Đang sử dụng" if action == "Bàn giao" else "Kho dự phòng"
                        new_dept = dept if action == "Bàn giao" else asset.get("department", "")
                        new_user = employee_name if action == "Bàn giao" else ""
                        db.update_asset(asset_id, {
                            "status": new_status,
                            "department": new_dept,
                            "assigned_to": new_user,
                        })

                        show_success(f"Đã tạo phiếu {action} — ID: {record['id']}")
                        logger.info(f"Assignment created: {record['id']} - {action} - {asset_id}")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Assignment error: {e}")
                        show_error()

        st.divider()
        section_header("🎫", "Tạo IT Ticket")
        with st.form("form_ticket"):
            t_asset_label = st.selectbox("Tài sản liên quan", list(asset_options.keys()), key="t_asset")
            t_asset_id = asset_options[t_asset_label]
            t_title = st.text_input("Tiêu đề *", placeholder="VD: Yêu cầu đổi màn hình")
            t_desc = st.text_area("Mô tả chi tiết", height=100)
            t_priority = st.selectbox("Mức ưu tiên", ["Thấp", "Trung bình", "Cao", "Khẩn cấp"])
            t_by = st.text_input("Người yêu cầu")

            if st.form_submit_button("🎫 Tạo ticket", use_container_width=True):
                if not t_title:
                    show_warning("Vui lòng nhập tiêu đề ticket.")
                else:
                    try:
                        ticket = db.create_ticket({
                            "asset_id": t_asset_id,
                            "title": t_title,
                            "description": t_desc,
                            "priority": t_priority,
                            "created_by": t_by,
                        })
                        show_success(f"Đã tạo IT Ticket: {ticket['id']}")
                        logger.info(f"IT Ticket created: {ticket['id']}")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Ticket create error: {e}")
                        show_error()

    with col_history:
        section_header("📜", "Lịch sử bàn giao")
        assignments = db.get_all_assignments()
        if not assignments:
            show_info("Chưa có lịch sử bàn giao nào.")
        else:
            for rec in assignments[:20]:
                action_color = {"Bàn giao": "#10B981", "Thu hồi": "#EF4444", "Chuyển phòng ban": "#F59E0B"}.get(rec.get("action", ""), "#64748B")
                st.markdown(f"""
                <div class="ticket-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span class="ticket-id">#{rec.get('id')}</span>
                        <span class="badge" style="background:{action_color}22;color:{action_color};">
                            {rec.get('action')}
                        </span>
                    </div>
                    <div style="margin-top:0.5rem;font-size:0.87rem;font-weight:600;">{rec.get('employee_name')}</div>
                    <div style="font-size:0.78rem;color:#64748B;">
                        🏷️ {rec.get('asset_id')} &nbsp;|&nbsp; 🏢 {rec.get('department')} &nbsp;|&nbsp; 📅 {format_date(rec.get('action_date'))}
                    </div>
                    {f'<div style="font-size:0.78rem;color:#94A3B8;margin-top:4px;">{rec.get("notes")}</div>' if rec.get("notes") else ''}
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        section_header("🎫", "IT Tickets")
        tickets = db.get_all_tickets()
        if not tickets:
            show_info("Chưa có ticket nào.")
        else:
            for t in tickets[:10]:
                priority_color = {"Khẩn cấp": "#EF4444", "Cao": "#F59E0B", "Trung bình": "#2563EB", "Thấp": "#10B981"}.get(t.get("priority", ""), "#64748B")
                status_color = {"Mở": "#F59E0B", "Đang xử lý": "#2563EB", "Đóng": "#10B981"}.get(t.get("status", ""), "#64748B")

                with st.container():
                    st.markdown(f"""
                    <div class="ticket-card">
                        <div style="display:flex;justify-content:space-between;">
                            <span class="ticket-id">{t.get('id')}</span>
                            <div style="display:flex;gap:6px;">
                                <span class="badge" style="background:{priority_color}22;color:{priority_color};">{t.get('priority')}</span>
                                <span class="badge" style="background:{status_color}22;color:{status_color};">{t.get('status')}</span>
                            </div>
                        </div>
                        <div style="font-weight:600;font-size:0.87rem;margin-top:4px;">{t.get('title')}</div>
                        <div style="font-size:0.78rem;color:#64748B;">🏷️ {t.get('asset_id')} | {format_date(t.get('created_at','')[:10] if t.get('created_at') else '')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    cols = st.columns([1, 1, 1])
                    for i, status in enumerate(["Đang xử lý", "Đóng"]):
                        with cols[i]:
                            if st.button(f"→ {status}", key=f"tk_{t['id']}_{i}", use_container_width=True):
                                db.update_ticket_status(t["id"], status)
                                st.rerun()


# ══════════════════════════════════════════════════════════
# TAB 3 · THEO DÕI BẢO HÀNH
# ══════════════════════════════════════════════════════════

def render_tab_warranty():
    import yaml
    from datetime import timedelta

    with open("config/settings.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    alert_days = cfg["warranty"]["alert_days_before"]
    critical_days = cfg["warranty"]["critical_days_before"]

    assets = db.get_all_assets()
    today = __import__("datetime").date.today()

    expired = []
    critical = []
    warning = []
    healthy = []

    for a in assets:
        wd = a.get("warranty_end_date")
        if not wd:
            continue
        days = warranty_days_remaining(wd)
        if days < 0:
            expired.append((a, days))
        elif days <= critical_days:
            critical.append((a, days))
        elif days <= alert_days:
            warning.append((a, days))
        else:
            healthy.append((a, days))

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("ĐÃ HẾT BẢO HÀNH", len(expired), "Cần xử lý ngay", "#EF4444"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("SẮP HẾT (≤7 ngày)", len(critical), "Ưu tiên cao", "#F59E0B"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(f"CẢNH BÁO (≤{alert_days} ngày)", len(warning), "Cần theo dõi", "#0EA5E9"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("CÒN BẢO HÀNH", len(healthy), "Bình thường", "#10B981"), unsafe_allow_html=True)

    st.divider()

    # Download report
    expiring = db.get_expiring_warranties(alert_days)
    if expiring:
        report_bytes = export_warranty_report(expiring)
        st.download_button(
            f"📥 Xuất báo cáo bảo hành ({len(expiring)} thiết bị)",
            data=report_bytes,
            file_name="bao_cao_bao_hanh.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    tabs = st.tabs(["🔴 Đã hết hạn", "🟡 Sắp hết (khẩn)", f"⚠️ Cảnh báo ≤{alert_days} ngày", "🟢 Còn bảo hành"])

    def render_warranty_list(items):
        if not items:
            show_info("Không có tài sản nào trong nhóm này.")
            return
        for a, days in items:
            color = "#EF4444" if days < 0 else ("#F59E0B" if days <= critical_days else "#0EA5E9")
            days_text = f"Hết hạn {abs(days)} ngày trước" if days < 0 else f"Còn {days} ngày"
            st.markdown(f"""
            <div style="background:white;border:1px solid #E2E8F0;border-left:4px solid {color};
                        border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.5rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
                    <div>
                        <div style="font-weight:700;font-size:0.92rem;color:#1E3A5F;">{a.get('name')}</div>
                        <div style="font-size:0.78rem;color:#64748B;">
                            🏷️ {a.get('id')} | 📁 {a.get('category')} | 👤 {a.get('assigned_to') or '—'} | 🏢 {a.get('department') or '—'}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-weight:700;color:{color};font-size:1rem;">{days_text}</div>
                        <div style="font-size:0.78rem;color:#64748B;">📅 {format_date(a.get('warranty_end_date'))}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tabs[0]:
        render_warranty_list(expired)
    with tabs[1]:
        render_warranty_list(critical)
    with tabs[2]:
        render_warranty_list(warning)
    with tabs[3]:
        render_warranty_list(healthy)


# ══════════════════════════════════════════════════════════
# TAB 4 · DASHBOARD & BÁO CÁO
# ══════════════════════════════════════════════════════════

def render_tab_dashboard():
    import plotly.graph_objects as go
    import plotly.express as px

    assets = db.get_all_assets()
    if not assets:
        show_info("Chưa có dữ liệu tài sản. Vui lòng thêm tài sản ở Tab 1.")
        _render_ai_chat([])
        return

    # Top metrics
    total = len(assets)
    in_use = sum(1 for a in assets if a.get("status") == "Đang sử dụng")
    storage = sum(1 for a in assets if a.get("status") == "Kho dự phòng")
    expiring = len(db.get_expiring_warranties(30))
    total_value = sum(float(a.get("purchase_price") or 0) for a in assets)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(metric_card("TỔNG TÀI SẢN", total, "thiết bị", "#1E3A5F"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("ĐANG SỬ DỤNG", in_use, f"{in_use/total*100:.0f}%", "#10B981"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("KHO DỰ PHÒNG", storage, "thiết bị", "#2563EB"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("SẮP HẾT BH", expiring, "trong 30 ngày", "#F59E0B"), unsafe_allow_html=True)
    with c5:
        st.markdown(metric_card("TỔNG GIÁ TRỊ", format_currency(total_value), "", "#7C3AED"), unsafe_allow_html=True)

    st.divider()

    # Charts
    col_l, col_r = st.columns(2)

    with col_l:
        section_header("📊", "Phân bổ theo trạng thái")
        status_counts = {}
        for a in assets:
            s = a.get("status", "Không rõ")
            status_counts[s] = status_counts.get(s, 0) + 1
        colors_map = {
            "Đang sử dụng": "#10B981", "Kho dự phòng": "#2563EB",
            "Đang bảo hành": "#F59E0B", "Hỏng / Chờ xử lý": "#EF4444", "Đã thanh lý": "#94A3B8",
        }
        fig = go.Figure(go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.55,
            marker_colors=[colors_map.get(k, "#94A3B8") for k in status_counts.keys()],
            textfont_size=12,
        ))
        fig.update_layout(
            showlegend=True, height=300, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(size=11)),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        section_header("🏢", "Phân bổ theo phòng ban")
        dept_counts = {}
        for a in assets:
            d = a.get("department") or "Chưa phân công"
            dept_counts[d] = dept_counts.get(d, 0) + 1
        dept_sorted = sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)
        fig2 = go.Figure(go.Bar(
            y=[d[0] for d in dept_sorted],
            x=[d[1] for d in dept_sorted],
            orientation="h",
            marker_color="#2563EB",
            text=[d[1] for d in dept_sorted],
            textposition="outside",
        ))
        fig2.update_layout(
            height=300, margin=dict(t=10, b=10, l=10, r=30),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Category breakdown
    section_header("📦", "Phân bổ theo loại thiết bị")
    cat_counts = {}
    for a in assets:
        c = a.get("category") or "Khác"
        cat_counts[c] = cat_counts.get(c, 0) + 1
    cat_sorted = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    palette = ["#1E3A5F", "#2563EB", "#0EA5E9", "#10B981", "#F59E0B", "#EF4444", "#7C3AED", "#EC4899", "#14B8A6", "#F97316"]
    fig3 = go.Figure(go.Bar(
        x=[c[0] for c in cat_sorted],
        y=[c[1] for c in cat_sorted],
        marker_color=palette[:len(cat_sorted)],
        text=[c[1] for c in cat_sorted],
        textposition="outside",
    ))
    fig3.update_layout(
        height=280, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Assets not recovered (nhân viên nghỉ - mô phỏng)
    section_header("⚠️", "Tài sản chưa thu hồi (nhân viên đã ghi nhận nghỉ)")
    unrecovered = [a for a in assets if a.get("assigned_to") and a.get("status") == "Đang sử dụng"]
    if unrecovered:
        show_warning(f"Có {len(unrecovered)} tài sản đang bàn giao — kiểm tra khi nhân viên nghỉ việc.")
        for a in unrecovered[:5]:
            st.markdown(f"• **{a.get('name')}** (ID: {a.get('id')}) — 👤 {a.get('assigned_to')} — 🏢 {a.get('department')}", unsafe_allow_html=False)
    else:
        show_info("Không có tài sản nào đang bàn giao.")

    st.divider()
    _render_ai_chat(assets)


def _render_ai_chat(assets: list):
    """AI Chat assistant trong tab Dashboard."""
    section_header("🤖", "Trợ lý AI Asset Manager")
    from core.agent import get_agent_response
    from core.memory import add_message, get_history, clear_history

    # Asset context summary
    asset_context = f"Có {len(assets)} tài sản. " if assets else "Chưa có tài sản. "
    if assets:
        in_use = sum(1 for a in assets if a.get("status") == "Đang sử dụng")
        expiring = len(db.get_expiring_warranties(30))
        asset_context += f"{in_use} đang sử dụng, {expiring} sắp hết bảo hành trong 30 ngày."

    # Chat history display
    history = get_history()
    chat_container = st.container()
    with chat_container:
        if not history:
            show_info("💬 Hỏi AI về tình trạng tài sản, bảo hành, quy trình bàn giao...")
        for msg in history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="display:flex;justify-content:flex-end;margin-bottom:0.5rem;">
                    <div style="background:#2563EB;color:white;border-radius:12px 12px 2px 12px;
                                padding:0.6rem 1rem;max-width:75%;font-size:0.87rem;">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display:flex;justify-content:flex-start;margin-bottom:0.5rem;">
                    <div style="background:white;border:1px solid #E2E8F0;border-radius:12px 12px 12px 2px;
                                padding:0.6rem 1rem;max-width:75%;font-size:0.87rem;color:#1E293B;">
                        🤖 {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Input
    col_inp, col_btn, col_clear = st.columns([5, 1, 1])
    with col_inp:
        user_input = st.text_input(
            "Câu hỏi của bạn",
            placeholder="VD: Có bao nhiêu thiết bị sắp hết bảo hành?",
            label_visibility="collapsed",
            key="ai_input",
        )
    with col_btn:
        send = st.button("Gửi", use_container_width=True)
    with col_clear:
        if st.button("🗑️", use_container_width=True, help="Xóa lịch sử"):
            clear_history()
            st.rerun()

    if send and user_input.strip():
        from core.llm import check_llm_available
        if not check_llm_available():
            show_warning("⚠️ LLM chưa được cấu hình. Vui lòng thêm GOOGLE_API_KEY vào file .env")
        else:
            try:
                add_message("user", user_input.strip())
                with st.spinner("Đang xử lý..."):
                    response = get_agent_response(user_input.strip(), asset_context)
                add_message("assistant", response)
                st.rerun()
            except Exception as e:
                logger.error(f"AI chat error: {e}")
                show_error()


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    render_header()

    # Sidebar
    with st.sidebar:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.75rem;opacity:0.6;text-transform:uppercase;letter-spacing:0.08em;'>Trạng thái hệ thống</p>", unsafe_allow_html=True)
        render_db_status()
        render_llm_status()
        st.divider()
        st.markdown("<p style='font-size:0.75rem;opacity:0.6;text-transform:uppercase;letter-spacing:0.08em;'>Thông tin</p>", unsafe_allow_html=True)
        assets = db.get_all_assets()
        expiring = db.get_expiring_warranties(30)
        tickets = db.get_all_tickets()
        open_tickets = [t for t in tickets if t.get("status") == "Mở"]

        st.markdown(f"<p style='font-size:0.85rem;'>📦 Tổng tài sản: <b>{len(assets)}</b></p>", unsafe_allow_html=True)
        if expiring:
            st.markdown(f"<p style='font-size:0.85rem;color:#FCD34D;'>⚠️ Sắp hết BH: <b>{len(expiring)}</b></p>", unsafe_allow_html=True)
        if open_tickets:
            st.markdown(f"<p style='font-size:0.85rem;color:#FCD34D;'>🎫 Ticket mở: <b>{len(open_tickets)}</b></p>", unsafe_allow_html=True)

        st.divider()
        st.markdown("<p style='font-size:0.7rem;opacity:0.5;'>Asset Tracker v1.0.0<br>Powered by Gemini AI</p>", unsafe_allow_html=True)

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Danh sách tài sản",
        "🔄 Bàn giao & Thu hồi",
        "🛡️ Theo dõi bảo hành",
        "📊 Dashboard & Báo cáo",
    ])

    with tab1:
        try:
            render_tab_asset_list()
        except Exception as e:
            logger.error(f"Tab 1 error: {e}")
            show_error()

    with tab2:
        try:
            render_tab_assignment()
        except Exception as e:
            logger.error(f"Tab 2 error: {e}")
            show_error()

    with tab3:
        try:
            render_tab_warranty()
        except Exception as e:
            logger.error(f"Tab 3 error: {e}")
            show_error()

    with tab4:
        try:
            render_tab_dashboard()
        except Exception as e:
            logger.error(f"Tab 4 error: {e}")
            show_error()


if __name__ == "__main__":
    main()
