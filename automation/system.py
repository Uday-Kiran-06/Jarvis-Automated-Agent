import os
import shutil
import glob

def organize_directory(directory_path):
    """Organizes files in a directory by moving them into subfolders based on extension."""
    if not os.path.exists(directory_path):
        return f"Error: Directory {directory_path} does not exist."

    files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    
    moved_count = 0
    for file in files:
        name, ext = os.path.splitext(file)
        ext = ext[1:].lower() if ext else "no_extension"
        
        target_folder = os.path.join(directory_path, ext)
        os.makedirs(target_folder, exist_ok=True)
        
        shutil.move(os.path.join(directory_path, file), os.path.join(target_folder, file))
        moved_count += 1
        
    return f"Successfully organized {moved_count} files into {len(set([os.path.splitext(f)[1] for f in files]))} categories."

def search_files(directory, pattern):
    """Searches for files matching a pattern in a directory recursively."""
    search_path = os.path.join(directory, "**", pattern)
    results = glob.glob(search_path, recursive=True)
    return results if results else "No files found matching the pattern."

def get_directory_summary(directory):
    """Returns a summary of the directory contents (size, count)."""
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(directory):
        for f in files:
            fp = os.path.join(root, f)
            total_size += os.path.getsize(fp)
            file_count += 1
            
    return {
        "directory": directory,
        "total_files": file_count,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }
