
import os

def remove_prefix(filepath, parent_dir):
    """
    Remove the parent_dir prefix from the filepath.
    """
    if filepath.startswith(parent_dir):
        filepath = filepath[len(parent_dir):]
    return filepath


def get_data_file_path(filename: str, check_exists: bool = True):
    # strip off ./data prefix if it is there
    target = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
    if check_exists and not os.path.exists(target):
        raise FileNotFoundError(f"File {target} not found")
    return target


def get_fixture_file_path(filename: str):
    # strip off ./fixtures prefix if it is there
    target = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures', filename)
    if not os.path.exists(target):
        raise FileNotFoundError(f"File {target} not found")
    return target