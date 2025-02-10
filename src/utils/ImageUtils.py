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





import numpy as np

def reshape_to_HW_slices(first_array, second_array):
    """
    Reshapes the second array (any permutation of H, W, slices) into (H, W, slices),
    using the first array to determine H and W.

    Parameters:
        first_array (np.ndarray): Fixed array of shape (H, W).
        second_array (np.ndarray): Array with any permutation of (H, W, slices).

    Returns:
        np.ndarray: Reshaped array of shape (H, W, slices).
    """
    H, W = first_array.shape  # Extract correct H, W
    print(f"First array shape (H, W): ({H}, {W})")  # Log the shape of first_array

    shape = second_array.shape  # Current shape of the second array
    print(f"Second array shape before rearranging: {shape}")  # Log the original shape of second_array
    
    if H==shape[0] and W ==shape[1]:
        return second_array


    # Find the indices of H and W in second_array's shape
    idx_H = shape.index(H)
    idx_W = shape.index(W)
    print(f"Index of H in second array: {idx_H}, Index of W in second array: {idx_W}")  # Log indices of H and W

    # The remaining dimension is slices
    idx_slices = list({0, 1, 2} - {idx_H, idx_W})[0]
    print(f"Index of slices in second array: {idx_slices}")  # Log index of slices

    # Rearrange the axes correctly
    arr_fixed = np.transpose(second_array, (idx_H, idx_W, idx_slices))
    print(f"Second array shape after rearranging: {arr_fixed.shape}")  # Log the final reshaped array shape

    return arr_fixed


