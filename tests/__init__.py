
import os

def get_data_file_path(filename: str):
    # strip off ./data prefix if it is there
    if filename.startswith("./data"):
        filename = os.path.split(filename)[-1]
    target = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
    if not os.path.exists(target):
        raise FileNotFoundError(f"File {target} not found")
    return target
    