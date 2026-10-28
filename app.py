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

lot = st.text_input("자재 / LOT명 입력")

st.markdown("---")
st.subheader("📝 시험 결과")

nail = st.selectbox("1️⃣ 손톱박리", ["적합", "부적합"])
tape = st.selectbox("2️⃣ 테이프박리", ["적합", "부적합"])

st.markdown("---")
up_file = st.file_uploader("현장 사진", type=["jpg", "jpeg", "png"])

if up_file:
    st.image(up_file, width=250)

rem = st.text_area("특이사항", placeholder="입력")

if st.button("💾 Save", type="primary"):
    if not lot.strip():
        st.warning("⚠️ LOT명을 입력해 주세요!")
    else:
        dt = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        fn = "none"
        if up_file:
            s_lot = "".join(c for c in lot if c.isalnum())
            t_str = datetime.now(KST).strftime('%Y%m%d_%H%M%S')
            fn = f"{s_lot}_{t_str}_{up_file.name}"
            path = D + "/" + fn
            with open(path, "wb") as f:
                f.write(up_file.getbuffer())

        nd = pd.DataFrame([{
            "검사일시": dt,
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
st.subheader("📋 전체 검사 내역 (표 형식)")

if os.path.exists(F):
    try:
        df = pd.read_csv(F)
        q = st.text_input("🔍 검색", placeholder="검색어...")
        
        if q:
            df_f = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False).any(), axis=1)].reset_index(drop=True)
        else:
            df_f = df.reset_index(drop=True)

        # 💡 가로 스크롤과 표 형식을 지원하는 HTML 테이블 생성
        html = """
        <div style="overflow-x: auto; max-height: 450px; border: 1px solid #ddd; border-radius: 5px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; background-color: white;">
          <thead>
            <tr style="background-color: #f8f9fa; border-bottom: 2px solid #ccc; text-align: left;">
              <th style="padding: 8px; white-space: nowrap;">일시</th>
              <th style="padding: 8px; white-space: nowrap;">LOT</th>
              <th style="padding: 8px; white-space: nowrap;">손톱</th>
              <th style="padding: 8px; white-space: nowrap;">테이프</th>
              <th style="padding: 8px; white-space: nowrap;">특이사항</th>
              <th style="padding: 8px; white-space: nowrap; text-align: center;">미리보기</th>
            </tr>
          </thead>
          <tbody>
        """

        for idx, row in df_f.iterrows():
            dt_val = str(row["검사일시"])
            lot_val = str(row["자재/LOT명"])
            nail_val = str(row["손톱박리"])
            tape_val = str(row["테이프박리"])
            rem_val = str(row["특이사항"]) if pd.notna(row["특이사항"]) else ""
            
            # 사진 미리보기 링크 (새 창 띄우기)
            img_td = "-"
            fname = str(row["사진파일명"])
            if fname != "none":
                ip = D + "/" + fname
                if os.path.exists(ip):
                    with open(ip, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                    img_td = f'<a href="data:image/jpeg;base64,{encoded}" target="_blank" style="text-decoration:none; font-size:1.2rem;" title="새 창으로 사진 보기">🔍</a>'

            html += f"""
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 8px; white-space: nowrap;">{dt_val}</td>
              <td style="padding: 8px; white-space: nowrap;">{lot_val}</td>
              <td style="padding: 8px; white-space: nowrap;">{nail_val}</td>
              <td style="padding: 8px; white-space: nowrap;">{tape_val}</td>
              <td style="padding: 8px; min-width: 120px;">{rem_val}</td>
              <td style="padding: 8px; text-align: center;">{img_td}</td>
            </tr>
            """

        html += """
          </tbody>
        </table>
        </div>
        """
        
        st.markdown(html, unsafe_allow_html=True)

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
        if st.button("🗑️ Reset Data", use_container_width=True):
            os.remove(F)
            st.success("Reset!")
            st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("저장된 이력이 없습니다.")
