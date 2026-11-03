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

LOGO_PATH = "logo.png"
ADMIN_PW = "1234"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwGhXKRINWEH0A1fn57SfcK-TsMtL1rjv22ZDMv2G3SMD8ayyFIZ58khBAINLS_qpf3bw/exec"

KST = timezone(timedelta(hours=9))

def get_kst_now():
    actual_kst = datetime.now(timezone.utc) + timedelta(hours=9)
    target_min = datetime(2026, 11, 2, 0, 0, 0, tzinfo=KST)
    if actual_kst < target_min:
        return target_min
    return actual_kst

def format_date_str(val):
    if not val or str(val).lower() in ["nan", "nat", "none", "", "-"]:
        return "-"
    v_str = str(val).strip()
    
    if v_str.isdigit() and len(v_str) >= 10:
        try:
            num_val = float(v_str)
            dt_obj = datetime.fromtimestamp(num_val / 1000.0 if len(v_str) >= 12 else num_val, tz=KST)
            return dt_obj.strftime("%Y-%m-%d")
        except:
            pass

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

def parse_date_safely(val, fallback_date):
    if not val or str(val).lower() in ["nan", "nat", "none", "", "-", "null"]:
        return fallback_date
    
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, type(fallback_date)):
        return val
        
    v_str = str(val).strip()
    
    months_map = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06", 
                  "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
    try:
        parts = v_str.replace(",", "").split()
        found_m, found_d, found_y = None, None, "2026"
        for p in parts:
            if p in months_map:
                found_m = months_map[p]
            elif p.isdigit():
                if len(p) == 2 and not found_d:
                    found_d = p
                elif len(p) == 4:
                    found_y = p
        if found_m and found_d:
            return datetime.strptime(f"{found_y}-{found_m}-{found_d}", "%Y-%m-%d").date()
    except:
        pass

    if v_str.isdigit() and len(v_str) >= 10:
        try:
            num_val = float(v_str)
            if len(v_str) >= 12:
                return datetime.fromtimestamp(num_val / 1000.0, tz=KST).date()
            else:
                return datetime.fromtimestamp(num_val, tz=KST).date()
        except:
            pass
            
    if 'T' in v_str:
        v_str = v_str.split('T')[0]
    elif ' ' in v_str and not ('GMT' in v_str or 'Standard' in v_str):
        v_str = v_str.split(' ')[0]
        
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(v_str[:10], fmt).date()
        except:
            continue
            
    try:
        parsed_dt = pd.to_datetime(v_str, errors='coerce')
        if pd.notna(parsed_dt):
            return parsed_dt.date()
    except:
        pass
        
    return fallback_date

def get_judgment_badge(val):
    v_str = str(val).strip()
    if "최종 적합" in v_str or "PASS" in v_str:
        return '<span style="background-color:#e6f4ea; color:#137333; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block;">🟢 최종적합(PASS)</span>'
    elif "최종 부적합" in v_str or "FAIL" in v_str:
        return '<span style="background-color:#fce8e6; color:#c5221f; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block;">🔴 최종부적합(FAIL)</span>'
    elif "조건부 진행" in v_str:
        return '<span style="background-color:#fef7e0; color:#b06000; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block;">🟠 조건부진행</span>'
    elif "대기" in v_str or "확인" in v_str:
        return '<span style="background-color:#fef7e0; color:#b06000; padding:2px 4px; border-radius:8px; font-size:8.5px; white-space:nowrap; display:inline-block;">🟡 판정대기</span>'
    else:
        return f'<span style="background-color:#fef7e0; color:#b06000; padding:2px 4px; border-radius:8px; font-size:8.5px; white-space:nowrap; display:inline-block;">🟡 {html.escape(v_str)}</span>'

