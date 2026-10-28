import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile

st.set_page_config(page_title="Inspection", layout="centered")

F = "inspection_history.csv"
D = "inspection_images"
LOGO_PATH = "logo.png"
ADMIN_PW = "1234"  # 💡 관리자 비밀번호

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))

# 💡 1단계: 맨 윗줄 우측 구석에 CI 로고 배치
col_empty, col_logo = st.columns([3, 1.5])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=160)

# 💡 2단계: 그 아랫줄에 온전한 제목 배치
st.markdown("### 📦🧴 포장재 착인 검사 이력 관리")

st.info(f"⏰ 일자: **{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}**")

with st.form("f1", clear_on_submit=True):
    st.subheader("📝 시험 결과 입력")
    mat_no = st.text_input("포장재 번호")
    pack_name = st.text_input("포장재 약호")
    nail = st.selectbox("손톱 박리 결과", ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)"])
    tape = st.selectbox("테이프 박리 결과", ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)"])
    up_file = st.file_uploader("검사 사진", type=["jpg", "jpeg", "png"])
    rem = st.text_area("특이사항")
    ok = st.form_submit_button("💾 Save", type="primary")

if ok:
    if not mat_no.strip():
        st.warning("⚠️ 포장재 번호를 입력해 주세요!")
    else:
        dt_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        fn = "none"
        if up_file:
            s_lot = "".join(c for c in mat_no if c.isalnum())
            t_str = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
            fn = f"{s_lot}_{t_str}_{up_file.name}"
            file_path = os.path.join(D, fn)
            with open(file_path, "wb") as f:
                f.write(up_file.getbuffer())

        nd = pd.DataFrame([{
            "검사일시": dt_str,
            "포장재번호": mat_no,
            "포장재약호": pack_name if pack_name.strip() else "-",
            "손톱박리": nail,
            "테이프박리": tape,
            "사진파일명": fn,
            "특이사항": rem,
        }])

        df_c = nd
        if os.path.exists(F):
            try:
                df_ex = pd.read_csv(F)
                if not df_ex.empty:
                    df_c = pd.concat([df_ex, nd], ignore_index=True)
            except:
                pass

        df_c.to_csv(F, index=False, encoding="utf-8-sig")
        st.success("✅ Saved!")
        st.rerun()

# 💡 사진 팝업 모달 함수
@st.dialog("📸 사진 미리보기")
def show_image_popup(img_path, m_name, p_name, date_str):
    st.markdown(f"📦 **포장재 번호: {m_name}**")
    st.markdown(f"🏷️ **포장재 약호: {p_name}**")
    st.caption(f"📅 검사 일자: {date_str[:10] if len(date_str) >= 10 else date_str}")
    st.image(img_path, use_column_width=True)

st.markdown("---")
st.subheader("📋 전체 검사 내역")

if os.path.exists(F):
    try:
        df = pd.read_csv(F)
        q = st.text_input("🔍 검색", placeholder="검색어 입력...")
        df_f = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False).any(), axis=1)].reset_index(drop=True) if q else df.reset_index(drop=True)

        # 💡 URL 쿼리를 통한 팝업 모달 호출 연동
        if "pop_idx" in st.query_params:
            try:
                p_idx = int(st.query_params["pop_idx"])
                if 0 <= p_idx < len(df_f):
                    p_row = df_f.iloc[p_idx]
                    p_fname = str(p_row.get("사진파일명", "none"))
                    if p_fname != "none":
                        p_ip = os.path.join(D, p_fname)
                        if os.path.exists(p_ip):
                            raw_dt = str(p_row.get("검사일시", "-"))
                            show_image_popup(
                                p_ip, 
                                str(p_row.get("포장재번호", "-")), 
                                str(p_row.get("포장재약호", "-")), 
                                raw_dt
                            )
                st.query_params.clear()
            except:
                st.query_params.clear()

        # 💡 결과에 따라 이쁜 색상 배지를 입혀주는 함수
        def get_badge(val):
            v_str = str(val).strip()
            if "적합" in v_str or "PASS" in
