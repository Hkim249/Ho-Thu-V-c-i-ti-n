# Thu Vũ AI — Gemini 3.1 Flash-Lite

## Cập nhật trong phiên bản này
- Giữ nguyên bìa ảnh mùa thu và tiêu đề Thu Vũ trên màn hình chào mừng.
- Không hiển thị lời chào dạng văn bản trên bìa.
- Không hiển thị thanh điều khiển âm thanh; ứng dụng thử tự phát lời chào tiếng Việt bằng Edge TTS khi mở bìa.
- Khi nhấn Bắt đầu, giao diện chính vẫn thử tự phát lời chào của chuyên viên Thu Vũ bằng giọng Việt Nam.
- Giữ model Gemini 3.1 Flash-Lite và các chức năng phối hương.

## Secrets
```toml
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
GOOGLE_MODEL = "gemini-3.1-flash-lite"
```

Lưu ý: trình duyệt có thể chặn autoplay có tiếng trước khi người dùng tương tác. Mã nguồn sẽ thử phát tự động nhưng không thể vượt qua chính sách chặn autoplay của trình duyệt. Giọng Edge TTS cần Internet.



