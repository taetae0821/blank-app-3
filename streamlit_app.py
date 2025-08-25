# streamlit_app.py

import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="이러다가 나도 유명화가??",
    page_icon="🎨",
    layout="wide"
)

# --- API 연동 함수 ---
@st.cache_data
def get_artworks(artist_name):
    api_url = f"https://api.artic.edu/api/v1/artworks/search?q={artist_name}&fields=id,title,image_id,artist_title&limit=9"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()['data']
        
        artworks = []
        for item in data:
            if item.get('image_id'):
                artworks.append({
                    "title": item['title'],
                    "artist": item['artist_title'],
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
    artists = ["Vincent van Gogh", "Claude Monet", "Rembrandt"]
    selected_artist = st.radio(
        "감상하고 싶은 화가를 선택하세요:",
        artists
    )
    st.divider()
    st.header("🖌️ 그리기 도구")
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

with st.spinner(f"{selected_artist}의 작품을 불러오는 중..."):
    artworks = get_artworks(selected_artist)

    if not artworks:
        st.warning("작품을 불러오지 못했습니다. 다른 화가를 선택해보세요.")
    else:
        cols = st.columns(3)
        for i, art in enumerate(artworks):
            with cols[i % 3]:
                # ✨ 여기가 바로 수정한 부분입니다! ✨
                st.image(art['image_url'], caption=f"{art['title']}", use_container_width=True)

st.divider()

# 2. 그림판 (캔버스)
st.header("🎨 나만의 캔버스")
st.write("왼쪽 도구 모음에서 색과 굵기를 조절하여 자유롭게 그림을 그려보세요!")

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=500,
    drawing_mode=drawing_mode,
    key="canvas",
)

# 3. 그림 저장하기
if canvas_result.image_data is not None:
    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
    
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