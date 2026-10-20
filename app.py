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
