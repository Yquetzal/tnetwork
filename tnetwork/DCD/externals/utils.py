import os

def clean_create_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)

    filelist = [f for f in os.listdir(dir)]
    for f in filelist:
        os.remove(os.path.join(dir, f))

def clear_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

