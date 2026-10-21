# Ho-Thu-V-c-i-ti-n
# Thu Vũ AI — Gemini 2.5 Flash

## Cài đặt và chạy
1. Cài Python 3.10 trở lên.
2. Cài thư viện:
   ```bash
   pip install -r requirements.txt
   ```
3. Khai báo API key trong Streamlit Secrets (`.streamlit/secrets.toml` khi chạy local hoặc mục Secrets trên nền tảng triển khai):
   ```toml
   GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
   ```
   Ứng dụng mặc định dùng model `gemini-2.5-flash`. Có thể đặt rõ model trong Secrets bằng `GOOGLE_MODEL = "gemini-2.5-flash"`. Không nhập hoặc công khai API key trên giao diện hay trong mã nguồn.
4. Chạy ứng dụng:
   ```bash
   streamlit run app.py
   ```

## Tính năng
- Dùng model `gemini-2.5-flash` qua SDK `google-genai`.
- Giữ giao diện, tư vấn công thức hương, điều chỉnh thanh thành phần, và tính năng giọng nói của bản trước.
- API key được đọc từ Streamlit Secrets hoặc biến môi trường `GOOGLE_API_KEY`.

## Lưu ý hạn mức
Hạn mức miễn phí và số yêu cầu mỗi ngày phụ thuộc model, dự án và trạng thái tài khoản. Xem giới hạn thực tế trong Google AI Studio trước khi triển khai rộng. Đổi model không tự động bảo đảm một số lượt/ngày cụ thể.

