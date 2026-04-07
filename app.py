import io
import json
import numpy as np
import streamlit as st
from PIL import Image
import cv2

from streamlit_drawable_canvas import st_canvas

# =========================================================
# PARAMÈTRES GÉNÉRAUX
# =========================================================
st.set_page_config(
    page_title="RX Void Analyzer – ROI & Corrections",
    layout="wide"
)

st.title("RX Void Analyzer – Canvas RX (ROI + corrections manuelles)")

# =========================================================
# UTILS
# =========================================================
def shapes_to_roi_mask(json_data, h, w):
    """Convertit des polygones canvas en masque ROI binaire"""
    mask = np.zeros((h, w), dtype=np.uint8)

    if not json_data or "objects" not in json_data:
        return mask

    for obj in json_data["objects"]:
        if obj["type"] == "polygon":
            pts = np.array(
                [[int(p["x"] + obj["left"]), int(p["y"] + obj["top"])]
                 for p in obj["points"]],
                dtype=np.int32
            )
            cv2.fillPoly(mask, [pts], 1)

    return mask


def overlay_rx(img_rgb, roi_mask, corr_mask, alpha=0.35):
    """Overlay RX : ROI vert, corrections jaune/rouge"""
    out = img_rgb.copy()

    # ROI (vert)
    out[roi_mask == 1] = (0, 255, 0)

    # Corrections
    out[corr_mask == 1] = (255, 255, 0)  # soudure
    out[corr_mask == 2] = (255, 0, 0)    # void

    return out


def add_disk(mask, x, y, r, label):
    tmp = np.zeros_like(mask, dtype=np.uint8)
    cv2.circle(tmp, (x, y), r, 1, -1)
    mask[tmp > 0] = label
    return mask


def add_potato(mask, x, y, rx, ry, angle, label):
    tmp = np.zeros_like(mask, dtype=np.uint8)
    cv2.ellipse(tmp, ((x, y), (rx*2, ry*2), angle), 1, -1)
    mask[tmp > 0] = label
    return mask


def erase(mask, x, y, r):
    tmp = np.zeros_like(mask, dtype=np.uint8)
    cv2.circle(tmp, (x, y), r, 1, -1)
    mask[tmp > 0] = 0
    return mask


def to_png(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


# =========================================================
# CHARGEMENT IMAGE RX
# =========================================================
uploaded = st.file_uploader("Image RX (.png / .jpg)", type=["png", "jpg", "jpeg"])
if not uploaded:
    st.stop()

img_pil = Image.open(uploaded).convert("RGB")
img = np.array(img_pil)
h, w = img.shape[:2]

# Session state
if "roi_mask" not in st.session_state:
    st.session_state.roi_mask = np.zeros((h, w), dtype=np.uint8)

if "corr_mask" not in st.session_state:
    st.session_state.corr_mask = np.zeros((h, w), dtype=np.uint8)

# =========================================================
# 1️⃣ CANVAS ROI (POLYGONES SUR IMAGE RX)
# =========================================================
st.subheader("1️⃣ Définition des ROI (polygones)")

canvas_roi = st_canvas(
    fill_color="rgba(0,255,0,0.35)",
    stroke_width=2,
    stroke_color="rgba(0,255,0,1)",
    background_image=img_pil,   # ✅ SUPERPOSITION RÉELLE
    height=h,
    width=w,
    drawing_mode="polygon",
    update_streamlit=True,
    key="canvas_roi",
)

if canvas_roi.json_data:
    st.session_state.roi_mask = shapes_to_roi_mask(
        canvas_roi.json_data, h, w
    )

# =========================================================
# 2️⃣ CORRECTIONS MANUELLES RX (CLICK-BASED)
# =========================================================
st.subheader("2️⃣ Corrections manuelles RX (clic disque / patatoïde)")

col1, col2 = st.columns(2)

with col1:
    action = st.radio(
        "Action",
        ["Ajouter Soudure (Jaune)", "Ajouter Void (Rouge)", "Supprimer"],
        horizontal=True
    )
    shape = st.radio("Forme", ["Disque", "Patatoïde"], horizontal=True)
    radius = st.slider("Rayon (px)", 3, 40, 12)

with col2:
    x = st.number_input("X (px)", 0, w-1, w//2)
    y = st.number_input("Y (px)", 0, h-1, h//2)

    if st.button("Appliquer la correction"):
        if st.session_state.roi_mask[y, x] == 0:
            st.warning("Correction hors ROI ignorée")
        else:
            if action == "Ajouter Soudure (Jaune)":
                if shape == "Disque":
                    st.session_state.corr_mask = add_disk(
                        st.session_state.corr_mask, x, y, radius, 1
                    )
                else:
                    st.session_state.corr_mask = add_potato(
                        st.session_state.corr_mask,
                        x, y,
                        radius, radius // 2,
                        angle=20,
                        label=1
                    )

            elif action == "Ajouter Void (Rouge)":
                st.session_state.corr_mask = add_disk(
                    st.session_state.corr_mask, x, y, radius, 2
                )

            else:
                st.session_state.corr_mask = erase(
                    st.session_state.corr_mask, x, y, radius
                )

# =========================================================
# 3️⃣ VISUALISATION RX
# =========================================================
st.subheader("3️⃣ Visualisation RX (overlay)")

overlay = overlay_rx(
    img,
    st.session_state.roi_mask,
    st.session_state.corr_mask
)

st.image(overlay, clamp=True)

# =========================================================
# 4️⃣ EXPORT DES MASQUES
# =========================================================
st.subheader("4️⃣ Export des masques")

roi_color = np.zeros((h, w, 3), dtype=np.uint8)
roi_color[st.session_state.roi_mask == 1] = (0, 255, 0)

corr_color = np.zeros((h, w, 3), dtype=np.uint8)
corr_color[st.session_state.corr_mask == 1] = (255, 255, 0)
corr_color[st.session_state.corr_mask == 2] = (255, 0, 0)

st.download_button(
    "⬇️ Télécharger ROI_MASK.png",
    to_png(roi_color),
    file_name="ROI_MASK.png"
)

st.download_button(
    "⬇️ Télécharger CORRECTION_MASK.png",
    to_png(corr_color),
    file_name="CORRECTION_MASK.png"
)
