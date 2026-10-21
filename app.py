import os
import json
import html
import base64
from pathlib import Path
import asyncio
import time
import random
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    # Official Google GenAI SDK.
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
# Local visual assets are bundled with the app so the UI does not depend on remote image URLs.
ASSET_DIR = Path(__file__).parent / "assets"
BACKGROUND_PATH = ASSET_DIR / "autumn_background.png"
AVATAR_PATH = ASSET_DIR / "thu_vu_avatar.png"
BACKGROUND_B64 = base64.b64encode(BACKGROUND_PATH.read_bytes()).decode("ascii") if BACKGROUND_PATH.exists() else ""
BACKGROUND_URL = f"data:image/png;base64,{BACKGROUND_B64}" if BACKGROUND_B64 else ""

st.markdown(
    f"""
    <style>
    :root {{ --amber:#d99a4c; --gold:#f5c47d; --cream:#fff0d7; --brown:#3b281d; --panel:rgba(73,49,34,.78); }}
    .stApp {{ background: radial-gradient(ellipse at 10% 0%,rgba(165,91,40,.22),transparent 35%), linear-gradient(135deg,#1d140f 0%,#342218 50%,#1d1712 100%); color:#fff0df; }}
    [data-testid="stHeader"] {{ background:transparent; }}
    [data-testid="stToolbar"] {{ right:1rem; }}
    [data-testid="stSidebar"] {{ display:none; }}
    .block-container {{ max-width: 1720px; padding: 1.0rem 1.35rem 2rem; }}
    h1,h2,h3,h4 {{ color:#fff0d7 !important; }}
    p, label, [data-testid="stMarkdownContainer"] {{ color:#f6e8d7; }}
    [data-testid="stCaptionContainer"] {{ color:#d9c0a4; }}
    .app-header {{ text-align:center; padding:18px 10px 24px; margin-bottom:14px; border-radius:22px; background-image:linear-gradient(90deg,rgba(34,20,12,.83),rgba(55,32,18,.56),rgba(34,20,12,.78)),url("{BACKGROUND_URL}"); background-size:cover; background-position:center 42%; border:1px solid rgba(255,205,137,.18); box-shadow:0 10px 32px rgba(0,0,0,.18); }}
    .app-header h1 {{ margin:0; font-family:Georgia,'Times New Roman',serif; font-size:clamp(2.5rem,4vw,3.8rem); line-height:1.04; font-weight:500; color:#fff0d5 !important; text-shadow:0 3px 16px rgba(0,0,0,.6); }}
    .app-header .slogan {{ margin-top:8px; font-size:1.02rem; color:#f6d9b3; }}
    .header-ornament {{ color:#e7a64f; letter-spacing:.2em; font-size:1.1rem; }}
    .panel {{ background:linear-gradient(145deg,rgba(82,57,40,.83),rgba(49,34,25,.91)); border:1px solid rgba(240,187,125,.23); border-radius:17px; padding:16px; box-shadow:0 10px 26px rgba(0,0,0,.18); margin-bottom:12px; }}
    .panel-title {{ font-size:1.05rem; font-weight:650; color:#ffedcf; margin:0 0 12px 0; }}
    .nav-stack {{ padding-top:10px; }}
    .nav-item {{ border-radius:12px; padding:12px 10px; margin:5px 0; color:#f3dfc5; font-size:.92rem; border:1px solid transparent; }}
    .nav-item.active {{ background:linear-gradient(100deg,rgba(184,105,39,.86),rgba(113,65,31,.7)); border-color:rgba(255,200,122,.4); color:#fff4df; }}
    .nav-note {{ color:#cdb398; font-size:.78rem; padding:10px 8px; line-height:1.5; }}
    div[data-testid="stButton"] > button {{ border-radius:11px; border:1px solid rgba(243,180,99,.56); background:linear-gradient(110deg,#8e4a24,#b96d32); color:#fff3df; font-weight:600; min-height:2.5rem; }}
    div[data-testid="stButton"] > button:hover {{ border-color:#ffe2b4; color:white; background:linear-gradient(110deg,#a85a2b,#d28a43); }}
    div[data-testid="stButton"] > button[kind="secondary"] {{ background:rgba(104,72,49,.65); border-color:rgba(231,183,129,.3); }}
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{ background:#f2b65e; border:2px solid #fff0d2; }}
    div[data-testid="stSlider"] [data-testid="stTickBar"] {{ background:#a7774a; }}
    div[data-testid="stNumberInput"] input {{ background:#fff1dd !important; color:#2c1a10 !important; border-radius:9px; }}
    [data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input,[data-testid="stChatInput"] textarea,[data-testid="stChatInputTextArea"],[data-testid="stChatInput"] input,[data-baseweb="textarea"] textarea,[data-baseweb="input"] input,[data-testid="stChatInput"] div[contenteditable="true"] {{ background:#fff2df !important; color:#20150f !important; -webkit-text-fill-color:#20150f !important; caret-color:#20150f !important; opacity:1 !important; border-radius:12px !important; }}
    [data-testid="stTextArea"] textarea::placeholder,[data-testid="stChatInput"] textarea::placeholder,[data-testid="stChatInputTextArea"]::placeholder,[data-testid="stChatInput"] input::placeholder,[data-testid="stChatInput"] div[contenteditable="true"]:empty::before {{ color:#7a6250 !important; -webkit-text-fill-color:#7a6250 !important; opacity:1 !important; }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{ background:linear-gradient(145deg,rgba(82,57,40,.83),rgba(49,34,25,.91)); border:1px solid rgba(240,187,125,.23); border-radius:17px; box-shadow:0 10px 26px rgba(0,0,0,.18); }}
    div[data-testid="stVerticalBlockBorderWrapper"] > div {{ border-color:rgba(240,187,125,.23) !important; }}
    [data-testid="stChatMessage"] {{ background:rgba(239,218,191,.08); border:1px solid rgba(244,199,143,.1); border-radius:13px; padding:10px 12px; }}
    [data-testid="stChatMessage"] p {{ color:#fff0df; }}
    [data-testid="stDataFrame"] {{ border-radius:11px; overflow:hidden; }}
    [data-testid="stMetric"] {{ background:rgba(103,64,39,.35); border:1px solid rgba(240,183,118,.28); padding:10px; border-radius:12px; }}
    [data-testid="stAudioInput"] {{ background:rgba(255,241,220,.08); border-radius:12px; padding:7px; }}
    .welcome-screen {{ position:relative; isolation:isolate; min-height:72vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:48px 22px; border-radius:26px; overflow:hidden; background-image:linear-gradient(90deg,rgba(15,10,6,.22),rgba(22,13,7,.28)),url("{BACKGROUND_URL}"); background-size:cover; background-position:center; border:1px solid rgba(255,211,146,.25); box-shadow:0 18px 55px rgba(0,0,0,.35); }}
    .welcome-title {{ color:#fff1d8 !important; font-family:Georgia,'Times New Roman',serif; font-size:clamp(3.6rem,8vw,6.4rem); line-height:1.04; font-weight:500; margin:0; text-shadow:0 4px 24px rgba(0,0,0,.65); }}
    .welcome-slogan {{ margin-top:18px; color:#ffe0ad; font-size:clamp(1.05rem,2vw,1.5rem); text-shadow:0 2px 12px #24160d; }}
    .welcome-ornament {{ color:#e8a74d; font-size:1.35rem; margin-top:12px; letter-spacing:.22em; }}
    .welcome-action div[data-testid="stButton"] > button {{ min-height:3.7rem; border-radius:999px; font-size:1.2rem; background:linear-gradient(110deg,#8d451f,#c97834); border:2px solid #f4bd70; box-shadow:0 8px 30px rgba(0,0,0,.35); }}
    .quick-label {{ color:#d8b995; font-size:.84rem; margin:7px 0 5px; }}
    .status-valid {{ background:rgba(71,89,38,.55); border:1px solid rgba(183,208,122,.45); border-radius:10px; padding:10px; color:#eff7d9; font-size:.85rem; }}
    .safety-note {{ background:#f2d0a3; color:#543017; padding:13px 14px; border-radius:12px; font-size:.87rem; }}
    .safety-note span {{ color:#543017; }}
    @media (max-width: 1050px) {{ .block-container {{ padding: .6rem .6rem 1.5rem; }} .app-header {{ padding:15px 8px; }} }}
    </style>
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
    """Call Gemini and retry transient overload/rate-limit/server errors with backoff."""
    if genai is None or types is None:
        raise RuntimeError(
            "Chưa cài google-genai. Hãy cài các gói trong requirements.txt rồi chạy lại app."
        )

    client = genai.Client(api_key=api_key)
    contents = [prompt]
    if audio_bytes:
        contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))

    retryable_statuses = {429, 500, 502, 503, 504}
    max_attempts = 4  # first attempt + up to 3 retries
    for attempt in range(max_attempts):
        try:
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
        except Exception as exc:
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            message = str(exc).lower()
            if status is None:
                for candidate in retryable_statuses:
                    if str(candidate) in message or f"http {candidate}" in message:
                        status = candidate
                        break
                if "resource_exhausted" in message or "rate limit" in message:
                    status = 429
                elif "service unavailable" in message or "overloaded" in message:
                    status = 503
            should_retry = status in retryable_statuses or any(
                token in message for token in ("temporarily unavailable", "connection reset", "timed out", "timeout")
            )
            if not should_retry or attempt >= max_attempts - 1:
                if should_retry:
                    raise RuntimeError(
                        "Gemini vẫn đang quá tải hoặc giới hạn lượt gọi sau 4 lần thử. "
                        "Đợi khoảng 30–60 giây rồi gửi lại; công thức hiện tại vẫn được giữ nguyên."
                    ) from exc
                raise
            delay = min(8.0, 1.5 * (2 ** attempt)) + random.uniform(0, 0.5)
            time.sleep(delay)

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

    st.markdown(
        '''<div class="welcome-screen">
          <h1 class="welcome-title">Thu Vũ</h1>
          <div class="welcome-ornament">〰 ❧ 〰</div>
          <div class="welcome-slogan">Hương thu theo cách của bạn</div>
        </div>''',
        unsafe_allow_html=True,
    )
    if st.session_state.welcome_audio:
        audio_b64 = base64.b64encode(st.session_state.welcome_audio).decode("ascii")
        components.html(
            f'''<!doctype html><html><body style="margin:0;background:transparent">
            <audio id="thu-vu-greeting" autoplay playsinline preload="auto" style="display:none">
              <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
            </audio><script>const p=document.getElementById('thu-vu-greeting');if(p){{const r=p.play();if(r&&r.catch)r.catch(()=>{{}});}}</script>
            </body></html>''', height=0, scrolling=False,
        )
    _, start_col, _ = st.columns([1, 1, 1])
    with start_col:
        st.markdown('<div class="welcome-action">', unsafe_allow_html=True)
        if st.button("Bắt đầu  ›", type="primary", use_container_width=True):
            st.session_state.intro_done = True
            st.session_state.main_greeting_pending = True
            st.session_state.main_greeting_audio = None
            st.session_state.main_greeting_error = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

api_key = str(secret_api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
model = str(secret_model or os.getenv("GOOGLE_MODEL", "gemini-3.1-flash-lite")).strip()

# Main dashboard header: title contains only the requested app name and slogan.
st.markdown(
    '''<div class="app-header"><h1>Thu Vũ</h1><div class="header-ornament">❧ ───── 🍂 ───── ❧</div><div class="slogan">Hương thu theo cách của bạn</div></div>''',
    unsafe_allow_html=True,
)

if st.session_state.main_greeting_pending:
    main_greeting = (
        "Chào bạn! Mình là chuyên viên tư vấn mùi hương của Thu Vũ. "
        "Bạn muốn tạo mùi hương như thế nào? Có thể kể về cảm giác, nguyên liệu yêu thích "
        "hoặc hoàn cảnh sử dụng nhé."
    )
    if st.session_state.main_greeting_audio is None and st.session_state.main_greeting_error is None:
        try:
            with st.spinner("Đang chuẩn bị lời chào…"):
                st.session_state.main_greeting_audio = generate_vietnamese_audio(main_greeting)
        except Exception as exc:
            st.session_state.main_greeting_error = str(exc)
    if st.session_state.main_greeting_audio:
        greeting_b64 = base64.b64encode(st.session_state.main_greeting_audio).decode("ascii")
        components.html(
            f'''<!doctype html><html><body style="margin:0;background:transparent"><audio autoplay playsinline preload="auto" style="display:none"><source src="data:audio/mpeg;base64,{greeting_b64}" type="audio/mpeg"></audio><script>const a=document.querySelector('audio');if(a){{const r=a.play();if(r&&r.catch)r.catch(()=>{{}});}}</script></body></html>''',
            height=0, scrolling=False,
        )
    st.session_state.main_greeting_pending = False

# Main grid: icon toolbar/navigation, formula controls, AI consultant.
nav_col, center_col, chat_col = st.columns([0.62, 1.23, 1.16], gap="small")
with nav_col:
    st.markdown('<div class="panel nav-stack"><div class="panel-title">🍂 Điều hướng</div><div class="nav-item active">🌿　Phối hương</div><div class="nav-item">▢　AI tư vấn</div><div class="nav-item">⚗　Công thức</div><div class="nav-item">▱　Lưu & Tải</div><div class="nav-item">♧　Hướng dẫn</div><div class="nav-note">Tùy chỉnh hương thơm theo cảm nhận riêng của bạn.</div></div>', unsafe_allow_html=True)

# Placeholders let the chat be processed before the sliders are created, so AI changes apply immediately.
with center_col:
    formula_slot = st.empty()
    summary_slot = st.empty()
with chat_col:
    with st.container(border=True):
        st.markdown('<div class="panel-title">🍂 AI tư vấn hương thơm</div>', unsafe_allow_html=True)
        avatar_col, greeting_col = st.columns([0.72, 1.28], gap="small")
        with avatar_col:
            if AVATAR_PATH.exists():
                st.image(str(AVATAR_PATH), use_container_width=True)
        with greeting_col:
            st.markdown('<div style="background:#f0d6b6;color:#3c2618;border-radius:15px;padding:13px;font-size:.9rem;line-height:1.55">Xin chào!<br/>Tớ là Thu Vũ AI 🍃<br/>Hãy kể cho tớ mùi hương bạn thích, tớ sẽ gợi ý công thức phù hợp nhé!</div>', unsafe_allow_html=True)

        # Persistent conversation history.
        if st.session_state.chat_history:
            for message_item in st.session_state.chat_history[-8:]:
                with st.chat_message(message_item["role"], avatar=(str(AVATAR_PATH) if message_item["role"] == "assistant" and AVATAR_PATH.exists() else None)):
                    st.write(message_item["content"])

        st.markdown('<div class="quick-label">Gợi ý nhanh:</div>', unsafe_allow_html=True)
        quick1, quick2 = st.columns(2, gap="small")
        quick3, quick4 = st.columns(2, gap="small")
        quick_prompt = None
        with quick1:
            if st.button("Ấm áp, dịu nhẹ", use_container_width=True): quick_prompt = "Mình muốn mùi hương ấm áp, dịu nhẹ."
        with quick2:
            if st.button("Thanh mát, trong lành", use_container_width=True): quick_prompt = "Mình muốn mùi hương thanh mát, trong lành."
        with quick3:
            if st.button("Ngọt ngào, quyến rũ", use_container_width=True): quick_prompt = "Mình muốn mùi hương ngọt ngào, quyến rũ."
        with quick4:
            if st.button("Gỗ trầm, sâu lắng", use_container_width=True): quick_prompt = "Mình muốn mùi hương gỗ trầm, sâu lắng."

        text_message = st.chat_input("Nhập mô tả mùi hương của bạn…")
        voice_value = st.audio_input("🎙️ Hoặc ghi âm tin nhắn", help="Nói tự nhiên như đang trao đổi với chuyên viên.")
        voice_bytes = voice_value.getvalue() if voice_value is not None else None
        voice_mime = getattr(voice_value, "type", None) or "audio/wav"
        send_voice = st.button("Gửi giọng nói", use_container_width=True, type="secondary")

        incoming_message = None
        incoming_audio = None
        incoming_mime = "audio/wav"
        incoming_digest = None
        if text_message and text_message.strip():
            incoming_message = text_message.strip()
        elif quick_prompt:
            incoming_message = quick_prompt
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
            if not api_key:
                st.error("Chưa tìm thấy GOOGLE_API_KEY trong Streamlit Secrets. Hãy kiểm tra cấu hình Secrets của ứng dụng.")
            elif genai is None:
                st.error("Chưa cài google-genai. Hãy cài lại các gói trong requirements.txt rồi triển khai app.")
            else:
                history_for_model = [{"role": item["role"], "content": item["content"]} for item in st.session_state.chat_history[-12:]]
                try:
                    with st.spinner("Thu Vũ đang lắng nghe và tư vấn…"):
                        result = get_ai_suggestion(
                            incoming_message, st.session_state.formula, api_key, model,
                            conversation_history=history_for_model, audio_bytes=incoming_audio, audio_mime=incoming_mime,
                        )
                    updated = normalize_percentages(result.get("percentages", {}))
                    st.session_state.formula = updated.copy()
                    for ingredient, value in updated.items():
                        st.session_state[f"slider_{ingredient}"] = float(value)
                    assistant_reply = str(result.get("spoken_response") or result.get("summary") or "Mình đã cập nhật công thức theo yêu cầu của bạn.").strip()
                    paragraphs = [part.strip() for part in assistant_reply.split("\n\n") if part.strip()]
                    assistant_reply = paragraphs[0] if paragraphs else "Mình đã cập nhật công thức theo yêu cầu của bạn."
                    user_display = "🎙️ Tin nhắn thoại đã gửi (Gemini đã phân tích âm thanh)." if incoming_audio is not None else incoming_message
                    if incoming_audio is not None:
                        st.session_state.last_audio_digest = incoming_digest
                    st.session_state.chat_history.append({"role": "user", "content": user_display})
                    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
                    st.session_state.ai_result = result
                    st.session_state.ai_audio_text = assistant_reply
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
            st.audio(st.session_state.ai_audio, format="audio/mp3", autoplay=st.session_state.ai_audio_pending)
            if st.session_state.ai_audio_pending:
                st.caption("Nếu trình duyệt chặn tự phát, bấm nút phát.")
                st.session_state.ai_audio_pending = False

# Formula controls, rendered into their placeholder after chat processing.
with formula_slot.container():
    with st.container(border=True):
        st.markdown('<div class="panel-title">🍃 Tùy chỉnh công thức</div>', unsafe_allow_html=True)
        batch_ml = st.slider("Dung tích pha chế (mL)", min_value=1, max_value=20, value=int(st.session_state.get("batch_ml", 10)), step=1, key="batch_ml")
        st.markdown('<div style="display:flex;justify-content:space-between;color:#d9b995;font-size:.78rem;margin-top:-8px"><span>1 mL</span><span>20 mL</span></div>', unsafe_allow_html=True)
        edited = {}
        for name, default in DEFAULTS.items():
            slider_key = f"slider_{name}"
            if slider_key not in st.session_state:
                st.session_state[slider_key] = float(st.session_state.formula.get(name, default))
            edited[name] = st.slider(
                f"{name} ({LAYERS[name]}) (%)", min_value=0.0,
                max_value=(10.0 if name == "Chất định hương" else 20.0), step=0.01,
                key=slider_key,
            )
        st.session_state.formula = edited.copy()
        st.markdown('</div>', unsafe_allow_html=True)

formula = {name: float(st.session_state.get(f"slider_{name}", st.session_state.formula[name])) for name in DEFAULTS}
st.session_state.formula = formula
total_aroma = sum(formula.values())
solvent = max(0.0, 100.0 - total_aroma)
rows = []
for name, percent in formula.items():
    rows.append({"Thành phần": name, "Tỉ lệ (%)": round(percent, 3), "Thể tích (mL)": round(percent / 100 * batch_ml, 3)})
rows.append({"Thành phần": "Dung môi (cồn + nước)", "Tỉ lệ (%)": round(solvent, 3), "Thể tích (mL)": round(solvent / 100 * batch_ml, 3)})
rows.append({"Thành phần": "Tổng cộng", "Tỉ lệ (%)": round(total_aroma + solvent, 3), "Thể tích (mL)": round(batch_ml, 3)})
df = pd.DataFrame(rows)

with summary_slot.container():
    with st.container(border=True):
        st.markdown('<div class="panel-title">🍂 Tổng hợp công thức</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True, height=270)
        if total_aroma <= 40.0 and formula.get("Chất định hương", 0) <= 10.0:
            st.markdown('<div class="status-valid">🟢 Công thức hợp lệ (tổng = 100%)</div>', unsafe_allow_html=True)
        else:
            st.warning("Tổng thành phần hương vượt giới hạn quy định. Hãy giảm tỷ lệ trước khi tải công thức.")
        st.download_button(
            "⬇ Tải công thức (CSV)", data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="thu_vu_formula.csv", mime="text/csv", use_container_width=True,
            disabled=(total_aroma > 40.0 or formula.get("Chất định hương", 0) > 10.0),
        )

with chat_col:
    with st.container(border=True):
        st.markdown('<div class="panel-title" style="margin-top:8px">🌼 Mô tả mùi hương</div>', unsafe_allow_html=True)
        ai_result = st.session_state.get("ai_result") or {}
        description = ai_result.get("summary") or "AI sẽ phân tích và mô tả mùi hương dựa trên công thức của bạn."
        st.markdown(f'<div style="background:#efd5b5;color:#4b301d;border-radius:14px;padding:20px;min-height:150px;text-align:center;display:flex;align-items:center;justify-content:center;line-height:1.6">{html.escape(str(description))}</div>', unsafe_allow_html=True)
        st.markdown('<div class="safety-note" style="margin-top:12px">ⓘ　<span>Cần giáo viên duyệt an toàn trước khi pha.</span></div>', unsafe_allow_html=True)

with st.expander("Hướng dẫn và lưu ý an toàn"):
    st.write(
        "Bạn có thể trò chuyện nhiều lượt bằng văn bản hoặc ghi âm; Gemini dùng ngữ cảnh các lượt gần nhất để tư vấn. "
        "Tỷ lệ AI đề xuất được cập nhật trực tiếp vào thanh trượt. Phản hồi có thể được đọc bằng giọng tiếng Việt Hoài My Neural qua Edge TTS, cần kết nối mạng; trình duyệt có thể chặn tự phát âm thanh. "
        "AI chỉ diễn giải cảm nhận chủ quan và đề xuất tỷ lệ, không xác nhận an toàn hoặc bảo đảm hiệu quả lưu hương. "
        "Hãy kiểm tra giới hạn sử dụng của từng nguyên liệu và thử nghiệm quy mô nhỏ trước khi sử dụng."
    )
