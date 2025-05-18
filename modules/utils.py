# utils.py


import os
import glob


def clear_frames_folder(folder="frames"):
    if not os.path.exists(folder):
        os.makedirs(folder)
        return
    for file in glob.glob(os.path.join(folder, "*.png")):
        os.remove(file)


def initialize_folders():
    os.makedirs("res", exist_ok=True)
    i = 0
    while os.path.exists("res/res" + str(i)):
        i += 1
    os.makedirs("res/res" + str(i), exist_ok=True)
    os.makedirs("res/res" + str(i) + "/frames", exist_ok=True)
    return "res/res" + str(i)
