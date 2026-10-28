import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="포장재 검사 내역 관리", layout="wide")

# 데이터 파일 경로 정의
DATA_FILE = "inspection_data.csv"

# 1. 데이터 로드 및 초기화 함수
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE)
        except Exception as e:
            st.error(f"데이터를 읽는 중 오류가 발생했습니다: {e}")
    
    # 파일이 없을 경우 기본 테스트 데이터 생성
    initial_data = {
        "일자": ["2026-10-28", "2026-10-28"],
        "포장재 번호": ["5114558", "51145554"],
        "포장재 약호": ["ANA-TMBBM(F)E 용기(공용)", "ANA-TMBBM(F)E CASE"],
        "손톱": ["적합(PASS)", "적합(PASS)"],
        "테이프": ["적합(PASS)", "적합(PASS)"],
        "특이사항": ["", ""]
    }
    df = pd.DataFrame(initial_data)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    return df

# 데이터 불러오기
df = load_data()

# --- [메인 화면] ---
st.title("📋 전체 검사 내역")

# 검색 기능
search_query = st.text_input("🔍 검색", placeholder="검색어 입력...")

# 검색어 필터링 로직
if search_query:
    # 데이터프레임의 모든 컬럼을 문자열로 변환 후 검색어 포함 여부 확인
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
    filtered_df = df[mask]
else:
    filtered_df = df

# 검사 내역 테이블 출력 (이미지 형태와 유사하게 구성)
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# --- [하단 관리자 메뉴 영역] ---
with st.expander("🛠️ 관리자 메뉴 (다운로드 / 초기화 / 데이터 수정)"):
    
    st.subheader("1. 데이터 내보내기 및 초기화")
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV 다운로드 버튼
        csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 전체 데이터 다운로드 (CSV)",
            data=csv_data,
            file_name=f"inspection_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    with col2:
        # 초기화 버튼 (주의 필요)
        if st.button("🗑️ 데이터 초기화 (주의)"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.success("데이터가 초기화되었습니다. 새로고침 해주세요.")
            st.rerun()

    st.divider()

    st.subheader("2. ✏️ 잘못 입력된 포장재 번호 수정 (관리자 전용)")
    
    # 관리자 인증 비밀번호 (원하시는 비밀번호로 변경하세요)
    admin_pw = st.text_input("관리자 비밀번호를 입력하세요", type="password", key="admin_pw_box")
    
    if admin_pw == "1234":  # 비밀번호 설정 (예: 1234)
        if df.empty:
            st.info("수정할 데이터가 없습니다.")
        else:
            # 사용자가 대상 행을 쉽게 찾을 수 있도록 레이블 생성
            df['__temp_label'] = "일자: " + df['일자'].astype(str) + " | 번호: " + df['포장재 번호'].astype(str) + " | " + df['포장재 약호'].astype(str)
            
            selected_label = st.selectbox("수정할 검사 내역 선택", df['__temp_label'].tolist())
            
            if selected_label:
                # 선택된 행의 인덱스 추출
                target_idx = df[df['__temp_label'] == selected_label].index[0]
                
                cur_date = df.loc[target_idx, '일자']
                cur_no = df.loc[target_idx, '포장재 번호']
                cur_name = df.loc[target_idx, '포장재 약호']
                
                st.write(f"- **선택된 정보**: `[{cur_date}]` **{cur_name}** (기존 번호: `{cur_no}`)")
                
                # 수정할 새로운 포장재 번호 입력
                new_no = st.text_input("수정할 올바른 포장재 번호 입력", value=str(cur_no))
                
                if st.button("포장재 번호 변경 반영"):
                    if not new_no.strip():
                        st.warning("변경할 번호를 입력해 주세요.")
                    else:
                        # 값 업데이트
                        df.loc[target_idx, '포장재 번호'] = new_no.strip()
                        
                        # 임시 레이블 컬럼 제거 후 저장
                        df_to_save = df.drop(columns=['__temp_label'])
                        df_to_save.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                        
                        st.success(f"포장재 번호가 수정되었습니다! (`{cur_no}` ➔ `{new_no}`)")
                        st.rerun()
                        
    elif admin_pw:
        st.error("관리자 비밀번호가 틀렸습니다.")

# 하단 작성자 정보 (이미지 하단부 참고 반영)
st.markdown(
    "<div style='text-align: right; color: gray; font-size: 12px;'>"
    "Author: 김태현 책임기사 &nbsp;|&nbsp; Version: v1.1.0"
    "</div>", 
    unsafe_allow_html=True
)
