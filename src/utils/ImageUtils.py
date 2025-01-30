from PIL import Image
import numpy as np
from skimage.transform import resize


def ModifyImageForDicom(Path):
    image = Image.open(Path)
    array = np.array(image)
    resized_array = resize(array, (512, 512, 3), mode='reflect', anti_aliasing=True)
    combined_array = resized_array.mean(axis=2)  # Take the average of the 3 channels
    scaled_adjusted_array = (combined_array / combined_array.max() * 65534).astype(np.uint16)
    image = Image.fromarray(scaled_adjusted_array)
    return image


