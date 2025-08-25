# streamlit_app.py

import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO

# streamlit-drawable-canvas 라이브러리에서 필요한 기능을 가져옵니다.
from streamlit_drawable_canvas import st_canvas

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="이러다가 나도 유명화가??",
    page_icon="🎨",
    layout="wide"
)

# --- API 연동 함수 ---
# @st.cache_data: 이 함수가 실행된 결과를 저장(캐시)해 둡니다.
# 똑같은 화가를 다시 선택했을 때, API를 또 호출하지 않고 저장된 결과를 바로 보여줘서 속도가 빨라집니다.
@st.cache_data
def get_artworks(artist_name):
    """
    시카고 미술관(Art Institute of Chicago)의 무료 API를 사용해
    지정된 화가의 작품 정보를 가져오는 함수입니다.
    """
    # API URL 주소. 화가 이름으로 작품을 검색합니다.
    api_url = f"https://api.artic.edu/api/v1/artworks/search?q={artist_name}&fields=id,title,image_id,artist_title&limit=9"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # 요청이 실패하면 오류를 발생시킵니다.
        data = response.json()['data']
        
        artworks = []
        for item in data:
            # 작품 이미지가 있는 경우에만 목록에 추가합니다.
            if item.get('image_id'):
                artworks.append({
                    "title": item['title'],
                    "artist": item['artist_title'],
                    # IIIF 표준에 따라 이미지 URL을 구성합니다.
                    "image_url": f"https://www.artic.edu/iiif/2/{item['image_id']}/full/400,/0/default.jpg"
                })
        return artworks
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return []

# --- 앱 제목 ---
st.title("🎨 이러다가 나도 유명화가??")
st.write("유명 화가의 작품을 감상하고, 직접 그림을 그려보세요!")
st.divider()

# --- 사이드바 ---
with st.sidebar:
    st.header("✨ 화가 선택")
    
    # st.radio를 사용해 사용자가 화가를 선택할 수 있게 합니다.
    # Streamlit의 위젯들은 사용자의 선택을 자동으로 세션 상태에 저장하고 유지합니다.
    artists = ["Vincent van Gogh", "Claude Monet", "Rembrandt"]
    selected_artist = st.radio(
        "감상하고 싶은 화가를 선택하세요:",
        artists
    )

    st.divider()
    st.header("🖌️ 그리기 도구")
    # 사용자가 그림 도구의 설정을 바꿀 수 있게 합니다.
    stroke_width = st.slider("선의 굵기", 1, 50, 3)
    stroke_color = st.color_picker("선의 색상", "#000000")
    bg_color = st.color_picker("배경 색상", "#FFFFFF")
    drawing_mode = st.selectbox(
        "그리기 모드",
        ("freedraw", "line", "rect", "circle", "transform")
    )

# --- 메인 화면 ---

# 1. 선택된 화가의 작품 보여주기
st.header(f"🖼️ {selected_artist}의 작품들")

# API를 호출하는 동안 로딩 스피너를 보여줘서 사용자가 기다릴 수 있게 합니다.
with st.spinner(f"{selected_artist}의 작품을 불러오는 중..."):
    artworks = get_artworks(selected_artist)

    if not artworks:
        st.warning("작품을 불러오지 못했습니다. 다른 화가를 선택해보세요.")
    else:
        # st.columns를 사용해 작품 이미지를 3열로 보기 좋게 나열합니다.
        cols = st.columns(3)
        for i, art in enumerate(artworks):
            with cols[i % 3]:
                st.image(art['image_url'], caption=f"{art['title']}", use_column_width=True)

st.divider()

# 2. 그림판 (캔버스)
st.header("🎨 나만의 캔버스")
st.write("왼쪽 도구 모음에서 색과 굵기를 조절하여 자유롭게 그림을 그려보세요!")

# st_canvas를 사용해 그림을 그릴 수 있는 캔버스 영역을 만듭니다.
# 사용자가 그린 그림은 'canvas_result.image_data'에 이미지 데이터 형태로 저장됩니다.
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # 도형 내부 색상
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=500,
    drawing_mode=drawing_mode,
    key="canvas",
)

# 3. 그림 저장하기
# 사용자가 캔버스에 무언가 그렸을 경우에만 저장 버튼을 활성화합니다.
if canvas_result.image_data is not None:
    # st.download_button을 사용해 사용자가 그린 그림을 다운로드할 수 있게 합니다.
    # 캔버스에서 받은 이미지 데이터를 PNG 파일 형식으로 변환합니다.
    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
    
    # 이미지를 메모리 상의 파일(BytesIO)로 변환하여 다운로드에 사용합니다.
    buf = BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="그림 저장하기 (PNG)",
        data=byte_im,
        file_name="my_masterpiece.png",
        mime="image/png",
        type="primary"
    )