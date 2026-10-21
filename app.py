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
        position: relative; isolation: isolate;
        min-height: 72vh; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center;
        padding: 56px 24px; border-radius: 28px; overflow: hidden;
        background-image: linear-gradient(110deg, rgba(20,15,12,.18), rgba(35,22,15,.12)),
          url('data:image/jpeg;base64,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');
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
    .welcome-title { color: #fff7ec !important; font-size: clamp(3rem, 8vw, 6rem); line-height: 1.05; font-weight: 700; margin: 0; text-shadow: 0 4px 24px rgba(0,0,0,.5); animation: titleFloat 4.5s ease-in-out infinite; }
    .welcome-action div[data-testid="stButton"] > button { min-height: 3.4rem; padding: 0 3rem; border-radius: 999px; font-size: 1.05rem; background: linear-gradient(110deg, #9e512e, #d69a53); border: 1px solid #ffe1b6; box-shadow: 0 8px 26px rgba(0,0,0,.3); transition: transform .25s ease, box-shadow .25s ease; }
    .welcome-action div[data-testid="stButton"] > button:hover { transform: translateY(-3px); box-shadow: 0 12px 32px rgba(214,154,83,.35); }
    @keyframes welcomeReveal { from { opacity: 0; transform: translateY(8px) scale(.99); } to { opacity: 1; transform: translateY(0) scale(1); } }
    @keyframes autumnShimmer { 0%, 15% { transform: translateX(-65%) rotate(8deg); } 65%, 100% { transform: translateX(65%) rotate(8deg); } }
    @keyframes titleFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
    @media (prefers-reduced-motion: reduce) { .welcome-screen, .welcome-screen::before, .welcome-kicker, .welcome-title { animation: none !important; } }
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
        rate="+50%",
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
          <div class="welcome-kicker">Autumn Fragrance Studio</div>
          <h1 class="welcome-title">Thu Vũ</h1>
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


