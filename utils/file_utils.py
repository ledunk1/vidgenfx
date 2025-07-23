import os
import zipfile
import shutil
import math
import sys
from datetime import datetime

def get_absolute_path(relative_path):
    """Get absolute path, handling PyInstaller and different environments"""
    try:
        # Get the directory where the executable or script is located
        if getattr(sys, 'frozen', False):
            # If running from PyInstaller executable
            base_path = os.path.dirname(sys.executable)
        else:
            # Normal Python execution - get project root
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Combine with relative path
        full_path = os.path.join(base_path, relative_path)
        
        # Normalize path for Windows
        full_path = os.path.normpath(full_path)
        
        return full_path
        
    except Exception as e:
        print(f"Error resolving path {relative_path}: {e}")
        # Fallback to relative path
        return os.path.normpath(relative_path)

def create_zip_archive(folder_path, zip_name):
    """Create zip archive from folder"""
    try:
        # Ensure temp directory exists using absolute path
        temp_dir = get_absolute_path('temp')
        os.makedirs(temp_dir, exist_ok=True)
        zip_path = os.path.join(temp_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)
        return zip_path
    except Exception as e:
        print(f"Error creating zip: {e}")
        return None

def delete_file(file_path):
    """Delete a single file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False

def delete_folder_contents(folder_path):
    """Delete all contents of a folder"""
    try:
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting folder contents: {e}")
        return False

def delete_directory_tree(directory_path):
    """Delete entire directory tree"""
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting directory tree: {e}")
        return False

def get_file_list(folder_path):
    """Get list of files in folder with metadata"""
    files = []
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                try:
                    stat = os.stat(file_path)
                    files.append({
                        'name': filename,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Exception as e:
                    print(f"Error getting file stats for {filename}: {e}")
                    continue
    return files

def get_directory_size(directory_path):
    """Get total size of directory and all its contents"""
    total_size = 0
    file_count = 0
    
    if not os.path.exists(directory_path):
        return total_size, file_count
    
    try:
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except (OSError, IOError):
                    # Skip files that can't be accessed
                    continue
    except Exception as e:
        print(f"Error calculating directory size for {directory_path}: {e}")
    
    return total_size, file_count

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def cleanup_temp_files():
    """Clean up temporary files"""
    temp_dir = get_absolute_path('temp')
    if os.path.exists(temp_dir):
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    # Only delete files older than 1 hour
                    file_age = datetime.now().timestamp() - os.path.getmtime(file_path)
                    if file_age > 3600:  # 1 hour in seconds
                        os.remove(file_path)
                elif os.path.isdir(file_path):
                    # Delete old directories
                    dir_age = datetime.now().timestamp() - os.path.getmtime(file_path)
                    if dir_age > 3600:  # 1 hour in seconds
                        shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error cleaning temp files: {e}")

def ensure_directory_exists(directory_path):
    """Ensure directory exists, create if it doesn't"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def safe_filename(filename):
    """Make filename safe for filesystem"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename

def get_available_disk_space(path='.'):
    """Get available disk space in bytes"""
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path),
                ctypes.pointer(free_bytes),
                None,
                None
            )
            return free_bytes.value
        else:  # Unix/Linux/Mac
            statvfs = os.statvfs(path)
            return statvfs.f_frsize * statvfs.f_bavail
    except Exception as e:
        print(f"Error getting disk space: {e}")
        return 0