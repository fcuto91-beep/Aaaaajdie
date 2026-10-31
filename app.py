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

# 💡 브라우저 화면 정가운데에 완벽하게 뜨는 공식 이미지 상세보기 다이얼로그
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
            elif "시험 대기" in v_str or "사양 확인" in v_str:
                return '<span style="background-color:#fef7e0; color:#b06000; padding:2px 4px; border-radius:10px; font-size:9px; white-space:nowrap; display:inline-block;">🟡 시험대기 (사양확인)</span>'
            else:
                return f'<span style="white-space:nowrap; font-size:11px;">{html.escape(val)}</span>'

        # 스트림릿 네이티브 방식으로 각 행의 돋보기 버튼을 처리하기 위한 반복문
        for idx, row in df_f.iterrows():
            in_val = format_date_str(row.get("입고일자", "-"))
            d_val = format_date_str(row.get("검사일자", "-"))
            m_val = str(row.get("포장재번호", "-"))
            
            raw_p_name = str(row.get("포장재약호", "-"))
            if pd.isna(row.get("포장재약호")) or raw_p_name.lower() in ["nan", "none", ""]:
                raw_p_name = "-"
            p_val = raw_p_name
            
            n_val_html = get_badge(row.get("손톱박리", "-"))
            t_val_html = get_badge(row.get("테이프박리", "-"))
            r_val = str(row.get("특이사항", "-")) if pd.notna(row.get("특이사항")) else "-"
            
            fname = str(row.get("사진파일명", "none"))
            
            # 테이블의 각 행을 보기 좋게 출력
            c_in, c_d, c_m, c_p, c_img, c_n, c_t, c_r = st.columns([0.8, 0.8, 0.9, 2.2, 0.4, 0.9, 0.9, 1.8])
            with c_in:
                st.markdown(f"<div style='font-size:11.5px; text-align:center; padding-top:6px;'>{in_val}</div>", unsafe_allow_html=True)
            with c_d:
                st.markdown(f"<div style='font-size:11.5px; text-align:center; padding-top:6px;'>{d_val}</div>", unsafe_allow_html=True)
            with c_m:
                st.markdown(f"<div style='font-size:11.5px; text-align:center; padding-top:6px;'>{m_val}</div>", unsafe_allow_html=True)
            with c_p:
                st.markdown(f"<div style='font-size:11.5px; font-size:11.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-top:6px;' title='{p_val}'>{p_val}</div>", unsafe_allow_html=True)
            with c_img:
                if fname != "none" and os.path.exists(os.path.join(D, fname)):
                    if st.button("🔍", key=f"zoom_{idx}", help="사진 크게 보기"):
                        show_image_dialog(m_val, p_val, d_val, os.path.join(D, fname))
                else:
                    st.markdown("<div style='text-align:center; padding-top:6px;'>-</div>", unsafe_allow_html=True)
            with c_n:
                st.markdown(f"<div style='text-align:center; padding-top:4px;'>{n_val_html}</div>", unsafe_allow_html=True)
            with c_t:
                st.markdown(f"<div style='text-align:center; padding-top:4px;'>{t_val_html}</div>", unsafe_allow_html=True)
            with c_r:
                st.markdown(f"<div style='font-size:11.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-top:6px;' title='{r_val}'>{r_val}</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:4px 0; border:0; border-top:1px solid #f0f2f6;'>", unsafe_allow_html=True)

        st.markdown("---")
        with st.expander("🔐 관리자 메뉴 (백업 다운로드 / 수정 / 초기화)"):
            admin_input = st.text_input("관리자 비밀번호를 입력하세요", type="password")
            
            if admin_input == ADMIN_PW:
                st.success("✅ 관리자 인증이 완료되었습니다.")
                
                zb = io.BytesIO()
                with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as zf:
                    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                    zf.writestr("inspection_history.csv", csv_bytes)
                    if os.path.exists(D):
                        for file in os.listdir(D):
                            zf.write(os.path.join(D, file), arcname=os.path.join("inspection_images", file))
                zb.seek(0)
                
                backup_filename = f"backup_{get_kst_now().strftime('%Y%m%d')}.zip"
                st.download_button("💾 전체 검사 내역 및 사진 백업 다운로드", data=zb, file_name=backup_filename, mime="application/zip", type="primary", use_container_width=True)
                
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
                        
                        with st.form("edit_form"):
                            try:
                                default_in_date = datetime.strptime(str(curr_row.get("입고일자", ""))[:10], "%Y-%m-%d").date()
                            except:
                                default_in_date = kst_today
                            edit_in_date_val = st.date_input("포장재 입고 일자 수정", value=default_in_date)
                            edit_in_date_str = edit_in_date_val.isoformat()
                            
                            try:
                                default_inspect_date = datetime.strptime(str(curr_row.get("검사일자", ""))[:10], "%Y-%m-%d").date()
                            except:
                                default_inspect_date = kst_today
                            edit_inspect_date_val = st.date_input("검사 일자 수정", value=default_inspect_date)
                            edit_inspect_date_str = edit_inspect_date_val.isoformat()
                            
                            edit_mat_no = st.text_input("포장재 번호 수정", value=str(curr_row.get("포장재번호", "")))
                            edit_pack_name = st.text_input("포장재 약호 수정", value=str(curr_row.get("포장재약호", "")))
                            
                            nail_opts = ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)", "🟡 시험 대기 (사양 확인 중)"]
                            curr_nail = str(curr_row.get("손톱박리", ""))
                            nail_default = nail_opts.index(curr_nail) if curr_nail in nail_opts else 0
                            edit_nail = st.selectbox("손톱 박리 결과 수정", nail_opts, index=nail_default)
                            
                            tape_opts = ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)", "🟡 시험 대기 (사양 확인 중)"]
                            curr_tape = str(curr_row.get("테이프박리", ""))
                            tape_default = tape_opts.index(curr_tape) if curr_tape in tape_opts else 0
                            edit_tape = st.selectbox("테이프 박리 결과 수정", tape_opts, index=tape_default)
                            
                            edit_file = st.file_uploader("새로운 사진으로 교체 (선택사항)", type=["jpg", "jpeg", "png"])
                            edit_rem = st.text_area("특이사항 수정", value=str(curr_row.get("특이사항", "-")))
                            
                            update_btn = st.form_submit_button("🔄 수정 내용 반영하기", type="primary")
                            
                            if update_btn:
                                new_fn = str(curr_row.get("사진파일명", "none"))
                                if edit_file:
                                    s_lot = "".join(c for c in edit_mat_no if c.isalnum())
                                    t_str = get_kst_now().strftime("%Y%m%d_%H%M%S")
                                    new_fn = f"{s_lot}_{t_str}_{edit_file.name}"
                                    file_path = os.path.join(D, new_fn)
                                    with open(file_path, "wb") as f:
                                        f.write(edit_file.getbuffer())
                                
                                updated_row_data = [
                                    edit_in_date_str,
                                    edit_inspect_date_str,
                                    str(edit_mat_no),
                                    str(edit_pack_name) if edit_pack_name.strip() else "-",
                                    new_fn,
                                    edit_nail,
                                    edit_tape,
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
    "Author : 김태현 책임기사<br>Version : v1.10.57 (Native st.dialog True Center Fix)" \
    "</div>", 
    unsafe_allow_html=True
)
