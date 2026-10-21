import os
import json
import html
import base64
from pathlib import Path
import asyncio
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    # Official modern Gemini SDK; supports Gemini 2.5 Flash.
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

st.set_page_config(
    page_title="Thu Vũ",
    page_icon="🍂",
    layout="wide",
)

# Autumn-inspired interface. All CSS is decorative; app functionality remains native Streamlit.
style_html = (
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
        position: relative; isolation: isolate;
        min-height: 72vh; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center;
        padding: 56px 24px; border-radius: 28px; overflow: hidden;
        background-image: linear-gradient(110deg, rgba(20,15,12,.18), rgba(35,22,15,.12)),
          url('__WELCOME_BACKGROUND__');
        background-size: cover; background-position: center;
        border: 1px solid rgba(255,218,171,.48); box-shadow: 0 18px 55px rgba(0,0,0,.35);
        animation: welcomeReveal 1s ease-out both;
    }
    .welcome-screen::before {
        content: ""; position: absolute; inset: -35%; z-index: -1; pointer-events: none;
        background: linear-gradient(112deg, transparent 38%, rgba(255,230,184,.20) 50%, transparent 62%);
        transform: translateX(-65%) rotate(8deg); animation: autumnShimmer 9s ease-in-out infinite;
    }
    .welcome-kicker { color: #ffd8a8 !important; letter-spacing: .28em; text-transform: uppercase; font-size: .8rem; margin-bottom: 16px; animation: titleFloat 4.5s ease-in-out infinite; }
    .welcome-slogan { color: #fff0dc !important; font-size: clamp(1rem, 2.5vw, 1.45rem); letter-spacing: .04em; margin: 14px 0 0; text-shadow: 0 2px 12px rgba(0,0,0,.6); animation: titleFloat 4.5s ease-in-out infinite; }
    .welcome-title { color: #fff7ec !important; font-size: clamp(3rem, 8vw, 6rem); line-height: 1.05; font-weight: 700; margin: 0; text-shadow: 0 4px 24px rgba(0,0,0,.5); animation: titleFloat 4.5s ease-in-out infinite; }
    .welcome-action div[data-testid="stButton"] > button { min-height: 3.4rem; padding: 0 3rem; border-radius: 999px; font-size: 1.05rem; background: linear-gradient(110deg, #9e512e, #d69a53); border: 1px solid #ffe1b6; box-shadow: 0 8px 26px rgba(0,0,0,.3); transition: transform .25s ease, box-shadow .25s ease; }
    .welcome-action div[data-testid="stButton"] > button:hover { transform: translateY(-3px); box-shadow: 0 12px 32px rgba(214,154,83,.35); }
    @keyframes welcomeReveal { from { opacity: 0; transform: translateY(8px) scale(.99); } to { opacity: 1; transform: translateY(0) scale(1); } }
    @keyframes autumnShimmer { 0%, 15% { transform: translateX(-65%) rotate(8deg); } 65%, 100% { transform: translateX(65%) rotate(8deg); } }
    @keyframes titleFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
    @media (prefers-reduced-motion: reduce) { .welcome-screen, .welcome-screen::before, .welcome-kicker, .welcome-title, .welcome-slogan { animation: none !important; } }
    </style>
    <div class="autumn-banner">
      <h1>Thu Vũ</h1>
      <p>Hương thu theo cách riêng của bạn</p>
    </div>
    """
)
_bg_bytes = (Path(__file__).resolve().parent / "thu_vu_welcome_background.jpg").read_bytes()
_bg_uri = "data:image/jpeg;base64," + base64.b64encode(_bg_bytes).decode("ascii")
st.markdown(style_html.replace("__WELCOME_BACKGROUND__", _bg_uri), unsafe_allow_html=True)

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
Không tuyên bố đo chính xác cảm nhận chủ quan. Luôn trả lời bằng tiếng Việt tự nhiên. Khi nói với người dùng, gọi họ là “bạn” và tự xưng là “mình”; không dùng “tôi”, “quý khách” hoặc cách xưng hô khác.
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
  "spoken_response": "phản hồi đầy đủ, tự nhiên bằng tiếng Việt, xưng mình và gọi người dùng là bạn; nội dung này sẽ được đọc thành tiếng"
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

def call_gemini(prompt, api_key, model, audio_bytes=None, audio_mime="audio/wav"):
    """Call Gemini 2.5 Flash using the official google-genai SDK."""
    if genai is None or types is None:
        raise RuntimeError(
            "Chưa cài google-genai. Hãy cài các gói trong requirements.txt rồi chạy lại app."
        )

    # API key is loaded from Streamlit Secrets/environment; it is never requested in the UI.
    client = genai.Client(api_key=api_key)
    contents = [prompt]
    if audio_bytes:
        contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))

    # Gemini 2.5 Flash uses the current API settings; deprecated sampling options are omitted.
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config={"response_mime_type": "application/json"},
    )
    response_text = getattr(response, "text", None)
    if not response_text:
        raise RuntimeError("Gemini không trả về nội dung. Hãy thử lại.")
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini trả về dữ liệu không đúng định dạng JSON. Hãy gửi lại yêu cầu.") from exc

def get_ai_suggestion(message, current_values, api_key, model, conversation_history=None, audio_bytes=None, audio_mime="audio/wav"):
    """Return one consultant response and a fresh formula for the current conversation turn."""
    payload = {
        "current_user_message": message or "",
        "conversation_history": conversation_history or [],
        "current_formula_percent": current_values,
        "available_ingredients": list(DEFAULTS.keys()),
        "task": (
            "Hãy trò chuyện như một chuyên viên tư vấn nước hoa: luôn gọi người dùng là bạn và xưng mình, "
            "phản hồi trực tiếp điều người dùng vừa nói, nhớ ngữ cảnh các lượt trước, hỏi thêm khi cần "
            "và vẫn đề xuất công thức tốt nhất hiện tại. Nội dung phản hồi phải bằng tiếng Việt. "
            "Nếu có âm thanh đính kèm, hãy nghe và hiểu lời nói trong âm thanh. "
            "Mỗi lượt phải trả lời tự nhiên, hữu ích, không chỉ lặp lại công thức."
        ),
    }
    prompt = SYSTEM_PROMPT + "\n\nDữ liệu cuộc trò chuyện hiện tại:\n" + json.dumps(payload, ensure_ascii=False)
    return call_gemini(prompt, api_key, model, audio_bytes, audio_mime)

async def _generate_vietnamese_audio(text_to_speak):
    """Generate Vietnamese neural speech audio with Edge TTS."""
    communicate = edge_tts.Communicate(
        str(text_to_speak),
        voice="vi-VN-HoaiMyNeural",
        rate="+25%",
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
    secret_api_key = st.secrets.get("GOOGLE_API_KEY", "")
    secret_model = st.secrets.get("GOOGLE_MODEL", "gemini-3.1-flash-lite")
except Exception:
    secret_api_key = ""
    secret_model = "gemini-3.1-flash-lite"

# Welcome screen: play the Vietnamese greeting once, then reveal the original app.
if "intro_done" not in st.session_state:
    st.session_state.intro_done = False
if "welcome_audio" not in st.session_state:
    st.session_state.welcome_audio = None
if "welcome_audio_error" not in st.session_state:
    st.session_state.welcome_audio_error = None
if "main_greeting_pending" not in st.session_state:
    st.session_state.main_greeting_pending = False
if "main_greeting_audio" not in st.session_state:
    st.session_state.main_greeting_audio = None
if "main_greeting_error" not in st.session_state:
    st.session_state.main_greeting_error = None

if not st.session_state.intro_done:
    greeting = "chào mừng bạn đã đến với ứng dụng điều chế nước hoa thu vũ, nơi tạo ra mùa thu theo cách riêng của bạn. Hãy ấn nút bắt đầu để tiếp tục"
    if st.session_state.welcome_audio is None and st.session_state.welcome_audio_error is None:
        try:
            st.session_state.welcome_audio = generate_vietnamese_audio(greeting)
        except Exception as exc:
            st.session_state.welcome_audio_error = str(exc)

    # Keep the original cover image and title, but do not display the greeting text or audio controls.
    st.markdown(
        """<div class="welcome-screen">
          <h1 class="welcome-title">Thu Vũ</h1>
          <p class="welcome-slogan">Hương thu theo cách riêng của bạn</p>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.session_state.welcome_audio:
        # Hidden audio player: attempt automatic Vietnamese speech without showing text or controls.
        audio_b64 = base64.b64encode(st.session_state.welcome_audio).decode("ascii")
        components.html(
            f"""<!doctype html><html><body style="margin:0;background:transparent">
            <audio id="thu-vu-greeting" autoplay playsinline preload="auto" style="display:none">
              <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
            </audio>
            <script>
              const player = document.getElementById('thu-vu-greeting');
              const tryPlayGreeting = () => {{
                const attempt = player.play();
                if (attempt !== undefined) attempt.catch(() => {{}});
              }};
              player.addEventListener('canplay', tryPlayGreeting, {{ once: true }});
              tryPlayGreeting();
            </script></body></html>""",
            height=0,
            scrolling=False,
        )
    spacer_left, start_col, spacer_right = st.columns([1, 1, 1])
    with start_col:
        st.markdown('<div class="welcome-action">', unsafe_allow_html=True)
        if st.button("Bắt đầu", type="primary", use_container_width=True):
            st.session_state.intro_done = True
            st.session_state.main_greeting_pending = True
            st.session_state.main_greeting_audio = None
            st.session_state.main_greeting_error = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# API key is read from Streamlit Secrets (or the environment); it is never requested in the UI.
api_key = str(secret_api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
model = str(secret_model or os.getenv("GOOGLE_MODEL", "gemini-3.1-flash-lite")).strip()

with st.sidebar:
    st.header("🍁 Cài đặt AI")
    st.divider()
    batch_ml = st.number_input("Dung tích mẻ (mL)", min_value=1.0, max_value=10000.0, value=10.0, step=1.0)
    st.caption("Mỗi phản hồi tư vấn sẽ tự cập nhật công thức ở các thanh trượt bên phải.")

# When the main screen first opens, automatically try to read the existing consultant greeting.
# Browsers may block autoplay with sound; the audio controls remain available as a fallback.
if st.session_state.main_greeting_pending:
    main_greeting = (
        "Chào bạn! Mình là chuyên viên tư vấn mùi hương của Thu Vũ. "
        "Bạn muốn tạo mùi hương như thế nào? Có thể kể về cảm giác, nguyên liệu yêu thích "
        "hoặc hoàn cảnh sử dụng nhé."
    )
    if st.session_state.main_greeting_audio is None and st.session_state.main_greeting_error is None:
        try:
            with st.spinner("Chuyên viên Thu Vũ đang chuẩn bị lời chào…"):
                st.session_state.main_greeting_audio = generate_vietnamese_audio(main_greeting)
        except Exception as exc:
            st.session_state.main_greeting_error = str(exc)
    if st.session_state.main_greeting_audio:
        greeting_b64 = base64.b64encode(st.session_state.main_greeting_audio).decode("ascii")
        components.html(
            f"""<!doctype html><html><body style=\"margin:0;background:transparent;font-family:Arial,sans-serif\">
            <audio id=\"thu-vu-main-greeting\" autoplay playsinline preload=\"auto\" style=\"display:none\">
              <source src=\"data:audio/mpeg;base64,{greeting_b64}\" type=\"audio/mpeg\">
            </audio>
            <script>
              const player = document.getElementById('thu-vu-main-greeting');
              const attemptPlay = () => {{
                const attempt = player.play();
                if (attempt !== undefined) attempt.catch(() => {{}});
              }};
              player.addEventListener('canplay', attemptPlay, {{ once: true }});
              attemptPlay();
            </script></body></html>""",
            height=0,
            scrolling=False,
        )
    elif st.session_state.main_greeting_error:
        st.caption("Chưa phát được lời chào tự động. Bạn vẫn có thể bắt đầu trò chuyện; hãy kiểm tra kết nối mạng nếu muốn nghe giọng đọc.")
    st.session_state.main_greeting_pending = False

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
        if not api_key.strip():
            st.error("Chưa tìm thấy GOOGLE_API_KEY trong Streamlit Secrets. Hãy kiểm tra cấu hình Secrets của ứng dụng.")
        elif genai is None:
            st.error("Chưa cài google-genai. Hãy cài lại các gói trong requirements.txt rồi triển khai app.")
        else:
            # Send prior turns to Gemini as context, excluding any unprocessed turn.
            history_for_model = [
                {"role": item["role"], "content": item["content"]}
                for item in st.session_state.chat_history[-12:]
            ]
            try:
                with st.spinner("Chuyên viên Thu Vũ đang lắng nghe và tư vấn…"):
                    result = get_ai_suggestion(
                        incoming_message,
                        st.session_state.formula,
                        api_key.strip(),
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
                # Keep only the first paragraph of the AI response; omit the extra
                # follow-up/explanation paragraph because the user does not need it.
                paragraphs = [part.strip() for part in assistant_reply.split("\n\n") if part.strip()]
                assistant_reply = paragraphs[0] if paragraphs else "Mình đã cập nhật công thức theo yêu cầu của bạn."

                if incoming_audio is not None:
                    user_display = "🎙️ Tin nhắn thoại đã gửi (Gemini đã phân tích âm thanh)."
                    st.session_state.last_audio_digest = incoming_digest
                else:
                    user_display = incoming_message
                st.session_state.chat_history.append({"role": "user", "content": user_display})
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
                st.session_state.ai_result = result
                # Read only the first paragraph retained for the assistant response.
                st.session_state.ai_audio_text = assistant_reply.strip()
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
                st.error("Gemini trả về dữ liệu không đúng JSON. Hãy gửi lại tin nhắn nhé.")
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
        "Bạn có thể trò chuyện nhiều lượt bằng văn bản hoặc ghi âm; Gemini dùng ngữ cảnh các lượt gần nhất để tư vấn. Tỷ lệ AI đề xuất được cập nhật trực tiếp vào thanh trượt. "
        "Lời chào khi mở giao diện chính và toàn bộ nội dung phản hồi của AI đều được đọc thử tự động bằng giọng tiếng Việt Hoài My Neural qua Edge TTS, cần kết nối mạng. Trình duyệt có thể chặn tự phát âm thanh; khi đó hãy bấm nút phát trên thanh âm thanh. AI chỉ diễn giải cảm nhận chủ quan và đề xuất tỷ lệ, "
        "không xác nhận an toàn hoặc bảo đảm hiệu quả lưu hương. Hãy kiểm tra giới hạn sử dụng của từng nguyên liệu "
        "và thử nghiệm quy mô nhỏ trước khi sử dụng."
    )

