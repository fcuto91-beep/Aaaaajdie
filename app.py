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
st.subheader("📋 전체 내역 표 (Table)")

if os.path.exists(F):
    try:
        df = pd.read_csv(F)
        q = st.text_input("🔍 검색", placeholder="검색어...")
        
        if q:
            df_f = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False).any(), axis=1)].reset_index(drop=True)
        else:
            df_f = df.reset_index(drop=True)

        # 💡 모바일에서 깔끔하게 스크롤되는 네이티브 표 출력
        st.dataframe(df_f, use_container_width=True)

        st.markdown("### 🔍 사진 개별 확인")
        has_img = False
        for idx, row in df_f.iterrows():
            fname = str(row["사진파일명"])
            if fname != "none":
                ip = D + "/" + fname
                if os.path.exists(ip):
                    has_img = True
                    with open(ip, "rb") as f:
                        ib = f.read()
                    st.download_button(
                        f"📥 [{row['자재/LOT명']}] 사진 보기 ({row['검사일시']})",
                        ib,
                        file_name=fname,
                        mime="image/jpeg",
                        key=f"z_{idx}",
                        use_container_width=True
                    )
        if not has_img:
            st.caption("저장된 사진이 없습니다.")

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
