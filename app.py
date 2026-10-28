import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile

st.set_page_config(page_title="Inspection System", layout="centered")
st.title("🛡️ 공정 검사 및 이력 관리")

F = "inspection_history.csv"
D = "inspection_images"

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))
st.info(f"⏰ 현재 검사 시각: **{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}**")

lot = st.text_input("자재 / LOT명 입력")

st.markdown("---")
st.subheader("📝 시험 항목별 결과 판정")

nail = st.selectbox("1️⃣ 손톱박리 검사 결과", ["적합", "부적합"])
tape = st.selectbox("2️⃣ 테이프 박리 검사 결과", ["적합", "부적합"])

st.markdown("---")
up_file = st.file_uploader("현장 사진 첨부", type=["jpg", "jpeg", "png"])

if up_file:
    st.image(up_file, caption="사진 미리보기", width=250)

rem = st.text_area("특이사항 및 조치 내용", placeholder="특이사항 입력")

if st.button("💾 검사 이력 저장하기", type="primary"):
    if not lot.strip():
        st.warning("⚠️ 자재 / LOT명을 입력해 주세요!")
    else:
        try:
            dt = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
            fn = "none"
            if up_file:
                s_lot = "".join(c for c in lot if c.isalnum() or c in ('_', '-'))
                fn = f"{s_lot}_{datetime.now(KST).strftime('%Y%m%d_%H%M%S')}_{up_file.name}"
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

            if os.path.exists(F):
                try:
                    df_ex = pd.read_csv(F)
                    if df_ex.empty:
                        df_c = nd
                    else:
                        df_c = pd.concat([df_ex, nd], ignore_index=True)
                except:
                    df_c = nd
            else:
                df_c = nd

            df_c.to_csv(F, index=False, encoding="utf-8-sig")
            st.success("✅ 저장 완료!")
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")

st.markdown("---")
st.subheader("📋 전체 검사 내역 리스트")

if os.path.exists(F):
    try:
        df = pd.read_csv(F)
        q = st.text_input("🔍 이력 검색", placeholder="검색어 입력...")
        df_f = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False).any(), axis=1)].reset_index(drop=True) if q else df.reset_index(drop=True)

        for idx, row in df_f.iterrows():
            with st.container(border=True):
                st.markdown(f"📦 **LOT: {row['자재/LOT명']}**")
                st.caption(f"📅 검사일시: {row['검사일시']}")
                
                col1, col2 = st.columns(2)
                col1.write(f"손톱: **{row['손톱박리']}**")
                col2.write(f"테이프: **{row['테이프박리']}**")
                
                if str(row['특이사항']).strip() and str(row['특이사항']) != "nan":
                    st.markdown(f"💬 특이사항: {row['특이사항']}")
                
                fname = str(row["사진파일명"])
                if fname != "none":
                    ip = os.path.join(D, fname)
                    if os.path.exists(ip):
                        with open(ip, "rb") as f:
                            ib = f.read()
                        st.download_button(
                            "🔍 돋보기 (새 창으로 사진 보기)",
                            ib,
                            file_name=fname,
                            mime="image/jpeg",
                            key=f"z_{idx}",
                            use_container_width=True
                        )
                    else:
                        st.write("📷 사진 파일 없음")
                else:
                    st.write("📷 첨부된 사진 없음")

        st.markdown("---")
        zb = io.BytesIO()
        with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(F, arcname="inspection_history.csv")
            for root, dirs, files in os.walk(D):
                for file in files:
                    zf.write(os.path.join(root, file), arcname=os.path.join("inspection_images", file))
        zb.seek(0)
        
        st.download_button("📦 ZIP 다운로드", data=zb, file_name=f"backup_{datetime.now(KST).strftime('%Y%m%d')}.zip", mime="application/zip", type="primary", use_container_width=True)
        
        st.markdown("")
        if st.button("🗑️ 데이터 파일 초기화