@st.cache_data(ttl=60)
def load_data():
    try:
        no_cache_url = f"{APPS_SCRIPT_URL}?t={get_kst_now().timestamp()}"
        response = requests.get(no_cache_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                normalized_rows = []
                for item in data:
                    if isinstance(item, list):
                        vals = [str(v).strip() for v in item]
                        while len(vals) < 9:
                            vals.append("-")
                        in_d, d_d, m_no, p_name, f_n, nail_v, tape_v, j_v, rem_v = vals[:9]
                        if not j_v or j_v == "-":
                            j_v = "🟢 최종 적합 (PASS)" if ("적합" in nail_v and "적합" in tape_v) else "🟡 판정 대기"
                        normalized_rows.append({
                            "입고일자": in_d, "검사일자": d_d, "포장재번호": m_no, "포장재약호": p_name,
                            "사진파일명": f_n, "손톱박리": nail_v, "테이프박리": tape_v, "최종판정": j_v, "특이사항": rem_v
                        })
                    elif isinstance(item, dict):
                        normalized_rows.append({
                            "입고일자": str(item.get("입고일자", item.get("입고 일자", "-"))).strip(),
                            "검사일자": str(item.get("검사일자", item.get("검사 일자", "-"))).strip(),
                            "포장재번호": str(item.get("포장재번호", item.get("포장재 번호", "-"))).strip(),
                            "포장재약호": str(item.get("포장재약호", item.get("포장재 약호", "-"))).strip(),
                            "사진파일명": str(item.get("사진파일명", item.get("사진 파일명", "none"))).strip(),
                            "손톱박리": str(item.get("손톱박리", "-")).strip(),
                            "테이프박리": str(item.get("테이프박리", "-")).strip(),
                            "최종판정": str(item.get("최종판정", item.get("판정", "🟡 판정 대기"))).strip(),
                            "특이사항": str(item.get("특이사항", "-")).strip()
                        })
                return pd.DataFrame(normalized_rows)
    except Exception as e:
        print(f"Load error: {e}")
    
    return pd.DataFrame(columns=["입고일자", "검사일자", "포장재번호", "포장재약호", "사진파일명", "손톱박리", "테이프박리", "최종판정", "특이사항"])

def process_image_to_base64(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        b64_str = base64.b64encode(bytes_data).decode('utf-8')
        mime = uploaded_file.type if uploaded_file.type else "image/jpeg"
        return f"data:{mime};base64,{b64_str}"
    except Exception as e:
        print(f"Image processing error: {e}")
    return "none"

def append_to_sheet(row_data):
    try:
        payload = {"action": "append", "row": row_data}
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        st.cache_data.clear()
        return response.status_code == 200
    except Exception as e:
        print(f"Append error: {e}")
        return False

def update_sheet(old_mat, row_data):
    try:
        clean_mat = str(old_mat).strip().split('.')[0]
        payload = {"action": "update", "mat_no": clean_mat, "row": row_data}
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        st.cache_data.clear()
        return response.status_code == 200
    except Exception as e:
        print(f"Update error: {e}")
        return False

def clear_sheet_data():
    try:
        payload = {"action": "clear_sheet"}
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        st.cache_data.clear()
        return response.status_code == 200
    except Exception as e:
        print(f"Clear error: {e}")
        return False

@st.dialog("🎉 저장 완료")
def show_save_success_popup():
    st.success("검사 결과와 사진이 시트에 안전하게 영구 저장되었습니다!")
    if st.button("확인", type="primary", use_container_width=True):
        st.rerun()

@st.dialog("✏️ 수정 완료")
def show_edit_success_popup():
    st.success("검사 내역이 시트에 성공적으로 수정 반영되었습니다!")
    if st.button("확인", type="primary", use_container_width=True):
        st.rerun()

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
    
    judgment_options = ["🟢 최종 적합 (PASS)", "🔴 최종 부적합 (FAIL)", "🟠 조건부 진행 (특이사항 확인)", "🟡 판정 대기"]
    manual_judgment = st.selectbox("최종 판정 (협의 후 변경 가능)", judgment_options)
    
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
        img_data_str = "none"
        if up_file:
            img_data_str = process_image_to_base64(up_file)

        row_data = [
            in_date_str, 
            dt_str, 
            str(mat_no), 
            str(pack_name) if pack_name.strip() else "-", 
            img_data_str,
            nail, 
            tape, 
            manual_judgment,
            str(rem) if rem.strip() else "-"
        ]
        
        if append_to_sheet(row_data):
            st.session_state["show_saved_modal"] = True
            st.rerun()
        else:
            st.error("❌ 시트 저장 중 오류가 발생했습니다.")

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
        col_f1, col_f2 = st.columns([1.2, 1.8])
        with col_f1:
            q = st.text_input("🔍 검색", placeholder="검색어 입력...")
        with col_f2:
            filter_options = ["전체 보기", "🟢 최종 적합 (PASS)", "🔴 최종 부적합 (FAIL)", "🟠 조건부 진행 (특이사항 확인)", "🟡 판정 대기"]
            selected_single_filter = st.selectbox("🏷️ 최종 판정 (선택)", filter_options)
        
        if q:
            mask = df.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)
            df_f = df[mask].reset_index(drop=True)
        else:
            df_f = df.reset_index(drop=True)

        if selected_single_filter != "전체 보기":
            if "부적합" in selected_single_filter or "FAIL" in selected_single_filter:
                df_f = df_f[df_f["최종판정"].str.contains("부적합|FAIL", case=False, na=False)].reset_index(drop=True)
            elif "적합" in selected_single_filter or "PASS" in selected_single_filter:
                df_f = df_f[df_f["최종판정"].str.contains("적합|PASS", case=False, na=False)].reset_index(drop=True)
            elif "조건부" in selected_single_filter:
                df_f = df_f[df_f["최종판정"].str.contains("조건부", case=False, na=False)].reset_index(drop=True)
            elif "대기" in selected_single_filter:
                df_f = df_f[df_f["최종판정"].str.contains("대기|확인", case=False, na=False)].reset_index(drop=True)

        try:
            df_f["_temp_date"] = pd.to_datetime(df_f["입고일자"], errors='coerce')
            df_f = df_f.sort_values(by="_temp_date", ascending=True).drop(columns=["_temp_date"]).reset_index(drop=True)
            df_f = df_f.iloc[::-1].reset_index(drop=True)
        except Exception:
            pass

        def get_badge(val):
            v_str = str(val).strip()
            if "부적합" in v_str or "FAIL" in v_str:
                return '<span style="background-color:#fce8e6; color:#c5221f; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block;">🔴 부적합 (FAIL)</span>'
            elif "적합" in v_str or "PASS" in v_str:
                return '<span style="background-color:#e6f4ea; color:#137333; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block;">🟢 적합 (PASS)</span>'
            elif "시험 대기" in v_str or "사양 확인" in v_str:
                return '<span style="background-color:#fef7e0; color:#b06000; padding:2px 4px; border-radius:8px; font-size:8.5px; white-space:nowrap; display:inline-block;">🟡 시험대기(사양확인)</span>'
            else:
                return f'<span style="background-color:#fef7e0; color:#b06000; padding:2px 4px; border-radius:8px; font-size:8.5px; white-space:nowrap; display:inline-block;">🟡 {html.escape(v_str)}</span>'

        rows_list = []
        modals_list = []
        
        for idx, row in df_f.iterrows():
            in_val = format_date_str(row.get("입고일자", "-"))
            d_val = format_date_str(row.get("검사일자", "-"))

            m_val = html.escape(str(row.get("포장재번호", "-")))
            
            raw_p_name = str(row.get("포장재약호", "-"))
            if pd.isna(row.get("포장재약호")) or raw_p_name.lower() in ["nan", "none", ""]:
                raw_p_name = "-"
            p_val = html.escape(raw_p_name)
            
            n_val = get_badge(row.get("손톱박리", "-"))
            t_val = get_badge(row.get("테이프박리", "-"))
            
            final_j_raw = row.get("최종판정", "🟡 판정 대기")
            j_val = get_judgment_badge(final_j_raw)
            
            r_val = html.escape(str(row.get("특이사항", "-")) if pd.notna(row.get("특이사항")) else "-")
            
            img_val = str(row.get("사진파일명", "none")).strip()
            img_td = '-'
            
            if img_val and img_val.lower() not in ["none", "nat", "nan", "", "-"]:
                modal_id = f"modal_{idx}"
                img_td = f'<a href="javascript:void(0);" onclick="document.getElementById(\'{modal_id}\').style.display=\'flex\';" style="text-decoration:none; font-size:16px; cursor:pointer;" title="사진 보기">🔍</a>'
                
                if img_val.startswith("data:image") or "http" in img_val:
                    modal_img_html = f'<img src="{img_val}" style="max-width:100%; max-height:400px; height:auto; border-radius:6px; display:inline-block;" />'
                else:
                    modal_img_html = f'<div style="font-size:13px; color:#555; padding:20px;">📁 저장된 파일 정보:<br><code>{html.escape(img_val)}</code></div>'

                modal_html = f"""
<div id="{modal_id}" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:99999999; justify-content:center; align-items:center; background:rgba(0,0,0,0.6);">
    <div style="background:white; padding:24px; border-radius:14px; width:480px; max-width:90vw; box-shadow:0 25px 50px rgba(0,0,0,0.5); border:1px solid #d0d7de; text-align:center; position:relative;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid #eee; padding-bottom:8px;">
            <h3 style="margin:0; font-size:16px; color:#111; font-weight:bold;">🔍 검사 사진 크게 보기</h3>
            <a href="javascript:void(0);" onclick="document.getElementById('{modal_id}').style.display='none';" style="text-decoration:none; font-size:24px; color:#666; font-weight:bold; cursor:pointer; line-height:1; padding:0 4px;">&times;</a>
        </div>
        <div style="text-align:left; font-size:12.5px; color:#333; margin-bottom:12px; line-height:1.5; background:#f6f8fa; padding:10px 12px; border-radius:8px; border:1px solid #e1e4e8;">
            📦 <b>포장재 번호:</b> {m_val}<br>
            🏷️ <b>포장재 약호:</b> {p_val}<br>
            📅 <b>검사 일자:</b> {d_val}
        </div>
        <div style="background:#f8f9fa; border-radius:8px; padding:6px; margin-bottom:14px; max-height:400px; overflow-y:auto; text-align:center; border:1px solid #e1e4e8;">
            {modal_img_html}
        </div>
        <button onclick="document.getElementById('{modal_id}').style.display='none';" style="background-color:#ff4b4b; color:white; border:none; padding:10px 16px; border-radius:8px; font-weight:bold; font-size:13.5px; width:100%; cursor:pointer;">닫기</button>
    </div>
</div>
"""
                modals_list.append(modal_html)

            row_str = f"""<tr>
    <td style="padding:8px 8px; width:85px; white-space:nowrap; font-size:11.5px; color:#333; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{in_val}</td>
    <td style="padding:8px 8px; width:85px; white-space:nowrap; font-size:11.5px; color:#333; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{d_val}</td>
    <td style="padding:8px 8px; width:95px; white-space:nowrap; font-size:11.5px; color:#333; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{m_val}</td>
    <td style="padding:8px 10px; width:220px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-size:11.5px; color:#555; text-align:left; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{p_val}</td>
    <td style="padding:8px 6px; width:40px; text-align:center; white-space:nowrap; font-size:11.5px; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{img_td}</td>
    <td style="padding:8px 6px; width:100px; white-space:nowrap; font-size:11.5px; color:#555; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{n_val}</td>
    <td style="padding:8px 6px; width:100px; white-space:nowrap; font-size:11.5px; color:#555; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{t_val}</td>
    <td style="padding:8px 6px; width:120px; white-space:nowrap; font-size:11.5px; color:#555; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{j_val}</td>
    <td style="padding:8px 10px; min-width:130px; font-size:11.5px; color:#555; text-align:left; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0;">{r_val}</td>
</tr>"""
            rows_list.append(row_str)

        all_rows = "\n".join(rows_list)
        all_modals = "\n".join(modals_list)
        
        # 💡 들여쓰기 없이 맨 앞으로 바짝 붙여서 마크다운 코드 블록 버그 원천 차단
        table_code = f"""<div style="overflow-x:auto; max-height:480px; border:1px solid #d0d7de; border-radius:8px; background-color:#ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
    <table style="width:100%; min-width:970px; table-layout:auto; border-collapse:collapse; margin:0;">
        <thead style="position:sticky; top:0; background-color:#f6f8fa; border-bottom:2px solid #d0d7de; z-index:10;">
            <tr>
                <th style="padding:10px 8px; width:85px; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; text-align:center; border-right:1px solid #e0e0e0;">입고 일자</th>
                <th style="padding:10px 8px; width:85px; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; text-align:center; border-right:1px solid #e0e0e0;">검사 일자</th>
                <th style="padding:10px 8px; width:95px; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; text-align:center; border-right:1px solid #e0e0e0;">포장재 번호</th>
                <th style="padding:10px 10px; width:220px; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; text-align:center; border-right:1px solid #e0e0e0;">포장재 약호</th>
                <th style="padding:10px 6px; width:40px; text-align:center; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; border-right:1px solid #e0e0e0;">보기</th>
                <th style="padding:10px 6px; width:100px; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; text-align:center; border-right:1px solid #e0e0e0;">손톱</th>
                <th style="padding:10px 6px; width:100px; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; text-align:center; border-right:1px solid #e0e0e0;">테이프</th>
                <th style="padding:10px 6px; width:120px; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; text-align:center; border-right:1px solid #e0e0e0;">최종 판정</th>
                <th style="padding:10px 10px; min-width:130px; white-space:nowrap; font-size:12px; font-weight:600; color:#24292f; text-align:center; border-right:1px solid #e0e0e0;">특이사항</th>
            </tr>
        </thead>
        <tbody>
{all_rows}
        </tbody>
    </table>
</div>
{all_modals}"""

        st.markdown(table_code, unsafe_allow_html=True)

        st.markdown("---")
        with st.expander("🔐 관리자 메뉴 (백업 다운로드 / 수정 / 초기화)"):
            admin_input = st.text_input("관리자 비밀번호를 입력하세요", type="password")
            
            if admin_input == ADMIN_PW:
                st.success("✅ 관리자 인증이 완료되었습니다.")
                
                zb = io.BytesIO()
                with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as zf:
                    export_df = df.copy()
                    if "입고일자" in export_df.columns:
                        export_df["입고일자"] = export_df["입고일자"].apply(format_date_str)
                    if "검사일자" in export_df.columns:
                        export_df["검사일자"] = export_df["검사일자"].apply(format_date_str)

                    csv_bytes = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                    zf.writestr("inspection_history.csv", csv_bytes)
                zb.seek(0)
                
                backup_filename = f"backup_{get_kst_now().strftime('%Y%m%d')}.zip"
                st.download_button("💾 전체 검사 내역 백업 다운로드", data=zb, file_name=backup_filename, mime="application/zip", type="primary", use_container_width=True)
                
                st.markdown("---")
                st.subheader("✏️ 검사 내역 수정")
                edit_q = st.text_input("🔎 수정할 항목 검색 (포장재 번호)", placeholder="예: 5115558")
                
                if edit_q:
                    mask_edit = df.apply(lambda r: r.astype(str).str.contains(edit_q, case=False).any(), axis=1)
                    filtered_df = df[mask_edit]
                else:
                    filtered_df = df
                
                if not filtered_df.empty:
                    target_options = [f"[{i}] 번호: {row.get('포장재번호','')} | 약호: {row.get('포장재약호','')}" for i, row in filtered_df.iterrows()]
                    selected_target_str = st.selectbox("수정할 검사 내역 선택", target_options)
                    
                    if selected_target_str:
                        sel_idx = int(selected_target_str.split("]")[0].replace("[", ""))
                        curr_row = df.loc[sel_idx]
                        
                        edit_mat_no_val = str(curr_row.get("포장재번호", ""))
                        edit_file = st.file_uploader(f"새로운 사진 교체 (선택사항 - 현재 포장재 번호: {edit_mat_no_val})", type=["jpg", "jpeg", "png"], key=f"uploader_{sel_idx}")
                        
                        with st.form(f"edit_form_{sel_idx}"):
                            raw_in_date = curr_row["입고일자"] if "입고일자" in curr_row else curr_row.get(0, kst_today)
                            default_in_date = parse_date_safely(raw_in_date, kst_today)
                            edit_in_date_val = st.date_input("포장재 입고 일자 수정", value=default_in_date)
                            edit_in_date_str = edit_in_date_val.isoformat()
                            
                            raw_inspect_date = curr_row["검사일자"] if "검사일자" in curr_row else curr_row.get(1, kst_today)
                            default_inspect_date = parse_date_safely(raw_inspect_date, kst_today)
                            edit_inspect_date_val = st.date_input("검사 일자 수정", value=default_inspect_date)
                            edit_inspect_date_str = edit_inspect_date_val.isoformat()
                            
                            edit_mat_no = st.text_input("포장재 번호 수정", value=edit_mat_no_val)
                            edit_pack_name = st.text_input("포장재 약호 수정", value=str(curr_row.get("포장재약호", "")))
                            
                            nail_opts = ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)", "🟡 시험 대기 (사양 확인 중)"]
                            curr_nail = str(curr_row.get("손톱박리", ""))
                            nail_default = nail_opts.index(curr_nail) if curr_nail in nail_opts else 0
                            edit_nail = st.selectbox("손톱 박리 결과 수정", nail_opts, index=nail_default)
                            
                            tape_opts = ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)", "🟡 시험 대기 (사양 확인 중)"]
                            curr_tape = str(curr_row.get("테이프박리", ""))
                            tape_default = tape_opts.index(curr_tape) if curr_tape in tape_opts else 0
                            edit_tape = st.selectbox("테이프 박리 결과 수정", tape_opts, index=tape_default)
                            
                            judg_opts = ["🟢 최종 적합 (PASS)", "🔴 최종 부적합 (FAIL)", "🟠 조건부 진행 (특이사항 확인)", "🟡 판정 대기"]
                            curr_judg = str(curr_row.get("최종판정", ""))
                            judg_default = judg_opts.index(curr_judg) if curr_judg in judg_opts else 0
                            edit_judg = st.selectbox("최종 판정 수정", judg_opts, index=judg_default)
                            
                            edit_rem = st.text_area("특이사항 수정", value=str(curr_row.get("특이사항", "-")))
                            
                            update_btn = st.form_submit_button("🔄 수정 내용 반영하기", type="primary")
                            
                            if update_btn:
                                if edit_file is not None and getattr(edit_file, "size", 0) > 0:
                                    new_url = process_image_to_base64(edit_file)
                                else:
                                    new_url = str(curr_row.get("사진파일명", "none"))
                                
                                updated_row_data = [
                                    edit_in_date_str,
                                    edit_inspect_date_str,
                                    str(edit_mat_no),
                                    str(edit_pack_name) if edit_pack_name.strip() else "-",
                                    new_url,
                                    edit_nail,
                                    edit_tape,
                                    edit_judg,
                                    str(edit_rem) if edit_rem.strip() else "-"
                                ]
                                
                                if update_sheet(curr_row.get("포장재번호"), updated_row_data):
                                    st.session_state["show_edited_modal"] = True
                                    st.rerun()
                                else:
                                    st.error("❌ 수정 중 오류가 발생했습니다.")
                else:
                    st.info("검색 결과가 없습니다.")

                st.markdown("---")
                if st.button("🗑️ 사진 폴더 비우기", use_container_width=True):
                    if os.path.exists(D):
                        for f_name in os.listdir(D):
                            f_path = os.path.join(D, f_name)
                            if os.path.isfile(f_path):
                                os.remove(f_path)
                    st.success("사진 폴더가 초기화되었습니다!")
                    st.rerun()

                st.markdown("---")
                st.markdown("""
                    <style>
                    div.stButton > button {
                        border-color: #ff4b4b;
                    }
                    div.stButton > button:hover {
                        border-color: #ff2121;
                        color: #ff2121;
                    }
                    </style>
                """, unsafe_allow_html=True)

                if st.button("🚨 전체 데이터 초기화", use_container_width=True):
                    if clear_sheet_data():
                        st.success("모든 검사 이력이 초기화되었습니다!")
                        st.rerun()
                    else:
                        st.error("❌ 초기화 중 오류가 발생했습니다.")

            elif admin_input:
                st.error("❌ 비밀번호가 틀렸습니다.")
    else:
        st.info("저장된 검사 이력이 없습니다.")
except Exception as e:
    st.error(f"오류 발생: {e}")

st.markdown("---")
st.markdown(
    "<div style='text-align: right; color: #888; font-size: 12px; line-height: 1.4;'>" \
    "Author : 메이크업공정혁신팀 김태현 책임기사<br>Version : v1.11.50 (True Fullscreen Modal & Clean Table Fix)" \
    "</div>", 
    unsafe_allow_html=True
)
