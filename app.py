import os
import json
import html
import asyncio
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
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
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        background: rgba(255,248,238,.96);
        color: #2d211b;
    }
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

def call_gemini(prompt, api_key, model, audio_bytes=None, audio_mime="audio/wav"):
    if genai is None:
        raise RuntimeError("Chưa cài google-genai. Chạy: pip install -r requirements.txt")

    client = genai.Client(api_key=api_key)
    contents = [prompt]
    if audio_bytes:
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime)
        contents.append(audio_part)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.4,
        },
    )
    if not response.text:
        raise RuntimeError("Gemini không trả về nội dung. Hãy thử lại.")
    return json.loads(response.text)

def get_ai_suggestion(description, current_values, api_key, model, audio_bytes=None, audio_mime="audio/wav"):
    payload = {
        "human_scent_request": description or "",
        "current_formula_percent": current_values,
        "available_ingredients": list(DEFAULTS.keys()),
        "task": (
            "Phân tích yêu cầu mùi hương. Nếu có âm thanh đính kèm, hãy nghe và hiểu lời nói trong âm thanh "
            "rồi kết hợp với phần mô tả văn bản. Đề xuất tỷ lệ phần trăm và giải thích ngắn."
        ),
    }
    prompt = SYSTEM_PROMPT + "\n\nDữ liệu người dùng:\n" + json.dumps(payload, ensure_ascii=False)
    return call_gemini(prompt, api_key, model, audio_bytes, audio_mime)

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

try:
    secret_api_key = st.secrets.get("GOOGLE_API_KEY", "")
    secret_model = st.secrets.get("GOOGLE_MODEL", "gemini-2.5-flash")
except Exception:
    secret_api_key = ""
    secret_model = "gemini-2.5-flash"

with st.sidebar:
    st.header("🍁 Cài đặt AI")
    api_key = st.text_input(
        "Google Gemini API key",
        type="password",
        value=secret_api_key or os.getenv("GOOGLE_API_KEY", ""),
        help="Nên lưu GOOGLE_API_KEY trong Streamlit Secrets, không đăng key lên GitHub."
    )
    model = st.text_input(
        "Gemini model",
        value=secret_model or os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    )
    st.divider()
    batch_ml = st.number_input("Dung tích mẻ (mL)", min_value=1.0, max_value=10000.0, value=10.0, step=1.0)
    st.caption("AI đề xuất tỷ lệ; m cần bấm áp dụng để cập nhật thanh công thức.")

left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.subheader("1. Mô tả mùi hương")
    description = st.text_area(
        "Mùi hương m muốn tạo",
        placeholder="Ví dụ: Mùi sạch và tươi như vừa tắm, cam nhẹ lúc đầu, không quá ngọt, sau đó ấm và gỗ nhẹ.",
        height=130,
    )

    st.markdown("**Hoặc mô tả bằng giọng nói**")
    audio_value = st.audio_input("Ghi âm yêu cầu mùi hương", help="Nói rõ điều m thích hoặc không thích ở mùi hương.")
    audio_bytes = audio_value.getvalue() if audio_value is not None else None
    audio_mime = getattr(audio_value, "type", None) or "audio/wav"

    if st.button("Phân tích bằng Gemini", type="primary", use_container_width=True):
        if not description.strip() and not audio_bytes:
            st.warning("Hãy nhập mô tả bằng chữ hoặc ghi âm yêu cầu trước nhé.")
        elif not api_key.strip():
            st.error("Chưa có Google Gemini API key. Hãy nhập key ở thanh bên hoặc cấu hình GOOGLE_API_KEY trong Streamlit Secrets.")
        else:
            with st.spinner("Gemini đang phân tích yêu cầu mùi hương…"):
                try:
                    st.session_state.ai_result = get_ai_suggestion(
                        description,
                        st.session_state.formula,
                        api_key.strip(),
                        model.strip(),
                        audio_bytes=audio_bytes,
                        audio_mime=audio_mime,
                    )
                    speech = (
                        st.session_state.ai_result.get("spoken_response")
                        or st.session_state.ai_result.get("summary", "")
                    )
                    st.session_state.ai_audio_text = speech
                    st.session_state.ai_audio = None
                    if speech.strip():
                        with st.spinner("Đang tạo giọng đọc tiếng Việt…"):
                            st.session_state.ai_audio = generate_vietnamese_audio(speech)
                except json.JSONDecodeError:
                    st.error("Gemini trả về dữ liệu không đúng JSON. Hãy thử lại.")
                except Exception as exc:
                    st.error(f"Không thể tạo kết quả/giọng đọc: {exc}")

    result = st.session_state.ai_result
    if result:
        st.markdown("#### Kết quả tư vấn")
        st.write(result.get("summary", ""))
        question = result.get("clarifying_question", "")
        if question:
            st.info("Gemini muốn hỏi thêm: " + question)
        for item in result.get("reasoning", []):
            st.write("• " + str(item))
        st.caption("Mức độ đậm dự kiến: " + str(result.get("intensity", "chưa xác định")))

        speech = result.get("spoken_response") or result.get("summary", "")
        if st.session_state.ai_audio:
            st.audio(
                st.session_state.ai_audio,
                format="audio/mp3",
                autoplay=True,
            )
            st.caption("Giọng đọc tiếng Việt tự phát khi có kết quả. Nếu trình duyệt chặn tự phát, bấm nút phát trên thanh âm thanh.")
        else:
            st.warning("Chưa tạo được giọng đọc tự động. Hãy kiểm tra kết nối mạng và cài đặt edge-tts.")

        if st.button("Áp dụng công thức AI đề xuất", use_container_width=True):
            updated = normalize_percentages(result.get("percentages", {}))
            st.session_state.formula = updated
            # Set widget values before those sliders are instantiated on this rerun.
            for name, value in updated.items():
                st.session_state[f"slider_{name}"] = float(value)
            st.rerun()

with right:
    st.subheader("2. Công thức phối hương")
    st.caption("Khi áp dụng đề xuất AI, các thanh trượt sẽ tự cập nhật theo tỷ lệ mới.")
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
        "Phần ghi âm dùng khả năng hiểu âm thanh của Gemini; phần đọc tư vấn dùng giọng tiếng Việt Hoài My Neural qua Edge TTS "
        "và cần kết nối mạng. Trình duyệt có thể chặn tự phát âm thanh; khi đó hãy bấm nút phát trên thanh âm thanh. AI chỉ diễn giải cảm nhận chủ quan và đề xuất tỷ lệ, "
        "không xác nhận an toàn hoặc bảo đảm hiệu quả lưu hương. Hãy kiểm tra giới hạn sử dụng của từng nguyên liệu "
        "và thử nghiệm quy mô nhỏ trước khi sử dụng."
    )

