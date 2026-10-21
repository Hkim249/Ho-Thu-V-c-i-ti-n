# Thu Vũ AI — Autumn Fragrance Studio

Bản cập nhật giao diện chào mừng và tốc độ giọng đọc.

- Tăng tốc Edge TTS lên 1.5x (`rate=+50%`), giọng nữ tiếng Việt `vi-VN-HoaiMyNeural`.
- Dùng ảnh thiết kế thứ 3 trong ảnh tham khảo làm nền chào mừng.
- Thêm hiệu ứng hiện dần, ánh sáng lướt nhẹ và chuyển động rất nhẹ cho tiêu đề/nút; hỗ trợ `prefers-reduced-motion`.
- Giữ nguyên bìa chào mừng, tiêu đề Thu Vũ và các chức năng app hiện có.

Cài thư viện bằng `pip install -r requirements.txt`, sau đó chạy `streamlit run app.py`. Cần cấu hình `GOOGLE_API_KEY` trong Streamlit Secrets; model mặc định là `gemini-3.1-flash-lite`.

Lưu ý: trình duyệt vẫn có thể chặn tự phát âm thanh cho đến khi người dùng tương tác.

