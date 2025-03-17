# Initialize utils package
import os
import shutil
import glob

def clear_data_files():
    """
    Clear all JSON files from app/data folder and all files from app/uploads folder.
    """
    # Clear JSON files from app/data
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    for json_file in glob.glob(os.path.join(data_dir, '*.json')):
        os.remove(json_file)
    
    # Clear all files from app/uploads
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    for file_path in os.listdir(upload_dir):
        if os.path.isfile(os.path.join(upload_dir, file_path)):
            os.remove(os.path.join(upload_dir, file_path))