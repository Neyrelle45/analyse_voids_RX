import numpy as np

def overlay_rx(img_rgb, roi_mask, corr_mask, alpha=0.35):
    out = img_rgb.copy()

    # ROI en vert
    out[roi_mask == 1] = (0, 255, 0)

    # Corrections
    out[corr_mask == 1] = (255, 255, 0)  # jaune
    out[corr_mask == 2] = (255, 0, 0)    # rouge

    return out
