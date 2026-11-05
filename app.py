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
from PIL import Image

st.set_page_config(page_title="Inspection", layout="wide")

LOGO_PATH = "logo.png"
ADMIN_PW = "1234"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxYbt4TLqHrim_3ZPRBQ2Xq0cDF2LPZDXH5p3ZxfGo3VM1MRWbdVV717Ie1Zx6BOgz6/exec"

KST = timezone(timedelta(hours=9))

def get_kst_now():
    actual_kst = datetime.now(timezone.utc) + timedelta(hours=9)
    target_min = datetime(2026, 11, 2, 0, 0, 0, tzinfo=KST)
    if actual_kst < target_min:
        return target_min
    return actual_kst

def format_date_str(val):
    if not val or str(val).strip().lower() in ["nan", "nat", "", "-", "null"]:
        return "-"
        
    v_str = str(val).strip()
    
    try:
        iso_str = v_str.replace("Z", "+00:00")
        parsed_dt = datetime.fromisoformat(iso_str)

        if parsed_dt.tzinfo is not None:
            parsed_dt = parsed_dt.astimezone(KST)

        return parsed_dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    if len(v_str) >= 10:
        cleaned = v_str[:10].replace("/", "-").replace(".","-")
        try:
            return datetime.strptime(cleaned, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
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
    
    if len(v_str) >= 10:
        try:
            cleaned = v_str[:10].replace("/", "-").replace(".", "-")
            return datetime.strptime(cleaned, "%Y-%m-%d").date()
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
                data = data[1:]
                normalized_rows = []
                for item in data:
                    if isinstance(item, list):
                        vals = [str(v).strip() for v in item]
                        while len(vals) < 9:
                            vals.append("-")
                        in_d, d_d, m_no, p_name, f_n, nail_v, tape_v, j_v, rem_v = vals[:9]
                        
                        if not f_n or f_n.lower() in ["nan", "nat", "", "none", ".none"]:
                            f_n = "none"
                            
                        if not j_v or j_v == "-":
                            j_v = "🟢 최종 적합 (PASS)" if ("적합" in nail_v and "적합" in tape_v) else "🟡 판정 대기"
                        normalized_rows.append({
                            "입고일자": format_date_str(in_d), "검사일자": format_date_str(d_d), "포장재번호": m_no, "포장재약호": p_name,
                            "사진파일명": f_n, "손톱박리": nail_v, "테이프박리": tape_v, "최종판정": j_v, "특이사항": rem_v
                        })
                    elif isinstance(item, dict):
                        f_n = str(item.get("사진파일명", item.get("사진 파일명", "none"))).strip()
                        if not f_n or f_n.lower() in ["nan", "nat", "", "none", ".none"]:
                            f_n = "none"
                            
                        normalized_rows.append({
                            "입고일자": format_date_str(str(item.get("입고일자", item.get("입고 일자", "-"))).strip()),
                            "검사일자": format_date_str(str(item.get("검사일자", item.get("검사 일자", "-"))).strip()),
                            "포장재번호": str(item.get("포장재번호", item.get("포장재 번호", "-"))).strip(),
                            "포장재약호": str(item.get("포장재약호", item.get("포장재 약호", "-"))).strip(),
                            "사진파일명": f_n,
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
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        
        if image.width > 500:
            ratio = 500 / image.width
            new_height = int(image.height * ratio)
            image = image.resize((500, new_height), Image.Resampling.LANCZOS)
        
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=60)
        b64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        print(f"Image compression error: {e}")
        try:
            uploaded_file.seek(0)
            bytes_data = uploaded_file.getvalue()
            b64_str = base64.b64encode(bytes_data).decode('utf-8')
            mime = uploaded_file.type if uploaded_file.type else "image/jpeg"
            return f"data:{mime};base64,{b64_str}"
        except Exception as err:
            print(f"Fallback error: {err}")
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
        clean_mat = str(old_mat).strip()
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
        st.image(LOGO_PATH, use_column_width=600)

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
            elif "판정 대기" in selected_single_filter:  # 💡 "대기" 단독 매칭 대신 "판정 대기" 정확히 매칭하도록 수정
                df_f = df_f[df_f["최종판정"].str.contains("판정 대기", case=False, na=False)].reset_index(drop=True)

        try:
            df_f["_temp_date"] = pd.to_datetime(df_f["입고일자"], errors='coerce')
            df_f = df_f.sort_values(by="_temp_date", ascending=True).drop(columns=["_temp_date"]).reset_index(drop=True)
            df_f = df_f.iloc[::-1].reset_index(drop=True)
        except Exception:
            pass

        def get_badge(val):
            v_str = str(val).strip()
            if "부적합" in v_str or "FAIL" in v_str:
                return '<span style="background-color:#fce8e6; color:#c5221f; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif;">🔴 부적합 (FAIL)</span>'
            elif "적합" in v_str or "PASS" in v_str:
                return '<span style="background-color:#e6f4ea; color:#137333; padding:2px 5px; border-radius:10px; font-size:9.5px; white-space:nowrap; display:inline-block; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif;">🟢 적합 (PASS)</span>'
            elif "시험 대기" in v_str or "사양 확인" in v_str:
                return '<span style="background-color:#fef7e0; color:#b06000; padding:2px 4px; border-radius:8px; font-size:8.5px; white-space:nowrap; display:inline-block; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif;">🟡 시험대기(사양확인)</span>'
            else:
                return f'<span style="white-space:nowrap; font-size:11px; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif;">{html.escape(val)}</span>'

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
            
            if img_val and img_val.lower() not in ["none", "nat", "nan", "", "-", ".none"]:
                modal_id = f"modal_{idx}"
                img_td = f'<a href="javascript:void(0);" onclick="document.getElementById(\'{modal_id}\').style.display=\'flex\';" style="text-decoration:none; font-size:16px; cursor:pointer;" title="사진 보기">🔍</a>'
                
                if img_val.startswith("data:image"):
                    modal_content = f"""
                    <div style="background:#f8f9fa; border-radius:6px; padding:4px; margin-bottom:10px; max-height:280px; overflow-y:auto; text-align:center; border:1px solid #e1e4e8;">
                        <img src="{img_val}" style="max-width:100%; height:auto; border-radius:4px; display:inline-block;" />
                    </div>
                    """
                elif "http" in img_val:
                    modal_content = f"""
                    <div style="background:#f8f9fa; border-radius:6px; padding:4px; margin-bottom:10px; max-height:280px; overflow-y:auto; text-align:center; border:1px solid #e1e4e8;">
                        <img src="{img_val}" style="max-width:100%; height:auto; border-radius:4px; display:inline-block;" />
                    </div>
                    """
                else:
                    modal_content = f"""
                    <div style="background:#f8f9fa; border-radius:6px; padding:10px; margin-bottom:10px; font-size:12px; color:#555; text-align:center;">
                        📁 <b>저장된 파일 정보:</b><br>
                        <code style="font-size:10px; color:#0366d6;">{html.escape(img_val)}</code>
                    </div>
                    """

                modal_html = f"""
                <div id="{modal_id}" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; z-index:9999999; justify-content:center; align-items:center; background:transparent;">
                    <div style="background:white; padding:15px; border-radius:10px; width:320px; max-width:90%; box-shadow:0 10px 25px rgba(0,0,0,0.4); border:1px solid #d0d7de; position:relative; text-align:center; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:6px;">
                            <h3 style="margin:0; font-size:13.5px; color:#222; font-weight:bold;">🔍 검사 사진 크게 보기</h3>
                            <a href="javascript:void(0);" onclick="document.getElementById(\'{modal_id}\').style.display=\'none\';" style="text-decoration:none; font-size:18px; color:#666; font-weight:bold; cursor:pointer; line-height:1; padding:0 2px;">&times;</a>
                        </div>
                        <div style="text-align:left; font-size:11px; color:#444; margin-bottom:8px; line-height:1.3; background:#f8f9fa; padding:6px 8px; border-radius:5px; border:1px solid #e1e4e8;">
                            📦 <b>포장재 번호:</b> {m_val}<br>
                            🏷️ <b>포장재 약호:</b> {p_val}<br>
                            📅 <b>검사 일자:</b> {d_val}
                        </div>
                        {modal_content}
                        <button onclick="document.getElementById(\'{modal_id}\').style.display=\'none\';" style="background-color:#ff4b4b; color:white; border:none; padding:6px 12px; border-radius:5px; font-weight:bold; font-size:12px; width:100%; cursor:pointer;">닫기</button>
                    </div>
                </div>
                """
                modals_list.append(modal_html)

            row_str = f"""
<tr>
    <td style="padding:8px 8px; width:85px; white-space:nowrap; font-size:11.5px; color:#333; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">{in_val}</td>
    <td style="padding:8px 8px; width:85px; white-space:nowrap; font-size:11.5px; color:#333; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">{d_val}</td>
    <td style="padding:8px 8px; width:95px; white-space:nowrap; font-size:11.5px; color:#333; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">{m_val}</td>
    <td style="padding:8px 10px; width:220px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-size:11.5px; color:#333; text-align:left; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-weight:500;">{p_val}</td>
    <td style="padding:8px 6px; width:40px; text-align:center; white-space:nowrap; font-size:11.5px; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">{img_td}</td>
    <td style="padding:8px 6px; width:100px; white-space:nowrap; font-size:11.5px; color:#555; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">{n_val}</td>
    <td style="padding:8px 6px; width:100px; white-space:nowrap; font-size:11.5px; color:#555; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">{t_val}</td>
    <td style="padding:8px 6px; width:120px; white-space:nowrap; font-size:11.5px; color:#555; text-align:center; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">{j_val}</td>
    <td style="padding:8px 10px; min-width:130px; font-size:11.5px; color:#555; text-align:left; vertical-align:middle; border-bottom:1px solid #e0e0e0; border-right:1px solid #e0e0e0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">{r_val}</td>
</tr>"""
            rows_list.append(row_str)

        all_rows = "\n".join(rows_list)
        all_modals = "\n".join(modals_list)
        
        calc_iframe_height = min(max(400, len(df_f) * 45 + 120), 800)

        table_code = f"""
<div style="overflow-x:auto; background-color:#ffffff;">
    <table style="width:100%; min-width:970px; table-layout:auto; border-collapse:collapse; margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
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
{all_modals}
"""

        st.components.v1.html(table_code, height=calc_iframe_height, scrolling=True)

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
                        
                        raw_in_date = curr_row["입고일자"] if "입고일자" in curr_row else curr_row.get(0, kst_today)
                        default_in_date = parse_date_safely(raw_in_date, kst_today)
                        edit_in_date_val = st.date_input("포장재 입고 일자 수정", value=default_in_date, key=f"edit_in_{sel_idx}")
                        edit_in_date_str = edit_in_date_val.isoformat()
                        
                        raw_inspect_date = curr_row["검사일자"] if "검사일자" in curr_row else curr_row.get(1, kst_today)
                        default_inspect_date = parse_date_safely(raw_inspect_date, kst_today)
                        edit_inspect_date_val = st.date_input("검사 일자 수정", value=default_inspect_date, key=f"edit_insp_{sel_idx}")
                        edit_inspect_date_str = edit_inspect_date_val.isoformat()
                        
                        edit_mat_no = st.text_input("포장재 번호 수정", value=edit_mat_no_val, key=f"edit_mat_{sel_idx}")
                        edit_pack_name = st.text_input("포장재 약호 수정", value=str(curr_row.get("포장재약호", "")), key=f"edit_pack_{sel_idx}")
                        
                        nail_opts = ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)", "🟡 시험 대기 (사양 확인 중)"]
                        curr_nail = str(curr_row.get("손톱박리", ""))
                        nail_default = nail_opts.index(curr_nail) if curr_nail in nail_opts else 0
                        edit_nail = st.selectbox("손톱 박리 결과 수정", nail_opts, index=nail_default, key=f"edit_nail_{sel_idx}")
                        
                        tape_opts = ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)", "🟡 시험 대기 (사양 확인 중)"]
                        curr_tape = str(curr_row.get("테이프박리", ""))
                        tape_default = tape_opts.index(curr_tape) if curr_tape in tape_opts else 0
                        edit_tape = st.selectbox("테이프 박리 결과 수정", tape_opts, index=tape_default, key=f"edit_tape_{sel_idx}")
                        
                        judg_opts = ["🟢 최종 적합 (PASS)", "🔴 최종 부적합 (FAIL)", "🟠 조건부 진행 (특이사항 확인)", "🟡 판정 대기"]
                        curr_judg = str(curr_row.get("최종판정", ""))
                        judg_default = judg_opts.index(curr_judg) if curr_judg in judg_opts else 0
                        edit_judg = st.selectbox("최종 판정 수정", judg_opts, index=judg_default, key=f"edit_judg_{sel_idx}")
                        
                        edit_file = st.file_uploader(f"새로운 사진 교체 (선택사항 - 현재 포장재 번호: {edit_mat_no_val})", type=["jpg", "jpeg", "png"], key=f"uploader_{sel_idx}")
                        
                        edit_rem = st.text_area("특이사항 수정", value=str(curr_row.get("특이사항", "-")), key=f"edit_rem_{sel_idx}")
                        
                        update_btn = st.button("🔄 수정 내용 반영하기", type="primary", key=f"update_btn_{sel_idx}")
                        
                        if update_btn:
                            if edit_file is not None:
                                new_url = process_image_to_base64(edit_file)
                            else:
                                existing_img = str(curr_row.get("사진파일명", "none")).strip()
                                if not existing_img or existing_img.lower() in ["nan", "nat", "none", "", "-", ".none", "null"]:
                                    new_url = "none"
                                else:
                                    new_url = existing_img
                            
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
    "Author : 메이크업공정혁신팀 김태현 책임기사<br>Version : v1.11.49 (Filter Exact Match Fix)" \
    "</div>", 
    unsafe_allow_html=True
)
