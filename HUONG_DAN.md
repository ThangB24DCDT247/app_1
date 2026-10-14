# 📘 HƯỚNG DẪN SỬ DỤNG — PTIT MQTT Monitor

> **Phiên bản:** 1.0 | **Dành cho:** KIT-001 | **Broker:** mqtt.mysignage.vn

---

## 1. Yêu cầu hệ thống

| Yêu cầu | Chi tiết |
|---------|----------|
| Hệ điều hành | Windows 10/11, macOS, Linux |
| Python | 3.8 trở lên |
| Thư viện bắt buộc | `paho-mqtt`, `Pillow` (hiển thị logo) |

---

## 2. Cài đặt

### Bước 1 — Cài Python và Tkinter

- **Trên Windows:** Tải tại https://www.python.org/downloads/ (nhớ tích chọn "Add Python to PATH").
- **Trên Linux (Ubuntu / Debian / Raspberry Pi OS):**
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip python3-tk -y
  ```

### Bước 2 — Cài thư viện

```bash
pip install -r requirements.txt
```
*(hoặc: `pip install paho-mqtt Pillow`)*

### Bước 3 — Chạy app

- **Trên Windows:** Double-click vào file **`app1.bat`** (hoặc gõ `python app.py`).
- **Trên Linux:**
  ```bash
  chmod +x run.sh
  ./run.sh
  ```
  *(hoặc: `python3 app.py`)*

---

## 3. Giao diện chính

```
┌─────────────────────────────────────────────────────────────┐
│  [LOGO PTIT]  MQTT Monitor             [KIT-001 Badge]      │  ← Header đỏ
├────────────────────────────────────────┬────────────────────┤
│ ● Trạng thái kết nối          [Connect][Reconnect][Disconnect]│  ← Status bar
├────────────────────────────────────────┬────────────────────┤
│                                        │ 📡 Telemetry gần   │
│  📨 Tin nhắn nhận được                 │    nhất            │
│  ┌──────────────────────────────────┐  ├────────────────────┤
│  │ [12:34:56] topic/telemetry       │  │ 💓 Heartbeat gần   │
│  │ { "temp": 25.3, ... }            │  │    nhất            │
│  │ ──────────────────               │  ├────────────────────┤
│  │ [12:34:57] topic/heartbeat       │  │ ⚙ Cấu hình kết nối│
│  │ { "status": "ok" }               │  │ Host: ...          │
│  └──────────────────────────────────┘  │ Port: ...          │
│  [✓ Tự cuộn] [🗑 Xóa] [💾 Lưu log]   │ [💾 Áp dụng]       │
└────────────────────────────────────────┴────────────────────┘
│  🕐 2026-10-13 21:34:00    © PTIT                           │  ← Bottom bar
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Các nút chức năng

| Nút | Chức năng |
|-----|-----------|
| ⚡ **Connect** | Kết nối tới MQTT broker với cấu hình hiện tại |
| 🔄 **Reconnect** | Ngắt và kết nối lại (dùng khi mất kết nối) |
| ✖ **Disconnect** | Ngắt kết nối hoàn toàn |
| 🗑 **Xóa tất cả** | Xóa toàn bộ tin nhắn trên màn hình |
| 💾 **Lưu log** | Lưu toàn bộ tin nhắn ra file JSON |
| ✓ **Tự cuộn** | Bật/tắt chế độ cuộn tự động xuống tin mới nhất |
| 💾 **Áp dụng cấu hình** | Lưu cấu hình Host/Port/Client ID mới, sau đó Reconnect |

---

## 5. Đèn trạng thái kết nối

| Màu | Ý nghĩa |
|-----|---------|
| 🟢 Xanh lá | Đã kết nối thành công |
| 🟠 Cam | Đang kết nối... |
| ⚫ Xám | Chưa kết nối / Đã ngắt |
| 🔴 Đỏ | Lỗi kết nối — xem chi tiết trên thanh trạng thái |

---

## 6. Topics được theo dõi

| Topic | Mô tả |
|-------|-------|
| `lab/kit/KIT-001/telemetry` | Dữ liệu cảm biến (nhiệt độ, độ ẩm, ...) |
| `lab/kit/KIT-001/heartbeat` | Tín hiệu sống — kiểm tra KIT còn hoạt động |

App **chỉ nhận (subscribe)**, không gửi lệnh tới KIT.

---

## 7. Lưu log

Nhấn **💾 Lưu log** → file `mqtt_log_YYYYMMDD_HHMMSS.json` được tạo trong cùng thư mục với `app.py`.

Định dạng mẫu:
```json
[
  {
    "time": "21:34:56.123",
    "topic": "lab/kit/KIT-001/telemetry",
    "payload": "{\n  \"temp\": 25.3\n}"
  }
]
```

---

## 8. Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `paho-mqtt chưa cài đặt` | Thiếu thư viện | `pip install paho-mqtt` |
| `Lỗi không được phép truy cập (rc=5)` | Broker yêu cầu xác thực | Liên hệ quản trị viên hệ thống |
| `Mất kết nối đột ngột` | Mạng không ổn định | Nhấn 🔄 **Reconnect** |
| Logo không hiện | Thiếu Pillow | `pip install Pillow` |

---

## 9. Bảo mật

- App **không lưu** username/password.
- Port 1883 **không mã hóa** — không truyền thông tin bí mật qua kênh này.
- Nếu cần TLS (port 8883), liên hệ quản trị viên để bổ sung cấu hình.

---

*Phát triển bởi sinh viên PTIT — Học viện Công nghệ Bưu chính Viễn thông*

