"""
Image Augmentation Pipeline.
Simulates realistic real-world Indian restaurant/canteen bills:
- Bad lighting / uneven shadows
- Crumpled paper folds and geometric distortions
- Camera shake / defocus blur
- Slight camera rotations and perspective tilts
"""

import os
import random


import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2

def add_crumple_and_fold(image: Image.Image) -> Image.Image:
    """Simulates paper folds and creases with gradient shadow bands."""
    img_arr = np.array(image).astype(np.float32)
    h, w = img_arr.shape[:2]



    # Create 1 to 3 random shadow bands (folds)
    num_folds = random.randint(1, 3)
    shadow_mask = np.ones((h, w), dtype=np.float32)

    for _ in range(num_folds):
        y = random.randint(int(h * 0.1), int(h * 0.9))
        thickness = random.randint(15, 45)
        intensity = random.uniform(0.65, 0.88)
        y_min = max(0, y - thickness)
        y_max = min(h, y + thickness)
        for i in range(y_min, y_max):
            dist = abs(i - y) / thickness
            factor = intensity + (1.0 - intensity) * dist
            shadow_mask[i, :] *= factor

    if len(img_arr.shape) == 3:
        shadow_mask = np.expand_dims(shadow_mask, axis=2)

    img_arr = np.clip(img_arr * shadow_mask, 0, 255).astype(np.uint8)
    return Image.fromarray(img_arr)



def apply_perspective_tilt(image: Image.Image) -> Image.Image:
    """Applies slight perspective warping (taking photo from angle)."""
    img_arr = np.array(image)
    h, w = img_arr.shape[:2]

    delta = random.randint(10, 30)
    pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    pts2 = np.float32([
        [random.randint(0, delta), random.randint(0, delta)],
        [w - random.randint(0, delta), random.randint(0, delta)],
        [random.randint(0, delta), h - random.randint(0, delta)],
        [w - random.randint(0, delta), h - random.randint(0, delta)]
    ])




    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(img_arr, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(warped)

def augment_receipt_image(image: Image.Image) -> Image.Image:
    """
    Complete augmentation pipeline simulating difficult mobile capture conditions.
    """
    # 1. Random rotation (-6 to +6 degrees)
    angle = random.uniform(-6.0, 6.0)
    image = image.rotate(angle, resample=Image.Resampling.BILINEAR, expand=False, fillcolor=(255, 255, 255))



    # 2. Random perspective warp (60% probability)
    if random.random() < 0.6:
        image = apply_perspective_tilt(image)



    # 3. Crumple fold shadows (70% probability)
    if random.random() < 0.7:
        image = add_crumple_and_fold(image)

    # 4. Lighting & contrast variations
    enhancer_bright = ImageEnhance.Brightness(image)

    image = enhancer_bright.enhance(random.uniform(0.75, 1.25))

    enhancer_contrast = ImageEnhance.Contrast(image)
    image = enhancer_contrast.enhance(random.uniform(0.8, 1.3))



    # 5. Defocus blur or slight noise (camera shake)
    if random.random() < 0.4:


        image = image.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.2)))

    return image

if __name__ == "__main__":
    sample_img_path = "ml/data/processed/images/receipt_00000.jpg"
    if os.path.exists(sample_img_path):

        orig = Image.open(sample_img_path)

        aug = augment_receipt_image(orig)


        out_dir = "ml/data/processed/augmented_preview"
        os.makedirs(out_dir, exist_ok=True)

        aug.save(os.path.join(out_dir, "augmented_00000.jpg"))

        print(f"Sample augmented receipt saved to {out_dir}/augmented_00000.jpg")
    else:





        
        print("Run prepare_cord_indianized.py first to generate sample images.")
