import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile

st.set_page_config(page_title="Inspection System", layout="centered")
st.title("🛡️ 공정 검사 및 이력 관리")

F = "inspection_history.csv"
D = "inspection_images"

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))
st.info(f"⏰ 현재 검사 시각: **{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}**")

lot = st.text_input("자재 / LOT명 입력")

st.markdown("---")
st.subheader("📝 시험 항목별 결과 판정")

nail = st.selectbox("1️⃣ 손톱박리 검사 결과", ["적합", "부적합"])
tape = st.selectbox("2️⃣ 테이프 박리 검사 결과", ["적합", "부적합"])

st.markdown("---")
up_file = st.file_uploader("현장 사진 첨부", type=["jpg", "jpeg", "png"])

if up_file:
    st.image(up_file, caption="사진 미리보기", width=250)

rem = st.text_area("특이사항 및 조치 내용", placeholder="특이사항 입력")

if st.button("💾 Save Inspection", type="primary"):
    if not lot.strip():
        st.warning("⚠️ 자재 / LOT명을 입력해 주세요!")
    else:
        try:
            dt = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
            fn = "none"
            if up_file:
                s_lot = "".join(c for c in lot if c.isalnum() or c in ('_', '-'))
                fn = f"{s_lot}_{datetime.now(KST).strftime('%Y%m%d_%H%M%S')}_{up_file.name}"
                with open(os.path.join(D, fn), "wb") as f:
                    f.write(up_file.getbuffer())

            nd = pd.DataFrame([{
                "검사일시": dt,
                "자재/LOT명": lot,
                "손톱박리": nail,
                "테이프박리": tape,
                "사진파일명": fn,
                "특이사항": rem,
            }])

            if os.path.exists(F):
                try:
                    df_ex = pd.read_csv(F)
                    df_c = nd if df_ex.empty else pd.concat([df_ex, nd], ignore_index=True)
                except:
                    df_c = nd
            else:
                df_c = nd

            df_c.to_csv(F, index=False, encoding="utf-8-sig")
            st.success("✅ Saved successfully!")
            st.rerun()
        except Exception as e:
