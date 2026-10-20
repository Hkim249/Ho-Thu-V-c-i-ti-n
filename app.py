import os
 import json
 import streamlit as st
 import pandas as pd

 try:
 	from openai import OpenAI
 except ImportError:
 	OpenAI = None

 st.set_page_config(page_title="Thu Vũ AI — Fragrance Studio", page_icon="🌿", layout="wide")

 st.title("Thu Vũ AI — Fragrance Studio")
 st.caption("Mô tả mùi hương bạn muốn. AI sẽ chuyển cảm nhận thành gợi ý công thức có thể kiểm tra và chỉnh sửa.")

 # Formula defaults follow the existing Thu Vũ app's current formulation.
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
 Bạn là chuyên gia tư vấn mùi hương và trợ lý phối hương cho ứng dụng Thu Vũ.
 Mục tiêu: hiểu ngôn ngữ đời thường về mùi hương, đặt câu hỏi khi yêu cầu còn mơ hồ,
 rồi đề xuất tỷ lệ tương đối cho các thành phần hiện có: Cam, Gỗ thông, Hoa nhài,
 Vanilla, Chất định hương.

 Phân loại cảm nhận theo các trục: tươi/citrus, xanh-gỗ, hoa, ngọt-ấm, độ đậm,
 độ sạch, độ lưu hương, độ phù hợp theo mùa/thời điểm. Không khẳng định có thể
 đo chính xác cảm nhận chủ quan của con người. Không tự thêm nguyên liệu ngoài danh sách.
 Trả lời bằng tiếng Việt, ngắn gọn, giải thích vì sao từng thay đổi phù hợp yêu cầu.
 Khi đã đủ thông tin, trả về một đối tượng JSON theo schema:
 {
   "summary": "mô tả ngắn về mùi hương mục tiêu",
   "clarifying_question": "câu hỏi cần hỏi thêm hoặc chuỗi rỗng",
   "percentages": {
 	"Cam": number,
 	"Gỗ thông": number,
 	"Hoa nhài": number,
 	"Vanilla": number,
 	"Chất định hương": number
   },
   "reasoning": ["lý do 1", "lý do 2"],
   "intensity": "nhẹ/vừa/đậm"
 }
 Các số trong percentages là tỷ lệ % của công thức cuối cùng, không phải tỷ lệ tinh dầu nguyên chất.
 Tổng các thành phần hương và chất định hương phải nhỏ hơn 100%, để còn dung môi.
 Giữ tỷ lệ chất định hương trong khoảng 0–10% trừ khi người dùng yêu cầu khác.
 Không đưa ra khẳng định y tế hoặc đảm bảo an toàn da; nhắc người dùng thử nghiệm nhỏ và kiểm tra
 hướng dẫn an toàn của từng nguyên liệu khi cần.
 Chỉ trả JSON hợp lệ, không dùng markdown fences.
 """

 def normalize_percentages(values):
 	keys = list(DEFAULTS)
 	cleaned = {}
     for key in keys:
     	try:
         	value = float(values.get(key, DEFAULTS[key]))
     	except (TypeError, ValueError):
         	value = DEFAULTS[key]
     	cleaned[key] = max(0.0, min(20.0, value))
 	# Ensure total concentrate stays below 100%.
 	total = sum(cleaned.values())
 	if total > 40:
     	scale = 40 / total
     	cleaned = {k: v * scale for k, v in cleaned.items()}
 	return cleaned

 def get_ai_suggestion(description, current_values, api_key, model):
 	if OpenAI is None:
     	raise RuntimeError("Chưa cài thư viện openai. Hãy chạy: pip install -r requirements.txt")
 	client = OpenAI(api_key=api_key)
 	user_payload = {
     	"human_scent_request": description,
         "current_formula_percent": current_values,
         "available_ingredients": list(DEFAULTS.keys()),
     	"task": "Hiểu yêu cầu mùi hương; nếu thiếu thông tin quan trọng thì hỏi một câu. Nếu đủ, đề xuất tỷ lệ phần trăm."
 	}
 	response = client.chat.completions.create(
     	model=model,
  	   temperature=0.4,
         response_format={"type": "json_object"},
     	messages=[
         	{"role": "system", "content": SYSTEM_PROMPT},
         	{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
     	],
 	)
 	return json.loads(response.choices[0].message.content)

 if "formula" not in st.session_state:
 	st.session_state.formula = DEFAULTS.copy()
 if "ai_result" not in st.session_state:
 	st.session_state.ai_result = None

 with st.sidebar:
 	st.header("Cài đặt AI")
 	api_key = st.text_input(
     	"OpenAI API key",
     	type="password",
         value=os.getenv("OPENAI_API_KEY", ""),
     	help="Có thể đặt OPENAI_API_KEY trong Secrets của Streamlit thay vì nhập ở đây."
 	)
 	model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
 	st.divider()
 	batch_ml = st.number_input("Dung tích mẻ (mL)", min_value=1.0, max_value=10000.0, value=10.0, step=1.0)
 	st.caption("AI đưa ra gợi ý; công thức chỉ được áp dụng sau khi bạn chủ động chọn.")

 left, right = st.columns([1.05, 0.95], gap="large")
 with left:
 	st.subheader("1. Mô tả mùi hương bằng ngôn ngữ tự nhiên")
 	description = st.text_area(
     	"Bạn muốn mùi hương như thế nào?",
     	placeholder="Ví dụ: Mùi sạch và tươi như vừa tắm, mở đầu có cam nhẹ, không quá ngọt, sau đó ấm và gỗ nhẹ; độ tỏa hương vừa phải.",
     	height=150
 	)
 	if st.button("Phân tích yêu cầu bằng AI", type="primary", use_container_width=True):
     	if not description.strip():
      	   st.warning("Hãy mô tả mùi hương bạn muốn trước nhé.")
     	elif not api_key.strip():
         	st.error("Chưa có OpenAI API key. Hãy nhập key ở thanh bên hoặc cấu hình OPENAI_API_KEY trong Streamlit Secrets.")
     	else:
         	with st.spinner("Đang phân tích sắc thái mùi hương..."):
             	try:
                     st.session_state.ai_result = get_ai_suggestion(
                     	description, st.session_state.formula, api_key.strip(), model.strip()
                 	)
   	          except Exception as exc:
                 	st.error(f"Không thể gọi AI: {exc}")

 	result = st.session_state.ai_result
 	if result:
     	st.markdown("#### Kết quả AI")
         st.write(result.get("summary", ""))
     	question = result.get("clarifying_question", "")
     	if question:
         	st.info("AI cần làm rõ: " + question)
     	for item in result.get("reasoning", []):
         	st.write("• " + str(item))
     	st.caption("Mức độ đậm dự kiến: " + str(result.get("intensity", "chưa xác định")))
     	if st.button("Áp dụng tỷ lệ AI đề xuất", use_container_width=True):
         	st.session_state.formula = normalize_percentages(result.get("percentages", {}))
         	st.rerun()

 with right:
 	st.subheader("2. Tinh chỉnh công thức")
 	st.caption("Bạn luôn có thể chỉnh tay. Tổng dung dịch được cân bằng bằng cách tính dung môi còn lại.")
 	edited = {}
 	for name, default in DEFAULTS.items():
     	edited[name] = st.slider(
         	f"{name} — {LAYERS[name]} (%)",
         	min_value=0.0, max_value=20.0, step=0.1,
             value=float(st.session_state.formula.get(name, default)),
             key=f"slider_{name}"
     	)
 	if st.button("Lưu chỉnh sửa thủ công", use_container_width=True):
     	st.session_state.formula = edited
     	st.success("Đã cập nhật công thức.")
     	st.rerun()

 formula = st.session_state.formula
 total_aroma = sum(formula.values())
 solvent = max(0.0, 100.0 - total_aroma)
 st.divider()
 st.subheader("3. Công thức quy đổi")
 st.caption("Tỷ lệ dưới đây là % của công thức tổng. Dung môi được tính tự động để tổng bằng 100%.")
 rows = []
 for name, percent in formula.items():
 	rows.append({
     	"Thành phần": name,
     	"Tầng hương / vai trò": LAYERS[name],
     	"Tỷ lệ (%)": round(percent, 2),
     	f"Thể tích ({batch_ml:g} mL)": round(percent / 100 * batch_ml, 3)
 	})
 rows.append({
 	"Thành phần": "Dung môi (cồn/nước theo công thức nền)",
 	"Tầng hương / vai trò": "Dung môi",
 	"Tỷ lệ (%)": round(solvent, 2),
     f"Thể tích ({batch_ml:g} mL)": round(solvent / 100 * batch_ml, 3)
 })
 df = pd.DataFrame(rows)
 st.dataframe(df, use_container_width=True, hide_index=True)
 st.metric("Tổng tỷ lệ", f"{sum(formula.values()) + solvent:.2f}%")
 st.download_button(
 	"Tải công thức CSV",
     data=df.to_csv(index=False).encode("utf-8-sig"),
     file_name="thu_vu_ai_formula.csv",
 	mime="text/csv",
 	use_container_width=True
 )

 with st.expander("Lưu ý quan trọng"):
 	st.write(
     	"AI diễn giải mô tả chủ quan thành gợi ý phối hương, không thể biết chính xác người dùng ngửi thấy gì "
     	"nếu không có dữ liệu phản hồi thực tế. Nên thu thập đánh giá sau khi thử mùi để cá nhân hóa dần. "
     	"Các tỷ lệ trong app là gợi ý công thức, không phải xác nhận an toàn hoặc công thức thương mại đã kiểm nghiệm. "
     	"Kiểm tra giới hạn sử dụng của từng nguyên liệu và thử nghiệm quy mô nhỏ trước khi sử dụng."
 	)


