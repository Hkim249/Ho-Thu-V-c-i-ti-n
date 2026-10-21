import os
import json
import html
import base64
import asyncio
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    import requests
except ImportError:
    requests = None

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

st.set_page_config(
    page_title="Thu Vũ AI — Autumn Fragrance Studio",
    page_icon="🍂",
    layout="wide",
)

# Autumn-inspired interface. All CSS is decorative; app functionality remains native Streamlit.
st.markdown(
    """
    <style>
    .stApp {
        background:
          radial-gradient(ellipse at 12% 5%, rgba(230, 151, 77, .20), transparent 32%),
          radial-gradient(ellipse at 88% 20%, rgba(133, 65, 35, .18), transparent 30%),
          linear-gradient(135deg, #241a16 0%, #3b2820 42%, #1d211b 100%);
        color: #f7eee4;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #35231b 0%, #22231c 100%);
        border-right: 1px solid rgba(237, 176, 105, .25);
    }
    h1, h2, h3 { color: #f6d3a4 !important; }
    p, label, .stCaption, [data-testid="stMarkdownContainer"] { color: #f3e8dc; }
    div[data-testid="stMetric"] {
        background: rgba(103, 64, 39, .35);
        border: 1px solid rgba(240, 183, 118, .28);
        padding: 12px;
        border-radius: 12px;
    }
    .autumn-banner {
        padding: 22px 24px;
        margin: 0 0 18px 0;
        border-radius: 18px;
        background: linear-gradient(115deg, rgba(133,65,35,.88), rgba(174,105,48,.62), rgba(52,61,43,.88));
        border: 1px solid rgba(255, 210, 157, .3);
        box-shadow: 0 10px 30px rgba(0,0,0,.18);
    }
    .autumn-banner h1 { margin: 0 0 6px 0; font-size: 2.1rem; }
    .autumn-banner p { margin: 0; color: #fff0dc; }
    div.stButton > button {
        border-radius: 10px;
        border: 1px solid #d99b5b;
        background: linear-gradient(110deg, #9e512e, #bd7a3e);
        color: #fff7ee;
        font-weight: 600;
    }
    div.stButton > button:hover { border-color: #ffe0b5; color: white; }
    /* Chỉ tiêu đề giữ màu trắng; nội dung người dùng nhập luôn màu đen. */
    .description-heading { color: #ffffff !important; }
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"],
    [data-testid="stChatInput"] input,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="input"] input,
    [data-testid="stChatInput"] div[contenteditable="true"] {
        background: #fff8ee !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        caret-color: #000000 !important;
        opacity: 1 !important;
    }
    [data-testid="stTextArea"] textarea::placeholder,
    [data-testid="stChatInput"] textarea::placeholder,
    [data-testid="stChatInputTextArea"]::placeholder,
    [data-testid="stChatInput"] input::placeholder,
    [data-testid="stChatInput"] div[contenteditable="true"]:empty::before {
        color: #555555 !important;
        -webkit-text-fill-color: #555555 !important;
        opacity: 1 !important;
    }
    .welcome-screen {
        min-height: 72vh; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center;
        padding: 56px 24px; border-radius: 28px; overflow: hidden;
        background-image: linear-gradient(110deg, rgba(20,15,12,.72), rgba(35,22,15,.38)),
          url('https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=2200&q=90');
        background-size: cover; background-position: center;
        border: 1px solid rgba(255,218,171,.38); box-shadow: 0 18px 55px rgba(0,0,0,.35);
    }
    .welcome-kicker { color: #ffd8a8 !important; letter-spacing: .28em; text-transform: uppercase; font-size: .8rem; margin-bottom: 16px; }
    .welcome-title { color: #fff7ec !important; font-size: clamp(3rem, 8vw, 6rem); line-height: 1.05; font-weight: 700; margin: 0; text-shadow: 0 4px 24px rgba(0,0,0,.5); }
    .welcome-subtitle { max-width: 650px; margin: 18px auto 28px auto; color: #fff1df !important; font-size: 1.1rem; line-height: 1.7; text-shadow: 0 2px 10px rgba(0,0,0,.55); }
    .welcome-action div[data-testid="stButton"] > button { min-height: 3.4rem; padding: 0 3rem; border-radius: 999px; font-size: 1.05rem; background: linear-gradient(110deg, #9e512e, #d69a53); border: 1px solid #ffe1b6; box-shadow: 0 8px 26px rgba(0,0,0,.3); }
    </style>
    <div class="autumn-banner">
      <h1>🍂 Thu Vũ AI</h1>
      <p>Autumn Fragrance Studio · Mô tả cảm nhận, nghe tư vấn và tinh chỉnh công thức cùng Gemini.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

DEFAULTS = {
    "Cam": 1.38,
    "Gỗ thông": 4.83,
    "Hoa nhài": 2.07,
    "Vanilla": 1.72,
    "Chất định hương": 3.00,
}
LAYERS = {
    "Cam": "Hương đầu",
    "Gỗ thông": "Hương giữa",
    "Hoa nhài": "Hương giữa",
    "Vanilla": "Hương cuối",
    "Chất định hương": "Chất định hương",
}

SYSTEM_PROMPT = """
Bạn là chuyên gia tư vấn mùi hương và trợ lý phối hương cho Thu Vũ.
Hãy hiểu mô tả tự nhiên của người dùng, kể cả bản chép lời từ giọng nói, rồi đề xuất công thức
chỉ dùng các nguyên liệu có sẵn: Cam, Gỗ thông, Hoa nhài, Vanilla, Chất định hương.
Phân tích độ tươi/citrus, xanh-gỗ, hoa, ngọt-ấm, độ đậm, độ sạch, độ lưu hương và bối cảnh sử dụng.
Không tuyên bố đo chính xác cảm nhận chủ quan. Trả lời bằng tiếng Việt, ngắn gọn.
Khi thiếu thông tin quan trọng, hãy đặt một câu hỏi làm rõ nhưng vẫn trả công thức đề xuất tốt nhất hiện tại.
Tỷ lệ trong percentages là phần trăm của toàn bộ công thức, không phải tỷ lệ tinh dầu nguyên chất.
Giữ mỗi thành phần trong khoảng 0–20%, tổng nguyên liệu không vượt quá 40%, chất định hương không vượt quá 10%.
Không đưa ra bảo đảm an toàn da hoặc khẳng định y tế. Gợi ý chỉ mang tính tham khảo, cần kiểm tra giới hạn an toàn
của từng nguyên liệu và thử nghiệm quy mô nhỏ.
Chỉ trả về JSON hợp lệ theo schema:
{
  "summary": "mô tả ngắn về mùi hương mục tiêu",
  "clarifying_question": "câu hỏi cần hỏi thêm hoặc chuỗi rỗng",
  "percentages": {
    "Cam": 1.38,
    "Gỗ thông": 4.83,
    "Hoa nhài": 2.07,
    "Vanilla": 1.72,
    "Chất định hương": 3.0
  },
  "reasoning": ["lý do 1", "lý do 2"],
  "intensity": "nhẹ/vừa/đậm",
  "spoken_response": "một câu tư vấn ngắn, tự nhiên để đọc thành tiếng"
}
"""

def normalize_percentages(values):
    cleaned = {}
    for key, default in DEFAULTS.items():
        try:
            value = float(values.get(key, default))
        except (TypeError, ValueError, AttributeError):
            value = default
        cleaned[key] = max(0.0, min(20.0, value))

    # Keep fixative within the requested practical UI range.
    cleaned["Chất định hương"] = min(cleaned["Chất định hương"], 10.0)

    total = sum(cleaned.values())
    if total > 40.0:
        scale = 40.0 / total
        cleaned = {key: value * scale for key, value in cleaned.items()}
    return cleaned

@st.cache_resource
def get_whisper_model():
    """Load the local speech model once and reuse it between Streamlit reruns."""
    if WhisperModel is None:
        raise RuntimeError("Chưa cài faster-whisper. Hãy cài các gói trong requirements.txt.")
    return WhisperModel("small", device="cpu", compute_type="int8")


def transcribe_audio_locally(audio_bytes, audio_mime="audio/wav"):
    """Transcribe voice locally; no external transcription API."""
    if WhisperModel is None:
        raise RuntimeError("Chưa cài faster-whisper. Hãy cài các gói trong requirements.txt.")
    import tempfile
    suffix = ".wav"
    mime = (audio_mime or "").lower()
    if "mpeg" in mime or "mp3" in mime:
        suffix = ".mp3"
    elif "webm" in mime:
        suffix = ".webm"
    elif "mp4" in mime:
        suffix = ".mp4"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        whisper = get_whisper_model()
        segments, _ = whisper.transcribe(temp_path, language="vi", vad_filter=True)
        transcript = " ".join(s.text.strip() for s in segments).strip()
        if not transcript:
            raise RuntimeError("Không nhận diện được lời nói. Hãy ghi âm rõ hơn rồi gửi lại.")
        return transcript
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def call_ollama(prompt, base_url, model):
    """Call an Ollama model hosted on a machine you control."""
    if requests is None:
        raise RuntimeError("Chưa cài requests. Hãy cài requirements.txt.")
    endpoint = base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.3}
    }
    try:
        response = requests.post(endpoint, json=payload, timeout=300)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("Không kết nối được Ollama. Hãy khởi động Ollama và kiểm tra OLLAMA_BASE_URL.") from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("AI phản hồi quá lâu. Hãy thử model nhẹ hơn hoặc kiểm tra tài nguyên máy.") from exc
    except requests.exceptions.HTTPError as exc:
        try:
            detail = response.json().get("error", "")
        except Exception:
            detail = ""
        raise RuntimeError(f"Ollama báo lỗi: {detail or response.status_code}") from exc
    try:
        content = response.json().get("message", {}).get("content", "")
        return json.loads(content)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Model không trả về JSON hợp lệ. Hãy gửi lại yêu cầu hoặc thử model khác.") from exc


def get_ai_suggestion(message, current_values, base_url, model,
                      conversation_history=None, audio_bytes=None, audio_mime="audio/wav"):
    """Return consultant response and formula; voice is transcribed locally first."""
    actual_message = message or ""
    if audio_bytes:
        actual_message = transcribe_audio_locally(audio_bytes, audio_mime)
    payload = {
        "current_user_message": actual_message,
        "conversation_history": conversation_history or [],
        "current_formula_percent": current_values,
        "available_ingredients": list(DEFAULTS.keys()),
        "task": (
            "Trò chuyện như chuyên viên tư vấn nước hoa: phản hồi trực tiếp điều người dùng vừa nói, "
            "nhớ ngữ cảnh các lượt trước, hỏi thêm khi cần và vẫn đề xuất công thức tốt nhất hiện tại. "
            "Phân tích yêu cầu bằng tiếng Việt, không chỉ lặp lại công thức."
        ),
    }
    prompt = "Dữ liệu cuộc trò chuyện hiện tại:\\n" + json.dumps(payload, ensure_ascii=False)
    result = call_ollama(prompt, base_url, model)
    result["_transcript"] = actual_message if audio_bytes else ""
    return result


async def _generate_vietnamese_audio(text_to_speak):
    """Generate Vietnamese neural speech audio with Edge TTS."""
    communicate = edge_tts.Communicate(
        str(text_to_speak),
        voice="vi-VN-HoaiMyNeural",
        rate="-5%",
    )
    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            audio_chunks.append(chunk["data"])
    return b"".join(audio_chunks)


def generate_vietnamese_audio(text_to_speak):
    if edge_tts is None:
        raise RuntimeError("Chưa cài edge-tts. Chạy: pip install -r requirements.txt")
    # Streamlit normally runs without an active asyncio loop in this script context.
    return asyncio.run(_generate_vietnamese_audio(text_to_speak))

if "formula" not in st.session_state:
    st.session_state.formula = DEFAULTS.copy()
if "ai_result" not in st.session_state:
    st.session_state.ai_result = None
if "ai_audio" not in st.session_state:
    st.session_state.ai_audio = None
if "ai_audio_text" not in st.session_state:
    st.session_state.ai_audio_text = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_audio_pending" not in st.session_state:
    st.session_state.ai_audio_pending = False
if "last_audio_digest" not in st.session_state:
    st.session_state.last_audio_digest = None
if "chat_error" not in st.session_state:
    st.session_state.chat_error = None

try:
    secret_ollama_url = st.secrets.get("OLLAMA_BASE_URL", "http://localhost:11434")
    secret_model = st.secrets.get("OLLAMA_MODEL", "qwen2.5:7b")
except Exception:
    secret_ollama_url = "http://localhost:11434"
    secret_model = "qwen2.5:7b"

# Welcome screen: play the Vietnamese greeting once, then reveal the original app.
if "intro_done" not in st.session_state:
    st.session_state.intro_done = False
if "welcome_audio" not in st.session_state:
    st.session_state.welcome_audio = None
if "welcome_audio_error" not in st.session_state:
    st.session_state.welcome_audio_error = None

if not st.session_state.intro_done:
    greeting = "Chào mừng bạn đã đến với ứng dụng chế tạo nước hoa Thu Vũ."
    if st.session_state.welcome_audio is None and st.session_state.welcome_audio_error is None:
        try:
            st.session_state.welcome_audio = generate_vietnamese_audio(greeting)
        except Exception as exc:
            st.session_state.welcome_audio_error = str(exc)

    st.markdown(
        """<div class="welcome-screen">
          <div class="welcome-kicker">Autumn Fragrance Studio</div>
          <h1 class="welcome-title">Thu Vũ</h1>
          <p class="welcome-subtitle">Chạm vào hương thu, tạo nên mùi hương mang dấu ấn riêng của bạn.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.session_state.welcome_audio:
        # Tự thử phát ngay khi màn hình chào mừng được tải. Một số trình duyệt
        # chặn autoplay có tiếng; khi đó người dùng vẫn có nút phát dự phòng.
        audio_b64 = base64.b64encode(st.session_state.welcome_audio).decode("ascii")
        components.html(
            f"""<!doctype html><html><body style="margin:0;background:transparent;font-family:Arial,sans-serif">
            <audio id="thu-vu-greeting" controls autoplay playsinline preload="auto" style="width:100%">
              <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
            </audio>
            <div id="autoplay-note" style="font-size:12px;color:#fff1df;text-align:center;margin-top:4px;display:none">
              Trình duyệt đang chặn tự phát âm thanh. Bấm nút phát trên thanh audio để nghe lời chào.
            </div>
            <script>
              const player = document.getElementById('thu-vu-greeting');
              const note = document.getElementById('autoplay-note');
              const tryPlayGreeting = () => {{
                const attempt = player.play();
                if (attempt !== undefined) {{
                  attempt.then(() => {{ note.style.display = 'none'; }})
                    .catch(() => {{ note.style.display = 'block'; }});
                }}
              }};
              player.addEventListener('canplay', tryPlayGreeting, {{ once: true }});
              tryPlayGreeting();
            </script></body></html>""",
            height=66,
            scrolling=False,
        )
    else:
        st.caption("Không tạo được lời chào tự động. Kiểm tra kết nối Internet và tải lại trang.")
    spacer_left, start_col, spacer_right = st.columns([1, 1, 1])
    with start_col:
        st.markdown('<div class="welcome-action">', unsafe_allow_html=True)
        if st.button("Bắt đầu", type="primary", use_container_width=True):
            st.session_state.intro_done = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Ollama runs the model on a machine you control; no provider API key is required.
ollama_base_url = str(secret_ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).strip()
model = str(secret_model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")).strip()

with st.sidebar:
    st.header("🍁 Cài đặt AI")
    st.caption("Đang dùng Ollama chạy cục bộ; không cần API key của nhà cung cấp AI.")
    st.divider()
    batch_ml = st.number_input("Dung tích mẻ (mL)", min_value=1.0, max_value=10000.0, value=10.0, step=1.0)
    st.caption("Mỗi phản hồi tư vấn sẽ tự cập nhật công thức ở các thanh trượt bên phải.")
    st.caption("Ollama phải chạy trên máy chạy app hoặc tại địa chỉ OLLAMA_BASE_URL có thể truy cập.")

# Keep all user input handling before slider widgets are instantiated so their values
# can be updated safely in the same Streamlit rerun.
left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.markdown('<h3 class="description-heading">1. Trò chuyện với chuyên viên Thu Vũ</h3>', unsafe_allow_html=True)
    st.caption("Nhắn bằng văn bản hoặc ghi âm. Bạn có thể trao đổi nhiều lượt để tinh chỉnh mùi hương.")

    # Show the persistent conversation.
    if not st.session_state.chat_history:
        with st.chat_message("assistant"):
            st.write("Chào bạn! Mình là chuyên viên tư vấn mùi hương của Thu Vũ. Bạn muốn tạo mùi hương như thế nào? Có thể kể về cảm giác, nguyên liệu yêu thích hoặc hoàn cảnh sử dụng nhé.")
    else:
        for message_item in st.session_state.chat_history:
            with st.chat_message(message_item["role"]):
                st.write(message_item["content"])

    # Text chat: submission is processed immediately, with no separate Apply button.
    text_message = st.chat_input("Ví dụ: Mình muốn mùi sạch, tươi, hơi gỗ và không quá ngọt…")

    # Voice chat: record, then explicitly send the recording. Digest prevents duplicate turns
    # when Streamlit reruns because another widget changed.
    voice_col, send_col = st.columns([3, 1])
    with voice_col:
        voice_value = st.audio_input("Hoặc ghi âm tin nhắn", help="Nói tự nhiên như đang trao đổi với chuyên viên.")
    voice_bytes = voice_value.getvalue() if voice_value is not None else None
    voice_mime = getattr(voice_value, "type", None) or "audio/wav"
    with send_col:
        st.write("")
        send_voice = st.button("Gửi giọng nói", use_container_width=True, type="secondary")

    incoming_message = None
    incoming_audio = None
    incoming_mime = "audio/wav"
    incoming_digest = None
    if text_message and text_message.strip():
        incoming_message = text_message.strip()
    elif send_voice and voice_bytes:
        import hashlib
        incoming_digest = hashlib.sha256(voice_bytes).hexdigest()
        if incoming_digest == st.session_state.last_audio_digest:
            st.info("Tin nhắn ghi âm này đã được gửi rồi. Hãy ghi âm tin mới nếu muốn tiếp tục.")
        else:
            incoming_message = "Người dùng gửi tin nhắn thoại. Hãy nghe âm thanh đính kèm và phản hồi nội dung họ nói."
            incoming_audio = voice_bytes
            incoming_mime = voice_mime

    if incoming_message is not None:
        if requests is None:
            st.error("Chưa cài requests. Hãy cài lại các gói trong requirements.txt.")
        else:
            # Send prior turns to the local Ollama model as context.
            history_for_model = [
                {"role": item["role"], "content": item["content"]}
                for item in st.session_state.chat_history[-12:]
            ]
            try:
                with st.spinner("Chuyên viên Thu Vũ đang phân tích yêu cầu…"):
                    result = get_ai_suggestion(
                        incoming_message,
                        st.session_state.formula,
                        ollama_base_url,
                        model.strip(),
                        conversation_history=history_for_model,
                        audio_bytes=incoming_audio,
                        audio_mime=incoming_mime,
                    )

                # Normalize and immediately set slider state before those widgets are created below.
                updated = normalize_percentages(result.get("percentages", {}))
                st.session_state.formula = updated.copy()
                for ingredient, value in updated.items():
                    st.session_state[f"slider_{ingredient}"] = float(value)

                assistant_reply = str(
                    result.get("spoken_response")
                    or result.get("summary")
                    or "Mình đã cập nhật công thức theo yêu cầu của bạn."
                ).strip()
                extra_lines = []
                question = str(result.get("clarifying_question", "")).strip()
                if question:
                    extra_lines.append("Mình hỏi thêm một chút: " + question)
                reasoning = result.get("reasoning", [])
                if isinstance(reasoning, list) and reasoning:
                    extra_lines.append("Lý do đề xuất: " + "; ".join(str(item) for item in reasoning[:4]))
                intensity = str(result.get("intensity", "")).strip()
                if intensity:
                    extra_lines.append("Độ đậm dự kiến: " + intensity + ".")
                if extra_lines:
                    assistant_reply += "\n\n" + "\n".join(extra_lines)

                if incoming_audio is not None:
                    user_display = "🎙️ " + str(result.get("_transcript") or "Đã gửi tin nhắn thoại.")
                    st.session_state.last_audio_digest = incoming_digest
                else:
                    user_display = incoming_message
                st.session_state.chat_history.append({"role": "user", "content": user_display})
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
                st.session_state.ai_result = result
                st.session_state.ai_audio_text = str(result.get("spoken_response") or result.get("summary", "")).strip()
                st.session_state.ai_audio = None
                st.session_state.ai_audio_pending = False
                st.session_state.chat_error = None
                if st.session_state.ai_audio_text and edge_tts is not None:
                    try:
                        with st.spinner("Đang tạo giọng đọc tiếng Việt…"):
                            st.session_state.ai_audio = generate_vietnamese_audio(st.session_state.ai_audio_text)
                        st.session_state.ai_audio_pending = bool(st.session_state.ai_audio)
                    except Exception as tts_exc:
                        st.session_state.chat_error = "Tư vấn đã có, nhưng chưa tạo được giọng đọc: " + str(tts_exc)
                st.rerun()
            except json.JSONDecodeError:
                st.error("Ollama trả về dữ liệu không đúng JSON. Hãy gửi lại tin nhắn nhé.")
            except Exception as exc:
                st.error(f"Không thể xử lý cuộc trò chuyện: {exc}")

    if st.session_state.chat_error:
        st.warning(st.session_state.chat_error)
        st.session_state.chat_error = None

    if st.session_state.ai_audio:
        st.audio(
            st.session_state.ai_audio,
            format="audio/mp3",
            autoplay=st.session_state.ai_audio_pending,
        )
        if st.session_state.ai_audio_pending:
            st.caption("Đang thử tự phát phản hồi bằng giọng tiếng Việt. Nếu trình duyệt chặn, bấm nút phát.")
            st.session_state.ai_audio_pending = False

with right:
    st.subheader("2. Công thức phối hương")
    st.caption("Tỷ lệ sẽ tự cập nhật ngay sau mỗi phản hồi của AI — không cần nút áp dụng.")
    edited = {}
    for name, default in DEFAULTS.items():
        slider_key = f"slider_{name}"
        if slider_key not in st.session_state:
            st.session_state[slider_key] = float(st.session_state.formula.get(name, default))
        edited[name] = st.slider(
            f"{name} — {LAYERS[name]} (%)",
            min_value=0.0,
            max_value=20.0,
            step=0.1,
            key=slider_key,
        )

    if st.button("Lưu chỉnh sửa thủ công", use_container_width=True):
        st.session_state.formula = edited.copy()
        st.success("Đã cập nhật công thức.")
        st.rerun()

# Read slider state so displayed formula always matches what the controls currently show.
formula = {name: float(st.session_state.get(f"slider_{name}", st.session_state.formula[name])) for name in DEFAULTS}
st.session_state.formula = formula
total_aroma = sum(formula.values())
solvent = max(0.0, 100.0 - total_aroma)

st.divider()
st.subheader("3. Công thức quy đổi")
st.caption("Tỷ lệ tính trên toàn bộ công thức; dung môi được tính tự động để tổng bằng 100%.")
rows = []
for name, percent in formula.items():
    rows.append({
        "Thành phần": name,
        "Tầng hương / vai trò": LAYERS[name],
        "Tỷ lệ (%)": round(percent, 2),
        f"Thể tích ({batch_ml:g} mL)": round(percent / 100 * batch_ml, 3),
    })
rows.append({
    "Thành phần": "Dung môi (theo công thức nền)",
    "Tầng hương / vai trò": "Dung môi",
    "Tỷ lệ (%)": round(solvent, 2),
    f"Thể tích ({batch_ml:g} mL)": round(solvent / 100 * batch_ml, 3),
})
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)
st.metric("Tổng tỷ lệ", f"{sum(formula.values()) + solvent:.2f}%")
st.download_button(
    "Tải công thức CSV",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="thu_vu_ai_formula.csv",
    mime="text/csv",
    use_container_width=True,
)

with st.expander("Lưu ý quan trọng"):
    st.write(
        "Bạn có thể trò chuyện nhiều lượt bằng văn bản hoặc ghi âm; Ollama dùng ngữ cảnh các lượt gần nhất để tư vấn. Tỷ lệ AI đề xuất được cập nhật trực tiếp vào thanh trượt. "
        "Phần đọc tư vấn dùng giọng tiếng Việt Hoài My Neural qua Edge TTS và cần kết nối mạng. Trình duyệt có thể chặn tự phát âm thanh; khi đó hãy bấm nút phát trên thanh âm thanh. AI chỉ diễn giải cảm nhận chủ quan và đề xuất tỷ lệ, "
        "không xác nhận an toàn hoặc bảo đảm hiệu quả lưu hương. Hãy kiểm tra giới hạn sử dụng của từng nguyên liệu "
        "và thử nghiệm quy mô nhỏ trước khi sử dụng."
    )
