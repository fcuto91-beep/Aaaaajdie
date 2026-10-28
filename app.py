import streamlit as st
import pandas as pd
import datetime

# 예시: 데이터 로드 함수 (실제 사용하시는 데이터 불러오기 코드로 대체)
@st.cache_data
def load_data():
    # 예시 CSV 파일 경로
    try:
        return pd.read_csv("inspection_data.csv")
    except FileNotFoundError:
        # 파일이 없을 경우 테스트용 빈 데이터프레임 반환
        return pd.DataFrame(columns=["일자", "포장재 번호", "포장재 약호", "손톱", "테이프", "특이사항"])

df = load_data()

# 화면 아래쪽 기존 관리자 메뉴 영역 확장
with st.expander("🛠️ 관리자 메뉴 (다운로드 / 초기화 / 데이터 수정)"):
    
    # 1. 기존 다운로드 및 초기화 버튼 (유지)
    st.write("### 데이터 관리")
    # ... 기존 다운로드/초기화 코드 ...
    
    st.divider()
    
    # 2. 포장재 번호 수정 기능 추가
    st.write("### ✏️ 잘못 입력된 포장재 번호 수정")
    
    # 관리자 비밀번호 인증 (필요시 보안 강화)
    admin_pw = st.text_input("관리자 비밀번호를 입력하세요", type="password", key="admin_pw_input")
    
    if admin_pw == "1234":  # 설정하실 비밀번호로 변경
        if df.empty:
            st.info("수정할 검사 내역 데이터가 없습니다.")
        else:
            # 수정할 데이터 선택 (예: 최근 순 또는 일자별 검색)
            # 사용자가 쉽게 찾을 수 있도록 '일자 + 포장재 번호 + 약호' 조합으로 셀렉트박스 구성
            df['display_label'] = df['일자'].astype(str) + " | 번호: " + df['포장재 번호'].astype(str) + " | " + df['포장재 약호'].astype(str)
            
            selected_row_label = st.selectbox("수정할 검사 내역을 선택하세요", df['display_label'].tolist())
            
            if selected_row_label:
                # 선택된 행의 인덱스 찾기
                selected_idx = df[df['display_label'] == selected_row_label].index[0]
                
                current_date = df.loc[selected_idx, '일자']
                current_no = df.loc[selected_idx, '포장재 번호']
                current_name = df.loc[selected_idx, '포장재 약호']
                
                st.write(f"- **선택한 항목 정보**: [{current_date}] {current_name}")
                
                # 새로운 포장재 번호 입력
                new_packing_no = st.text_input("수정할 올바른 포장재 번호 입력", value=str(current_no))
                
                if st.button("포장재 번호 변경 저장"):
                    if new_packing_no.strip() == "":
                        st.warning("변경할 포장재 번호를 입력해주세요.")
                    else:
                        # 데이터프레임 값 업데이트
                        df.loc[selected_idx, '포장재 번호'] = new_packing_no
                        
                        # 임시로 만든 display_label 컬럼은 저장 전 삭제
                        df_to_save = df.drop(columns=['display_label'])
                        
                        # 파일로 저장 (CSV 기준)
                        df_to_save.to_csv("inspection_data.csv", index=False, encoding='utf-8-sig')
                        
                        st.success(f"포장재 번호가 성공적으로 수정되었습니다! ({current_no} ➔ {new_packing_no})")
                        
                        # 화면 새로고침 (변경사항 즉시 반영)
                        st.rerun()
    elif admin_pw:
        st.error("비밀번호가 틀렸습니다.")
