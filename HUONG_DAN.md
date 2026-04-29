# 📦 Asset Tracker — Hướng dẫn cài đặt & sử dụng

> Hệ thống quản lý tài sản & thiết bị văn phòng · Phiên bản 1.0.0

---

## 📋 Mục lục

1. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
2. [Cài đặt Local (Windows / macOS / Linux)](#cài-đặt-local)
3. [Cấu hình biến môi trường](#cấu-hình-biến-môi-trường)
4. [Chạy ứng dụng](#chạy-ứng-dụng)
5. [Cấu hình Database (Tùy chọn)](#cấu-hình-database)
6. [Deploy lên Streamlit Cloud](#deploy-lên-streamlit-cloud)
7. [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
8. [Xử lý lỗi thường gặp](#xử-lý-lỗi)

---

## Yêu cầu hệ thống

| Thành phần | Yêu cầu tối thiểu |
|-----------|-------------------|
| Python | 3.10 trở lên |
| RAM | 512 MB trống |
| Disk | 200 MB |
| Kết nối Internet | Cần thiết để dùng Gemini AI |

---

## Cài đặt Local

### Bước 1 — Tải source code

```bash
# Clone từ GitHub (nếu đã push)
git clone https://github.com/your-username/asset-tracker.git
cd asset-tracker

# Hoặc giải nén file ZIP vào thư mục mong muốn
```

### Bước 2 — Tạo môi trường ảo Python

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 3 — Cài đặt thư viện

```bash
pip install -r requirements.txt
```

> ⏳ Quá trình này mất khoảng 2–5 phút tùy tốc độ mạng.

---

## Cấu hình biến môi trường

### Bước 1 — Tạo file .env

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

### Bước 2 — Điền thông tin vào .env

Mở file `.env` bằng Notepad hoặc VS Code:

```env
# BẮT BUỘC — Gemini AI API Key
GOOGLE_API_KEY=AIzaSy...

# TÙY CHỌN — Neon PostgreSQL (bỏ trống để dùng bộ nhớ tạm)
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

### Lấy Google API Key

1. Truy cập: https://aistudio.google.com/app/apikey
2. Đăng nhập bằng tài khoản Google
3. Click **"Create API Key"**
4. Sao chép key và dán vào `.env`

---

## Chạy ứng dụng

```bash
# Đảm bảo đang trong thư mục dự án và đã activate venv
streamlit run app.py
```

Ứng dụng sẽ tự mở tại: **http://localhost:8501**

---

## Cấu hình Database

> **Lưu ý:** Database là tùy chọn. Nếu không cấu hình, app dùng bộ nhớ tạm (dữ liệu mất khi restart).

### Tạo tài khoản Neon PostgreSQL (Miễn phí)

1. Đăng ký tại: https://neon.tech
2. Tạo Project mới
3. Vào **Connection Details** → sao chép **Connection String**
4. Dán vào `DATABASE_URL` trong file `.env`

Khi cấu hình đúng, sidebar sẽ hiển thị: 🟢 **Neon DB: Đã kết nối**

---

## Deploy lên Streamlit Cloud

### Bước 1 — Push code lên GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/asset-tracker.git
git push -u origin main
```

### Bước 2 — Tạo app trên Streamlit Cloud

1. Đăng nhập: https://share.streamlit.io
2. Click **"New app"**
3. Chọn repository và branch `main`
4. Main file: `app.py`
5. Click **"Deploy"**

### Bước 3 — Cấu hình Secrets

Trong Streamlit Cloud → **Settings** → **Secrets**, điền:

```toml
GOOGLE_API_KEY = "AIzaSy..."
DATABASE_URL = "postgresql://..."
```

---

## Hướng dẫn sử dụng

### Tab 1 — Danh sách tài sản
- **Thêm tài sản**: Click nút "➕ Thêm tài sản", điền thông tin và lưu
- **Nhập từ Excel**: Upload file .xlsx với các cột: Tên tài sản, Loại, Serial, Ngày mua, Hết bảo hành, Trạng thái, Phòng ban, Người dùng
- **Tải QR Code**: Click "🔲 QR Code" để tải file PNG dán lên thiết bị
- **Tải nhãn PDF**: Click "🏷️ Nhãn PDF" để in nhãn dán thiết bị
- **Xuất Excel**: Click "📥 Xuất Excel" để tải toàn bộ danh sách

### Tab 2 — Bàn giao & Thu hồi
- Chọn tài sản → chọn hành động (Bàn giao / Thu hồi / Chuyển phòng)
- Điền thông tin nhân viên và xác nhận
- Tạo IT Ticket khi cần yêu cầu đổi trả / sửa chữa

### Tab 3 — Theo dõi bảo hành
- Xem tổng quan các thiết bị phân theo nhóm: hết hạn / khẩn / cảnh báo / còn bảo hành
- Xuất báo cáo Excel để gửi cho bộ phận phụ trách

### Tab 4 — Dashboard & AI Trợ lý
- Xem biểu đồ phân bổ tài sản theo trạng thái, phòng ban, loại thiết bị
- Hỏi AI về tình trạng tài sản, bảo hành, quy trình quản lý

---

## Xử lý lỗi

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `⚪ AI: Chưa cấu hình API key` | Chưa điền GOOGLE_API_KEY | Thêm key vào file .env |
| `🟡 DB: Bộ nhớ tạm` | Chưa cấu hình DATABASE_URL | Bình thường, hoặc cấu hình Neon DB |
| `ModuleNotFoundError` | Chưa cài đủ thư viện | Chạy lại `pip install -r requirements.txt` |
| Trang trắng khi chạy | Port 8501 bị chiếm | Chạy `streamlit run app.py --server.port 8502` |

### Xem logs để debug

```bash
# Xem log hoạt động
type logs\app.log        # Windows
cat logs/app.log         # macOS / Linux

# Xem log lỗi
type logs\error.log
cat logs/error.log
```

---

## 📁 Cấu trúc thư mục

```
asset_tracker/
├── core/
│   ├── llm.py          ← Khởi tạo Gemini LLM
│   ├── agent.py        ← LangGraph workflow
│   └── memory.py       ← Lịch sử hội thoại
├── tools/
│   ├── db.py           ← Neon PostgreSQL (optional)
│   └── file_handler.py ← Excel, PDF, QR Code
├── ui/
│   └── components.py   ← Widget dùng chung
├── config/
│   └── settings.yaml   ← Cấu hình nghiệp vụ
├── logs/               ← app.log + error.log
├── app.py              ← Entry point
├── requirements.txt
├── .env.example
└── HUONG_DAN.md
```

---

## 🔧 Mở rộng sau này

Khi cần bổ sung tính năng:

| Tính năng | Hướng thực hiện |
|-----------|-----------------|
| Phân quyền Admin/Staff | Thêm `auth/` module |
| Email cảnh báo bảo hành | Cấu hình SMTP trong `.env` |
| RAG tài liệu nội bộ | Thêm `core/embedding.py` |
| CI/CD tự động | Thêm `.github/workflows/deploy.yml` |
| Migration DB | Thêm `migrations/` dùng Alembic |

---

> Cần hỗ trợ? Liên hệ team IT hoặc mở issue trên GitHub.
