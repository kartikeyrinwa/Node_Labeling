import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
from skimage.morphology import flood, flood_fill
import skimage as ski


img = Image.open("../data/chicago/Chicago_neighborhoods_map.png")

new_img = ski.util.img_as_uint(img)

print("Image shape: ", new_img.shape)

rgb_image = new_img[:, :, :3]

seed = (800, 1000)

gray_image = ski.color.rgb2gray(rgb_image)

mask = flood(gray_image, seed)