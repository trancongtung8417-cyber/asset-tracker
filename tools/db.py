"""
tools/db.py
Neon PostgreSQL — kết nối OPTIONAL, không crash nếu chưa cấu hình
Tất cả method đều trả default value nếu DB chưa sẵn sàng
"""
import os
import logging
import uuid
from datetime import datetime, date
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── In-memory fallback store ──────────────────────────────
_STORE = {
    "assets": [],
    "assignments": [],
    "tickets": [],
}

_db_connected = False
_engine = None


def _try_connect():
    """Thử kết nối DB, không raise nếu thất bại."""
    global _db_connected, _engine
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        logger.info("DATABASE_URL chưa cấu hình — dùng bộ nhớ tạm.")
        return False
    try:
        from sqlalchemy import create_engine, text
        _engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _db_connected = True
        logger.info("Kết nối Neon PostgreSQL thành công.")
        _init_tables()
        return True
    except Exception as e:
        logger.warning(f"Không thể kết nối DB: {e} — dùng bộ nhớ tạm.")
        _db_connected = False
        return False


def _init_tables():
    """Tạo bảng nếu chưa có."""
    if not _db_connected or _engine is None:
        return
    try:
        from sqlalchemy import text
        ddl = """
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            serial_number TEXT,
            purchase_date DATE,
            warranty_end_date DATE,
            status TEXT DEFAULT 'Kho dự phòng',
            department TEXT,
            assigned_to TEXT,
            location TEXT,
            purchase_price NUMERIC,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            asset_id TEXT REFERENCES assets(id),
            employee_name TEXT,
            department TEXT,
            action TEXT,
            action_date DATE,
            notes TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS it_tickets (
            id TEXT PRIMARY KEY,
            asset_id TEXT REFERENCES assets(id),
            title TEXT,
            description TEXT,
            status TEXT DEFAULT 'Mở',
            priority TEXT DEFAULT 'Trung bình',
            created_by TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        with _engine.begin() as conn:
            conn.execute(text(ddl))
        logger.info("Khởi tạo bảng DB thành công.")
    except Exception as e:
        logger.error(f"Lỗi tạo bảng: {e}")


def is_connected() -> bool:
    return _db_connected


# ── Asset CRUD ────────────────────────────────────────────

def create_asset(data: dict) -> Optional[dict]:
    """Tạo tài sản mới."""
    asset = {
        "id": str(uuid.uuid4())[:8].upper(),
        "name": data.get("name", ""),
        "category": data.get("category", ""),
        "serial_number": data.get("serial_number", ""),
        "purchase_date": data.get("purchase_date"),
        "warranty_end_date": data.get("warranty_end_date"),
        "status": data.get("status", "Kho dự phòng"),
        "department": data.get("department", ""),
        "assigned_to": data.get("assigned_to", ""),
        "location": data.get("location", ""),
        "purchase_price": data.get("purchase_price", 0),
        "notes": data.get("notes", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO assets (id, name, category, serial_number, purchase_date,
                        warranty_end_date, status, department, assigned_to, location,
                        purchase_price, notes)
                    VALUES (:id, :name, :category, :serial_number, :purchase_date,
                        :warranty_end_date, :status, :department, :assigned_to, :location,
                        :purchase_price, :notes)
                """), asset)
            logger.info(f"Tạo tài sản DB: {asset['id']}")
        else:
            _STORE["assets"].append(asset)
            logger.info(f"Tạo tài sản (bộ nhớ): {asset['id']}")
        return asset
    except Exception as e:
        logger.error(f"Lỗi tạo tài sản: {e}")
        _STORE["assets"].append(asset)
        return asset


def get_all_assets() -> list:
    """Lấy toàn bộ danh sách tài sản."""
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.connect() as conn:
                rows = conn.execute(text("SELECT * FROM assets ORDER BY created_at DESC")).mappings().all()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Lỗi get_all_assets: {e}")
    return list(_STORE["assets"])


def get_asset_by_id(asset_id: str) -> Optional[dict]:
    """Tìm tài sản theo ID."""
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.connect() as conn:
                row = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).mappings().first()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Lỗi get_asset_by_id: {e}")
    return next((a for a in _STORE["assets"] if a["id"] == asset_id), None)


def update_asset(asset_id: str, data: dict) -> bool:
    """Cập nhật thông tin tài sản."""
    data["updated_at"] = datetime.now().isoformat()
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            fields = ", ".join([f"{k} = :{k}" for k in data.keys()])
            data["id"] = asset_id
            with _engine.begin() as conn:
                conn.execute(text(f"UPDATE assets SET {fields} WHERE id = :id"), data)
            return True
    except Exception as e:
        logger.error(f"Lỗi update_asset DB: {e}")
    # Fallback
    for i, a in enumerate(_STORE["assets"]):
        if a["id"] == asset_id:
            _STORE["assets"][i].update(data)
            return True
    return False


