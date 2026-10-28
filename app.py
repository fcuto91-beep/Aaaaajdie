import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile

st.set_page_config(page_title="Inspection", layout="centered")
st.title("📦🧴 포장재 착인 검사 이력 관리")

F = "inspection_history.csv"
D = "inspection_images"

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))
st.info(f"⏰ 일자: **{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}**")

with st.form("f1", clear_on_submit=True):
    st.subheader("📝 시험 결과 입력")
    mat_no = st.text_input("포장재 번호")
    pack_name = st.text_input("포장재 약호")
    nail = st.selectbox("손톱 박리 결과", ["적합", "부적합"])
    tape = st.selectbox("테이프 박리 결과", ["적합", "부적합"])
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

        # 💡 HTML 표 기반 렌더링 (전체 가운데 정렬 및 최적화된 칸 너비)
        rows_list = []
        for idx, row in df_f.iterrows():
            raw_d = str(row.get("검사일시", "-"))
            d_val = raw_d[:10] if len(raw_d) >= 10 else raw_d
            m_val = str(row.get("포장재번호", "-"))
            p_val = str(row.get("포장재약호", "-")) if pd.notna(row.get("포장재약호")) else "-"
            n_val = str(row.get("손톱박리", "-"))
            t_val = str(row.get("테이프박리", "-"))
            r_val = str(row.get("특이사항", "-")) if pd.notna(row.get("특이사항")) else "-"
            
            fname = str(row.get("사진파일명", "none"))
            if fname != "none":
                ip = os.path.join(D, fname)
                if os.path.exists(ip):
                    img_td = f'<a href="?pop_idx={idx}" target="_self" style="text-decoration:none; font-size:16px;">🔍</a>'
                else:
                    img_td = '-'
            else:
                img_td = '-'

            row_str = f'''<tr>
                <td style="padding:8px 4px; width:82px; white-space:nowrap; font-size:11px; color:#333; text-align:center; vertical-align:middle;">{d_val}</td>
                <td style="padding:8px 6px; white-space:nowrap; font-weight:bold; font-size:12px; text-align:center; vertical-align:middle;">{m_val}</td>
                <td style="padding:8px 6px; white-space:nowrap; font-size:12px; color:#555; text-align:center; vertical-align:middle;">{p_val}</td>
                <td style="padding:8px 6px; white-space:nowrap; font-size:12px; text-align:center; vertical-align:middle;">{n_val}</td>
                <td style="padding:8px 6px; white-space:nowrap; font-size:12px; text-align:center; vertical-align:middle;">{t_val}</td>
                <td style="padding:8px 6px; text-align:center; width:70px; white-space:nowrap; vertical-align:middle;">{img_td}</td>
                <td style="padding:8px 6px; min-width:90px; font-size:12px; color:#555; text-align:center; vertical-align:middle;">{r_val}</td>
            </tr>'''
            rows_list.append(row_str)

        all_rows = "".join(rows_list)

        table_code = f'''<div style="overflow-x:auto; max-height:400px; border:1px solid #ccc; border-radius:6px; background-color:#fff;">
            <table style="width:100%; border-collapse:collapse;">
                <thead style="position:sticky; top:0; background-color:#f0f2f6; border-bottom:2px solid #ddd; z-index:10;">
                    <tr>
                        <th style="padding:
