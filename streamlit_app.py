# streamlit_app.py

import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import base64

# streamlit-drawable-canvas 라이브러리에서 필요한 기능을 가져옵니다.
from streamlit_drawable_canvas import st_canvas

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="이러다가 나도 유명화가??",
    page_icon="🎨",
    layout="wide"
)

# --- 세션 상태 초기화 ---
if 'background_image_pil' not in st.session_state:
    st.session_state.background_image_pil = None

# --- ✨ 핵심 수정 ✨ ---
# PIL Image 객체는 캐시할 수 없으므로, 이 함수의 @st.cache_data 데코레이터를 제거합니다.
# 이 함수는 계산이 빠르므로 캐시가 불필요합니다.
def image_to_base64(image):
    """PIL Image 객체를 Base64 문자열로 변환합니다."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- API 연동 함수 (캐시 유지) ---
@st.cache_data
def get_artworks(artist_name):
    """시카고 미술관 API를 사용해 화가의 작품 정보를 가져옵니다."""
    api_url = f"https://api.artic.edu/api/v1/artworks/search?q={artist_name}&fields=id,title,image_id,artist_title&limit=9"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()['data']
        artworks = [{"title": item['title'], "artist": item['artist_title'], "image_url": f"https://www.artic.edu/iiif/2/{item['image_id']}/full/400,/0/default.jpg"} for item in data if item.get('image_id')]
        return artworks
    except requests.exceptions.RequestException:
        st.error("API 호출 중 오류가 발생했습니다. 인터넷 연결을 확인해주세요.")
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
                if st.button("이 그림으로 그리기", key=f"btn_{art['image_url']}", use_container_width=True):
                    with st.spinner("이미지를 캔버스로 옮기는 중..."):
                        response = requests.get(art['image_url'])
                        bg_image_pil = Image.open(BytesIO(response.content))
                        st.session_state.background_image_pil = bg_image_pil
                        st.rerun()

st.divider()

# 2. 그림판 (캔버스)
st.header("🎨 나만의 캔버스")

if st.session_state.background_image_pil:
    if st.button("배경 이미지 지우기"):
        st.session_state.background_image_pil = None
        st.rerun()

# CSS를 사용해 배경 이미지 설정
canvas_container_style = "border: 1px solid #ccc; border-radius: 0.5rem; padding: 0; margin: 0;"
if st.session_state.background_image_pil:
    bg_image_b64 = image_to_base64(st.session_state.background_image_pil)
    canvas_container_style += f"""
        background-image: url("data:image/png;base64,{bg_image_b64}");
        background-size: contain; background-repeat: no-repeat; background-position: center;
    """

# CSS 스타일을 적용한 컨테이너 안에 캔버스를 넣습니다.
with st.container():
    st.markdown(f'<div style="{canvas_container_style}">', unsafe_allow_html=True)
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="rgba(0, 0, 0, 0)",
        update_streamlit=True,
        height=500,
        drawing_mode=drawing_mode,
        key="canvas",
    )
    st.markdown('</div>', unsafe_allow_html=True)

# 3. 그림 저장하기
if canvas_result.image_data is not None and canvas_result.image_data.shape[2] == 4:
    img_data = canvas_result.image_data
    if st.session_state.background_image_pil:
        bg_img = st.session_state.background_image_pil.resize((img_data.shape[1], img_data.shape[0]))
        final_img = Image.alpha_composite(bg_img.convert('RGBA'), Image.fromarray(img_data))
    else:
        final_img = Image.new('RGB', (img_data.shape[1], img_data.shape[0]), 'white')
        final_img.paste(Image.fromarray(img_data), mask=Image.fromarray(img_data))

    buf = BytesIO()
    final_img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="그림 저장하기 (PNG)",
        data=byte_im,
        file_name="my_masterpiece.png",
        mime="image/png",
        type="primary"
    )