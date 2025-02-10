import os
import numpy as np



def euclidean_distance(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    return np.linalg.norm(vec1 - vec2)

def delete_if_empty(directory_path):
    if not os.listdir(directory_path):  # Check if directory is empty
        os.rmdir(directory_path)  # Remove directory
        print(f"Directory {directory_path} has been removed")
    else:
        print(f"Directory {directory_path} is not empty")


class SingletonBase:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonBase, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]