ㅍ# streamlit_app.py

import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="이러다가 나도 유명화가??",
    page_icon="🎨",
    layout="wide"
)

# --- 세션 상태 초기화 ---
# ✨ 1. 캔버스의 배경 이미지를 기억할 변수 추가
if 'background_image' not in st.session_state:
    st.session_state.background_image = None

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
st.write("마음에 드는 작품을 선택해 캔버스 위에서 직접 따라 그려보세요!")
st.divider()

# --- 사이드바 ---
with st.sidebar:
    st.header("✨ 화가 선택")
    artists = ["Vincent van Gogh", "Claude Monet", "Rembrandt", "Katsushika Hokusai"]
    selected_artist = st.radio("감상하고 싶은 화가를 선택하세요:", artists)
    st.divider()
    st.header("🖌️ 그리기 도구")
    stroke_width = st.slider("선의 굵기", 1, 50, 3)
    stroke_color = st.color_picker("선의 색상", "#000000")
    bg_color = st.color_picker("배경 색상 (이미지 없을 시)", "#FFFFFF")
    drawing_mode = st.selectbox("그리기 모드", ("freedraw", "line", "rect", "circle", "transform"))

# --- 메인 화면 ---

# 1. 선택된 화가의 작품 보여주기
st.header(f"🖼️ {selected_artist}의 작품들")
st.info("마음에 드는 작품 아래의 '이 그림으로 그리기' 버튼을 클릭하면 캔버스 배경으로 설정됩니다.")

with st.spinner(f"{selected_artist}의 작품을 불러오는 중..."):
    artworks = get_artworks(selected_artist)

    if not artworks:
        st.warning("작품을 불러오지 못했습니다. 다른 화가를 선택해보세요.")
    else:
        cols = st.columns(3)
        for i, art in enumerate(artworks):
            with cols[i % 3]:
                st.image(art['image_url'], caption=art['title'], use_container_width=True)
                
                # ✨ 2. 각 이미지 아래에 '이 그림으로 그리기' 버튼 추가
                # 각 버튼을 구분하기 위해 이미지 URL을 key로 사용합니다.
                if st.button("이 그림으로 그리기", key=f"btn_{art['image_url']}", use_container_width=True):
                    # 버튼이 클릭되면, 해당 이미지 URL로부터 이미지를 다운로드 받습니다.
                    with st.spinner("이미지를 캔버스로 옮기는 중..."):
                        response = requests.get(art['image_url'])
                        # 다운로드 받은 이미지 데이터를 PIL 이미지 객체로 변환합니다.
                        bg_image = Image.open(BytesIO(response.content))
                        # 변환된 이미지를 세션 상태에 저장합니다.
                        st.session_state.background_image = bg_image
                        # 페이지를 새로고침하여 캔버스에 즉시 반영합니다.
                        st.rerun()

st.divider()

# 2. 그림판 (캔버스)
st.header("🎨 나만의 캔버스")

# ✨ 3. 배경 이미지를 지울 수 있는 버튼 추가
if st.session_state.background_image is not None:
    if st.button("배경 이미지 지우기"):
        st.session_state.background_image = None
        st.rerun()

# ✨ 4. st_canvas의 background_image 매개변수에 세션 상태의 이미지 전달
# 세션에 배경 이미지가 있으면 그것을, 없으면 사이드바에서 선택한 단색 배경을 사용합니다.
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    background_image=st.session_state.background_image, # 이 부분이 핵심!
    update_streamlit=True,
    height=500,
    drawing_mode=drawing_mode,
    key="canvas",
)

# 3. 그림 저장하기 (이전과 동일)
if canvas_result.image_data is not None:
    # 캔버스에서 받은 이미지 데이터를 PNG 파일 형식으로 변환합니다.
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