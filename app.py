import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile
import requests
import json
import html
import base64

st.set_page_config(page_title="Inspection", layout="wide")

D = "inspection_images"
LOGO_PATH = "logo.png"
ADMIN_PW = "1234"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbywD2brYz6Iory_KKDyh5pckjGqYvsf2ws1bY6EN6-NzGEslhyOF65Q9DKngsju5FWmlw/exec"

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))

def get_kst_now():
    actual_kst = datetime.now(timezone.utc) + timedelta(hours=9)
    target_min = datetime(2026, 10, 31, 0, 0, 0, tzinfo=KST)
    if actual_kst < target_min:
        return target_min
    return actual_kst

def format_date_str(val):
    if not val or str(val).lower() in ["nan", "nat", "none", "", "-"]:
        return "-"
    v_str = str(val).strip()
    
    months = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06", 
              "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
    
    try:
        parts = v_str.replace(",", "").split()
        m_num, d_num, y_num = None, None, "2026"
        for p in parts:
            if p in months:
                m_num = months[p]
            elif p.isdigit():
                if len(p) <= 2:
                    d_num = p.zfill(2)
                elif len(p) == 4:
                    y_num = p
        if m_num and d_num:
            return f"{y_num}-{m_num}-{d_num}"
    except:
        pass

    try:
        parsed_dt = pd.to_datetime(v_str, errors='coerce')
        if pd.notna(parsed_dt):
            return parsed_dt.strftime("%Y-%m-%d")
    except:
        pass
        
    return v_str[:10] if len(v_str) >= 10 else v_str

def load_data():
    try:
        no_cache_url = f"{APPS_SCRIPT_URL}?t={get_kst_now().timestamp()}"
        response = requests.get(no_cache_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                for col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                return df
    except Exception as e:
        print(f"Load error: {e}")
    
    return pd.DataFrame(columns=["입고일자", "검사일자", "포장재번호", "포장재약호", "사진파일명", "손톱박리", "테이프박리", "특이사항"])

def append_to_sheet(row_data):
    try:
        payload = {"action": "append", "row": row_data}
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Append error: {e}")
        return False

def update_sheet(old_mat, row_data):
    try:
        payload = {"action": "update", "mat_no": str(old_mat), "row": row_data}
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Update error: {e}")
        return False

def clear_sheet_data():
    try:
        payload = {"action": "clear_sheet"}
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Clear error: {e}")
        return False

@st.dialog("🎉 저장 완료")
def show_save_success_popup():
    st.success("검사 결과가 구글 시트에 실시간으로 안전하게 저장되었습니다!")
    if st.button("확인", type="primary", use_container_width=True):
        st.rerun()

@st.dialog("✏️ 수정 완료")
def show_edit_success_popup():
    st.success("검사 내역이 구글 시트에 성공적으로 수정 반영되었습니다!")
    if st.button("확인", type="primary", use_container_width=True):
        st.rerun()

# 💡 화면 진짜 정가운데에 웅장하게 뜨는 공식 다이얼로그 팝업
@st.dialog("🔍 검사 사진 크게 보기")
def show_image_dialog(m_val, p_val, d_val, image_path):
    st.markdown(f"""
        <div style="font-size:13px; color:#444; margin-bottom:10px; line-height:1.5;">
            📦 <b>포장재 번호:</b> {m_val}<br>
            🏷️ <b>포장재 약호:</b> {p_val}<br>
            📅 <b>검사 일자:</b> {d_val}
        </div>
    """, unsafe_allow_html=True)
    
    if os.path.exists(image_path):
        st.image(image_path, use_column_width=True)
    else:
        st.warning("⚠️ 저장된 이미지 파일이 존재하지 않습니다.")
    
    st.markdown("")
    if st.button("닫기", type="primary", use_container_width=True):
        st.rerun()

# UI 레이아웃
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_column_width=True)

st.markdown("")
st.markdown("<h1 style='text-align: center; font-size: 24px !important; font-weight: bold; margin-bottom: 10px; word-break: keep-all;'>📦🧴 포장재 착인 검사 이력 관리</h1>", unsafe_allow_html=True)

current_time_str = get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
st.info("⏰ 일자: **" + current_time_str + "**")

with st.form("f1", clear_on_submit=True):
    st.subheader("📝 시험 결과 입력")
    
    kst_today = get_kst_now().date()
    in_date_val = st.date_input("포장재 입고 일자", value=kst_today)
    in_date_str = in_date_val.isoformat()
    
    mat_no = st.text_input("포장재 번호", placeholder="예: 5115558")
    pack_name = st.text_input("포장재 약호", placeholder="예: ANA-TBMBM(F)E 용기(공용)")
    
    result_options = ["선택해주세요", "🟢 적합 (PASS)", "🔴 부적합 (FAIL)", "🟡 시험 대기 (사양 확인 중)"]
    
    nail = st.selectbox("손톱 박리 결과", result_options)
    tape = st.selectbox("테이프 박리 결과", result_options)
    
    up_file = st.file_uploader("검사 사진", type=["jpg", "jpeg", "png"])
    rem = st.text_area("특이사항")
    ok = st.form_submit_button("💾 Save", type="primary")

if ok:
    if not mat_no.strip():
        st.warning("⚠️ 포장재 번호를 입력해 주세요!")
    elif nail == "선택해주세요" or tape == "선택해주세요":
        st.warning("⚠️ 손톱 및 테이프 박리 결과를 선택해 주세요!")
    else:
        dt_str = get_kst_now().date().isoformat()
        fn = "none"
        if up_file:
            s_lot = "".join(c for c in mat_no if c.isalnum())
            t_str = get_kst_now().strftime("%Y%m%d_%H%M%S")
            fn = f"{s_lot}_{t_str}_{up_file.name}"
            file_path = os.path.join(D, fn)
            with open(file_path, "wb") as f:
                f.write(up_file.getbuffer())

        row_data = [
            in_date_str, 
            dt_str, 
            str(mat_no), 
            str(pack_name) if pack_name.strip() else "-", 
            fn,
            nail, 
            tape, 
            str(rem) if rem.strip() else "-"
        ]
        
        if append_to_sheet(row_data):
            st.session_state["show_saved_modal"] = True
            st.rerun()
        else:
            st.error("❌ 구글 시트 저장 중 오류가 발생했습니다.")

if st.session_state.get("show_saved_modal", False):
    st.session_state["show_saved_modal"] = False
    show_save_success_popup()

if st.session_state.get("show_edited_modal", False):
    st.session_state["show_edited_modal"] = False
    show_edit_success_popup()

st.markdown("---")
st.subheader("📋 전체 검사 내역")

try:
    df = load_data()
    
    if not df.empty:
        q = st.text_input("🔍 검색", placeholder="검색어 입력...")
        
        if q:
            mask = df.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)
            df_f = df[mask].reset_index(drop=True)
        else:
            df_f = df.reset_index(drop=True)

        def get_badge(val):
            v_str = str(val).strip()
            if "부적합" in v_str or "FAIL" in v_str:
                return '<span style="background-color:#fce8e6; color:#c5221f; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block;">🔴 부적합 (FAIL)</span>'
            elif "적합" in v_str or "PASS" in v_str:
                return '<span style="background-color:#e6f4ea; color:#137333; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block;">🟢 적합 (PASS)</span>'
            elif "시험 대
