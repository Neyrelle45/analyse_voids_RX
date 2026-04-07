import numpy as np
import cv2

def shapes_to_roi_mask(json_data, h, w):
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
