# Ho-Thu-V-c-i-ti-n
## Thu Vũ AI — Ollama Local

Bản này thay Gemini API bằng **Ollama**, một API chạy model AI trên máy chủ/máy tính do bạn kiểm soát.

## Điểm chính
- Không cần API key của nhà cung cấp AI.
- Không có hạn mức lượt gọi do nhà cung cấp API cloud áp đặt; tốc độ và số lượt thực tế vẫn phụ thuộc phần cứng, RAM, CPU/GPU và thời gian hoạt động.
- Hiểu mô tả tự nhiên bằng tiếng Việt, duy trì ngữ cảnh trò chuyện và đề xuất công thức JSON.
- Tin nhắn thoại được chuyển thành văn bản bằng `faster-whisper` chạy cục bộ.
- Công thức được cập nhật tự động trên thanh trượt sau mỗi phản hồi.

## Cài đặt
1. Cài Ollama: https://ollama.com/download
2. Tải model trong Terminal/Command Prompt:
   ```bash
   ollama pull qwen2.5:7b
   ```
   Máy yếu hơn có thể thử `ollama pull qwen2.5:3b`.
3. Trong thư mục app:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Cấu hình
Mặc định `OLLAMA_BASE_URL=http://localhost:11434` và `OLLAMA_MODEL=qwen2.5:7b`.

Có thể đặt trong `.streamlit/secrets.toml`:
```toml
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"
```

## Lưu ý triển khai
Nếu deploy lên Streamlit Community Cloud, `localhost` là máy chủ Streamlit chứ không phải máy tính cá nhân. Khi đó phải chạy Ollama trên một máy chủ khác có thể truy cập an toàn và đặt `OLLAMA_BASE_URL` đến máy đó. Không nên mở Ollama công khai không có bảo vệ mạng.

## Giới hạn
Không có dịch vụ AI cloud nào bảo đảm miễn phí và không giới hạn tuyệt đối. Ollama tránh hạn mức lượt gọi từ nhà cung cấp vì model chạy trên hạ tầng bạn kiểm soát, nhưng vẫn chịu giới hạn tài nguyên phần cứng. `faster-whisper` sẽ tải model nhận diện giọng nói ở lần đầu và có thể cần khá nhiều RAM/CPU.

