## Cấu hình MQTT — Python MQTT Monitor

### 1. Cấu hình mặc định

```yaml
mqtt:
  host: "mqtt.mysignage.vn"
  port: 1883
  transport: "tcp"
  protocol: "MQTTv311"
  keepalive_seconds: 60
  client_id: "KIT-001-python-monitor"
  tls_enabled: false

kit:
  kit_code: "KIT-001"

topics:
  telemetry: "lab/kit/KIT-001/telemetry"
  heartbeat: "lab/kit/KIT-001/heartbeat"

monitor:
  max_messages_in_memory: 500
  json_indent: 2
  auto_scroll: true
```

### 2. Yêu cầu kết nối

- Không xây dựng chức năng đăng nhập.
- Không tạo màn hình nhập username/password.
- Không yêu cầu người dùng đăng nhập trước khi sử dụng app.
- App tự kết nối tới broker bằng cấu hình trên khi khởi động.
- Không tự đặt hoặc thử username/password mặc định.
- Cấu hình ban đầu thử kết nối MQTT không có thông tin xác thực. Đây là lựa chọn cấu hình cần kiểm chứng, không phải khẳng định broker cho phép truy cập anonymous.
- Nếu broker từ chối kết nối do yêu cầu xác thực hoặc chính sách truy cập, hiển thị lỗi rõ ràng và hướng dẫn kiểm tra với quản trị viên. Không tự chuyển sang một phương thức xác thực khác.
- Có nút Connect/Reconnect và Disconnect để người dùng chủ động quản lý kết nối.
- Hiển thị trạng thái kết nối và lỗi gần nhất trên cửa sổ chính.

### 3. Giới hạn bảo mật

Port `1883` với MQTT thường không cung cấp mã hóa TLS. Không lưu hoặc truyền thông tin bí mật trong ứng dụng. Nếu sau này quản trị viên yêu cầu TLS hoặc xác thực, bổ sung cấu hình riêng mà không cần thiết kế lại toàn bộ giao diện.

### 4. Phạm vi ứng dụng

App chỉ subscribe:
- `lab/kit/KIT-001/telemetry`
- `lab/kit/KIT-001/heartbeat`

App nhận payload, parse JSON và trình bày dữ liệu dễ đọc. Không publish message, không gửi lệnh điều khiển kit và không xây dựng chức năng đăng nhập.