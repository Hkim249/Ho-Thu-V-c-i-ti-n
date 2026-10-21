# Thu Vũ

Bản tối ưu dung lượng mã nguồn, dùng Gemini 3.1 Flash-Lite qua Google GenAI SDK.

- Tên app: **Thu Vũ**
- Slogan: **Hương thu theo cách riêng của bạn**
- Background chào mừng đã nén thành JPEG và được nạp từ file cạnh `app.py`.
- Tốc độ giọng đọc Edge TTS: 1.25x (`rate=+25%`), giọng `vi-VN-HoaiMyNeural`.

Cài đặt: `pip install -r requirements.txt`. Cấu hình `GOOGLE_API_KEY` và `GOOGLE_MODEL = "gemini-3.1-flash-lite"` trong Streamlit Secrets. Đặt `app.py`, `requirements.txt` và `thu_vu_welcome_background.jpg` cùng thư mục khi triển khai.
