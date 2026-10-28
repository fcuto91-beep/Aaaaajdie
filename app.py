import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile
import base64

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
            t_str = datetime.now(KST).strftime('%Y%m%d_%H%M%S')
            fn = f"{s_lot}_{t_str}_{up_file.name}"
            with open(os.path.join(D, fn), "wb") as f:
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

st.markdown("---")
st.subheader("📋 전체 검사 내역")

if os.path.exists(F):
    try:
        df = pd.read_csv(F)
        q = st.text_input("🔍 검색", placeholder="검색어 입력...")
        df_f = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False).any(), axis=1)].reset_index(drop=True) if q else df.reset_index(drop=True)

        # 💡 URL 쿼리스트링을 통한 돋보기 팝업 사진 연동 처리
        selected_view_idx = st.query_params.get("view_idx", None)
        if selected_view_idx is not None:
            try:
                v_idx = int(selected_view_idx)
                if 0 <= v_idx < len(df_f):
                    v_row = df_f.iloc[v_idx]
                    st.markdown("---")
                    st.markdown(f"### 📸 팝업 사진 미리보기")
                    st.info(f"📦 **LOT: {v_row['자재/LOT명']}** | 📅 **일시: {v_row['검사일시']}**")
                    
                    v_fname = str(v_row["사진파일명"])
                    if v_fname != "none":
                        v_ip = os.path.join(D, v_fname)
                        if os.path.exists(v_ip):
                            st.image(v_ip, use_container_width=True, caption=f"{v_row['자재/LOT명']} 현장 사진")
                        else:
                            st.warning("⚠️ 사진 파일이 존재하지 않습니다.")
                    
                    if st.button("❌ 닫기", use_container_width=True):
                        st.query_params.clear()
                        st.rerun()
                    st.markdown("---")
            except:
                st.query_params.clear()

        # 💡 모바일/PC에서 절대 세로로 깨지지 않고 가로/세로 스크롤을 유지하는 완벽한 HTML 표 그리드
        rows_html = ""
        for idx, row in df_f.iterrows():
            d_val = str(row["검사일시"])
            l_val = str(row["자재/LOT명"])
            n_val = str(row["손톱박리"])
            t_val = str(row["테이프박리"])
            r_val = str(row["특이사항"]) if pd.notna(row["특이사항"]) else "-"
            
            img_td = "-"
            fname = str(row["사진파일명"])
            if fname != "none":
                ip = os.path.join(D, fname)
                if os.path.exists(ip):
                    # 돋보기를 누르면 해당 행의 사진이 팝업으로 연동되도록 쿼리스트링 링크 연결
                    img_td = f'<a href="?view_idx={idx}" style="text-decoration:none; font-size:1.4rem;" title="사진 보기">🔍</a>'

            rows_html += f'''
            <tr style="border-bottom: 1px solid #e0e0e0; background-color: #fff;">
                <td style="padding:10px 8px; white-space:nowrap; color:#333; font-size:12px;">{d_val}</td>
                <td style="padding:10px 8px; white-space:nowrap; font-weight:bold; color:#111; font-size:12px;">{l_val}</td>
                <td style="padding:10px 8px; white-space:nowrap; color:#333; font-size:12px;">{n_val}</td>
                <td style="padding:10px 8px; white-space:nowrap; color:#333; font-size:12px;">{t_val}</td>
                <td style="padding:10px 8px; min-width:120px; color:#555; font-size:12px;">{r_val}</td>
                <td style="padding:10px 8px; text-align:center;">{img_td}</td>
            </tr>
            '''

        table_html = f'''
        <div style="overflow-x: auto; max-height: 420px; border: 1px solid #dcdcdc; border-radius: 8px; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <thead style="position: sticky; top: 0; background-color: #f1f3f5; z-index: 10; border-bottom: 2px solid #ccc;">
                    <tr>
                        <th style="padding:10px 8px; white-space:nowrap; font-size:12px;">일시</th>
                        <th style="padding:10px 8px; white-space:nowrap; font-size:12px;">LOT</th>
                        <th style="padding:10px 8px; white-space:nowrap; font-size:12px;">손톱</th>
                        <th style="padding:10px 8px; white-space:nowrap; font-size:12px;">테이프</th>
                        <th style="padding:10px 8px; white-space:nowrap; font-size:12px;">특이사항</th>
                        <th style="padding:10px 8px; white-space:nowrap; text-align:center; font-size:12px;">미리보기</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        '''
        
        st.markdown(table_html, unsafe_allow_html=True)

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
