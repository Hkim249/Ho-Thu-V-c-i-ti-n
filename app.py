                            incoming_message, st.session_state.formula, api_key, model,
                            conversation_history=history_for_model, audio_bytes=incoming_audio, audio_mime=incoming_mime,
                        )
                    if not isinstance(result, dict):
                        raise RuntimeError("Phản hồi AI không hợp lệ. Hãy gửi lại tin nhắn.")
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
                    # Keep technical details in server logs only; show users a concise message.
                    # Preserve the current formula if the request fails.
                    logging.exception("Thu Vu chat request failed")
                    st.error("Không thể xử lý cuộc trò chuyện: Gemini đang bận hoặc kết nối bị gián đoạn. Vui lòng thử lại sau 20–60 giây; công thức hiện tại vẫn được giữ nguyên.")

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
                max_value=10.0, step=0.01,
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
