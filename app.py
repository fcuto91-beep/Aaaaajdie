import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile
import requests
import json
from PIL import Image

st.set_page_config(page_title="Inspection", layout="centered")

D = "inspection_images"
LOGO_PATH = "logo.png"
ADMIN_PW = "1234"  # 💡 관리자 비밀번호
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxxZFR3sBQRIMZxBiZfamJiIvPwTI4UGrVaHkfQnMQJqFm8ZFnUJyScN-fShF2ZoyLHBw/exec"

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))

# 💡 구글 시트에서 데이터 불러오기 함수
def load_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
    
    return pd.DataFrame(columns=["검사일시", "포장재번호", "포장재약호", "손톱박리", "테이프박리", "사진파일명", "특이사항"])

# 💡 구글 시트에 데이터 추가하기 함수
def append_to_sheet(row_data):
    try:
        payload = {
            "action": "append",
            "row": row_data
        }
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

# 💡 구글 시트 데이터 수정하기 함수
def update_sheet(date_val, mat_val, row_data):
    try:
        payload = {
            "action": "update",
            "date": str(date_val),
            "mat_no": str(mat_val),
            "row": row_data
        }
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

# 💡 이미지 자동 압축 및 저장 함수 (버퍼링 제거
