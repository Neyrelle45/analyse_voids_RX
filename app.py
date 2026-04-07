import io
import json
import numpy as np
import streamlit as st
from PIL import Image
import cv2

from streamlit_drawable_canvas import st_canvas

from roi_canvas import shapes_to_roi_mask
from manual_edit import add_disk, add_potato, erase
from overlay import overlay_rx

st.set_page_config(layout="wide", page_title="RX Void Analyzer")

st.title("RX Void Analyzer – Canvas & corrections manuelles")

uploaded = st.file_uploader("Image RX", type=["png", "jpg", "jpeg"])
if not uploaded:
    st.stop()

img = np.array(Image.open(uploaded).convert("RGB"))
h, w = img.shape[:2]

if "roi_mask" not in st.session_state:
    st.session_state.roi_mask = np.zeros((h, w), dtype=np.uint8)

if "corr_mask" not in st.session_state:
    st.session_state.corr_mask = np.zeros((h, w), dtype=np.uint8)

# ---------- ROI CANVAS ----------
st.subheader("1️⃣ Définition des ROI (polygones)")


img_pil = Image.open(uploaded).convert("RGB")
img = np.array(img_pil)
h, w = img.shape[:2]

canvas = st_canvas(
    fill_color="rgba(0,255,0,0.35)",   # ROI vert translucide
    stroke_width=2,
    stroke_color="rgba(0,255,0,1)",
    background_image=img_pil,          # ✅ IMAGE RX DANS LE CANVAS
    height=h,
    width=w,
    drawing_mode="polygon",
    update_streamlit=True,
    key="roi_canvas",
)

if canvas.json_data:
    st.session_state.roi_mask = shapes_to_roi_mask(
        canvas.json_data, h, w
    )


# ---------- MANUAL EDIT ----------
st.subheader("2️⃣ Corrections manuelles RX (clic)")

col1, col2 = st.columns(2)

with col1:
    mode = st.radio(
        "Action",
        ["Ajouter Soudure (Jaune)", "Ajouter Void (Rouge)", "Supprimer"],
        horizontal=True
    )
    shape = st.radio("Forme", ["Disque", "Patatoïde"], horizontal=True)
    radius = st.slider("Rayon (px)", 3, 40, 10)

with col2:
    x = st.number_input("X (px)", 0, w-1, w//2)
    y = st.number_input("Y (px)", 0, h-1, h//2)
    if st.button("Appliquer la correction"):
        if st.session_state.roi_mask[y, x] == 0:
            st.warning("Point hors ROI – correction ignorée")
        else:
            if mode == "Ajouter Soudure (Jaune)":
                if shape == "Disque":
                    st.session_state.corr_mask = add_disk(
                        st.session_state.corr_mask, x, y, radius, 1
                    )
                else:
                    st.session_state.corr_mask = add_potato(
                        st.session_state.corr_mask, x, y,
                        radius, radius//2, 25, 1
                    )
            elif mode == "Ajouter Void (Rouge)":
                st.session_state.corr_mask = add_disk(
                    st.session_state.corr_mask, x, y, radius, 2
                )
            else:
                st.session_state.corr_mask = erase(
                    st.session_state.corr_mask, x, y, radius
                )

# ---------- OVERLAY ----------
st.subheader("3️⃣ Visualisation RX")

overlay = overlay_rx(img, st.session_state.roi_mask, st.session_state.corr_mask)
st.image(overlay, clamp=True)

# ---------- EXPORT ----------
st.subheader("4️⃣ Export")

def to_png(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()

roi_color = np.zeros((h, w, 3), dtype=np.uint8)
roi_color[st.session_state.roi_mask == 1] = (0, 255, 0)

corr_color = np.zeros((h, w, 3), dtype=np.uint8)
corr_color[st.session_state.corr_mask == 1] = (255, 255, 0)
corr_color[st.session_state.corr_mask == 2] = (255, 0, 0)

st.download_button(
    "Télécharger ROI_MASK.png",
    to_png(roi_color),
    file_name="roi_mask.png"
)

st.download_button(
    "Télécharger CORRECTION_MASK.png",
    to_png(corr_color),
    file_name="correction_mask.png"
)
