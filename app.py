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
        dt = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        fn = "none"
        if up_file:
            s_lot = "".join(c for c in lot if c.isalnum())
            t_str = datetime.now(KST).strftime('%Y%m%d_%H%M%S')
            fn = f"{s_lot}_{t_str}_{up_file.name}"
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
st.subheader("📋 전체 검사 내역 (스크롤 표)")

if os.path.exists(F):
    try:
        df = pd.read_csv(F)
        q = st.text_input("🔍 검색", placeholder="검색어...")
        df_f = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False).any(), axis=1)].reset_index(drop=True) if q else df.reset_index(drop=True)

        # 💡 모바일 가로/세로 스크롤이 완벽하게 지원되는 네이티브 표 + 행 선택 기능
        event = st.dataframe(
            df_f,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
            key="inspection_table"
        )

        # 💡 표에서 행을 선택하면 해당 사진이 팝업(영역)으로 즉시 출력
        selection_rows = event.selection.rows
        if selection_rows:
            sel_idx = selection_rows[0]
            selected_row = df_f.iloc[sel_idx]
            fname = str(selected_row["사진파일명"])
            
            st.markdown("---")
            st.markdown(f"### 📸 선택한 검사 상세 & 사진 미리보기")
            st.info(f"📦 **LOT: {selected_row['자재/LOT명']}** | 📅 **일시: {selected_row['검사일시']}**")
            
            if fname != "none":
                ip = os.path.join(D, fname)
                if os.path.exists(ip):
                    st.image(ip, width=300, caption=f"{selected_row['자재/LOT명']} 현장 사진")
                else:
                    st.warning("⚠️ 저장된 사진 파일이 존재하지 않습니다.")
            else:
                st.caption("ℹ️ 이 검사 항목에는 첨부된 사진이 없습니다.")

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
