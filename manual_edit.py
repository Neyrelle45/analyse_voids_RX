import numpy as np
import cv2

YELLOW = 1  # soudure
RED = 2     # void

def add_disk(mask, x, y, radius, label):
    tmp = np.zeros_like(mask, dtype=np.uint8)
    cv2.circle(tmp, (x, y), radius, 1, -1)
    mask[tmp > 0] = label
    return mask

def add_potato(mask, x, y, rx, ry, angle, label):
    tmp = np.zeros_like(mask, dtype=np.uint8)
    cv2.ellipse(tmp, ((x, y), (rx*2, ry*2), angle), 1, -1)
    mask[tmp > 0] = label
    return mask

def erase(mask, x, y, radius):
    tmp = np.zeros_like(mask, dtype=np.uint8)
    cv2.circle(tmp, (x, y), radius, 1, -1)
    mask[tmp > 0] = 0
    return mask