def delete_asset(asset_id: str) -> bool:
    """Xóa tài sản."""
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.begin() as conn:
                conn.execute(text("DELETE FROM assets WHERE id = :id"), {"id": asset_id})
            return True
    except Exception as e:
        logger.error(f"Lỗi delete_asset: {e}")
    _STORE["assets"] = [a for a in _STORE["assets"] if a["id"] != asset_id]
    return True


# ── Assignment CRUD ───────────────────────────────────────

def create_assignment(data: dict) -> Optional[dict]:
    """Tạo bản ghi bàn giao / thu hồi."""
    record = {
        "id": str(uuid.uuid4())[:8].upper(),
        "asset_id": data.get("asset_id", ""),
        "employee_name": data.get("employee_name", ""),
        "department": data.get("department", ""),
        "action": data.get("action", "Bàn giao"),
        "action_date": data.get("action_date", date.today().isoformat()),
        "notes": data.get("notes", ""),
        "created_by": data.get("created_by", "Admin"),
        "created_at": datetime.now().isoformat(),
    }
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO assignments (id, asset_id, employee_name, department,
                        action, action_date, notes, created_by)
                    VALUES (:id, :asset_id, :employee_name, :department,
                        :action, :action_date, :notes, :created_by)
                """), record)
        else:
            _STORE["assignments"].append(record)
        return record
    except Exception as e:
        logger.error(f"Lỗi create_assignment: {e}")
        _STORE["assignments"].append(record)
        return record


def get_assignments_by_asset(asset_id: str) -> list:
    """Lấy lịch sử bàn giao theo tài sản."""
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT * FROM assignments WHERE asset_id = :id ORDER BY created_at DESC"),
                    {"id": asset_id}
                ).mappings().all()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Lỗi get_assignments_by_asset: {e}")
    return [a for a in _STORE["assignments"] if a["asset_id"] == asset_id]


def get_all_assignments() -> list:
    """Lấy toàn bộ lịch sử bàn giao."""
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.connect() as conn:
                rows = conn.execute(text("SELECT * FROM assignments ORDER BY created_at DESC")).mappings().all()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Lỗi get_all_assignments: {e}")
    return list(_STORE["assignments"])


# ── IT Ticket CRUD ────────────────────────────────────────

def create_ticket(data: dict) -> Optional[dict]:
    """Tạo IT ticket."""
    ticket = {
        "id": "TK-" + str(uuid.uuid4())[:6].upper(),
        "asset_id": data.get("asset_id", ""),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "status": data.get("status", "Mở"),
        "priority": data.get("priority", "Trung bình"),
        "created_by": data.get("created_by", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO it_tickets (id, asset_id, title, description, status, priority, created_by)
                    VALUES (:id, :asset_id, :title, :description, :status, :priority, :created_by)
                """), ticket)
        else:
            _STORE["tickets"].append(ticket)
        logger.info(f"Tạo IT ticket: {ticket['id']}")
        return ticket
    except Exception as e:
        logger.error(f"Lỗi create_ticket: {e}")
        _STORE["tickets"].append(ticket)
        return ticket


def get_all_tickets() -> list:
    """Lấy toàn bộ IT tickets."""
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.connect() as conn:
                rows = conn.execute(text("SELECT * FROM it_tickets ORDER BY created_at DESC")).mappings().all()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Lỗi get_all_tickets: {e}")
    return list(_STORE["tickets"])


def update_ticket_status(ticket_id: str, status: str) -> bool:
    """Cập nhật trạng thái ticket."""
    try:
        if _db_connected and _engine:
            from sqlalchemy import text
            with _engine.begin() as conn:
                conn.execute(
                    text("UPDATE it_tickets SET status = :s, updated_at = NOW() WHERE id = :id"),
                    {"s": status, "id": ticket_id}
                )
            return True
    except Exception as e:
        logger.error(f"Lỗi update_ticket_status: {e}")
    for t in _STORE["tickets"]:
        if t["id"] == ticket_id:
            t["status"] = status
            return True
    return False


# ── Warranty helpers ──────────────────────────────────────

def get_expiring_warranties(days: int = 30) -> list:
    """Lấy tài sản sắp hết bảo hành trong N ngày."""
    from datetime import timedelta
    today = date.today()
    cutoff = today + timedelta(days=days)
    assets = get_all_assets()
    result = []
    for a in assets:
        wd = a.get("warranty_end_date")
        if wd:
            try:
                if isinstance(wd, str):
                    wd = date.fromisoformat(wd)
                if today <= wd <= cutoff:
                    result.append(a)
            except Exception:
                pass
    return result


# Khởi động kết nối ngay khi module load
_try_connect()
