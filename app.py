import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile

st.set_page_config(page_title="Inspection", layout="centered")
st.title("🛡️ 공정 검사 및 이력 관리")

F = "inspection_history.csv"
D = "inspection_images"

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))
st.info(f"⏰ 시각: **{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}**")

with st.form("f1", clear_on_submit=True):
    st.subheader("📝 시험 결과 입력")
    lot = st.text_input("자재 / LOT명")
    nail = st.selectbox("1️⃣ 손톱박리", ["적합", "부적합"])
    tape = st.selectbox("2️⃣ 테이프박리", ["적합", "부적합"])
    up_file = st.file_uploader("현장 사진", type=["jpg", "jpeg", "png"])
    rem = st.text_area("특이사항")
    ok = st.form_submit_button("💾 Save", type="primary")

if ok:
    if not lot.strip():
        st.warning("⚠️ LOT명을 입력해 주세요!")
    else:
        dt_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        fn = "none"
        if up_file:
            s_lot = "".join(c for c in lot if c.isalnum())
            t_str = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
            fn = f"{s_lot}_{t_str}_{up_file.name}"
            file_path = os.path.join(D, fn)
            with open(file_path, "wb") as f:
                f.write(up_file.getbuffer())

        nd = pd.DataFrame([{
            "검사일시": dt_str,
            "자재/LOT명": lot,
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
@st.dialog("📸 사진 팝업 미리보기")
def show_image_popup(img_path, lot_name, date_str):
    st.markdown(f"📦 **LOT: {lot_name}**")
    st.caption(f"📅 검사일시: {date_str}")
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
                    p_fname = str(p_row["사진파일명"])
                    if p_fname != "none":
                        p_ip = os.path.join(D, p_fname)
                        if os.path.exists(p_ip):
                            show_image_popup(p_ip, str(p_row["자재/LOT명"]), str(p_row["검사일시"]))
                st.query_params.clear()
            except:
                st.query_params.clear()

        # 💡 HTML 표 기반 렌더링 (일시 폭 축소 & 미리보기 위치 변경)
        rows_list = []
        for idx, row in df_f.iterrows():
            d_val = str(row["검사일시"])
            l_val = str(row["자재/LOT명"])
            n_val = str(row["손톱박리"])
            t_val = str(row["테이프박리"])
            r_val = str(row["특이사항"]) if pd.notna(row["특이사항"]) else "-"
            
            fname = str(row["사진파일명"])
            if fname != "none":
                ip = os.path.join(D, fname)
                if os.path.exists(ip):
                    img_td = '<a href="?pop_idx=' + str(idx) + '" target="_self" style="text-decoration:none; font-size:16px;">🔍</a>'
                else:
                    img_td = '-'
            else:
                img_td = '-'

            row_str = '<tr>' \
                      '<td style="padding:8px 6px; width:110px; white-space:nowrap; font-size:11px; color:#333;">' + d_val + '</td>' \
                      '<td style="padding:8px 6px; white-space:nowrap; font-weight:bold; font-size:12px;">' + l_val + '</td>' \
                      '<td style="padding:8px 6px; white-space:nowrap; font-size:12px;">' + n_val + '</td>' \
                      '<td style="padding:8px 6px; white-space:nowrap; font-size:12px;">' + t_val + '</td>' \
                      '<td style="padding:8px 6px; text-align:center; width:60px;">' + img_td + '</td>' \
                      '<td style="padding:8px 6px; min-width:90px; font-size:12px; color:#555;">' + r_val + '</td>' \
                      '</tr>'
            rows_list.append(row_str)

        all_rows = "".join(rows_list)

        table_code = '<div style="overflow-x:auto; max-height:400px; border:1px solid #ccc; border-radius:6px; background-color:#fff;">' \
                     '<table style="width:100%; border-collapse:collapse; text-align:left;">' \
                     '<thead style="position:sticky; top:0; background-color:#f0f2f6; border-bottom:2px solid #ddd; z-index:10;">' \
                     '<tr>' \
                     '<th style="padding:8px 6px; width:110px; white-space:nowrap; font-size:11px;">일시</th>' \
                     '<th style="padding:8px 6px; white-space:nowrap; font-size:12px;">LOT</th>' \
                     '<th style="padding:8px 6px; white-space:nowrap; font-size:12px;">손톱</th>' \
                     '<th style="padding:8px 6px; white-space:nowrap; font-size:12px;">테이프</th>' \
                     '<th style="padding:8px 6px; text-align:center; width:60px; font-size:12px;">미리보기</th>' \
                     '<th style="padding:8px 6px; white-space:nowrap; font-size:12px;">특이사항</th>' \
                     '</tr>' \
                     '</thead>' \
                     '<tbody>' + all_rows + '</tbody>' \
                     '</table>' \
                     '</div>'

        st.markdown(table_code, unsafe_allow_html=True)

        st.markdown("---")
        zb = io.BytesIO()
        with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(F, arcname="inspection_history.csv")
            for root, dirs, files in os.walk(D):
                for file in files:
                    zf.write(os.path.join(root, file), arcname=os.path.join("inspection_images", file))
        zb.seek(0)
        
        st.download_button("📦 Download ZIP", data=zb, file_name=f"backup_{datetime.now(KST).strftime('%Y%m%d')}.zip", mime="application/zip", type="primary", use_container_width=True)
        
        st.markdown("")
        if st.button("🗑️ Reset", use_container_width=True):
            os.remove(F)
            st.success("Reset done!")
            st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("아직 저장된 검사 이력이 없습니다.")
