import os
import shutil

def organize_downloads():
    # Define the path to the Downloads folder
    downloads_folder = os.path.expanduser("~/Downloads")
    
    print(f"Organizing: {downloads_folder}")
    print(f"Files found: {os.listdir(downloads_folder)}")
    
    # Define the target folders for different file types
    target_folders = {
        'Documents': ['.pdf', '.docx', '.txt', '.xlsx'],
        'Images': ['.jpg', '.jpeg', '.png', '.gif'],
        'Videos': ['.mp4', '.mov', '.avi'],
        'Music': ['.mp3', '.wav', '.flac'],
        'Archives': ['.zip', '.rar', '.tar.gz']
    }
    
    # Create target folders if they don't exist
    for folder in target_folders.keys():
        target_path = os.path.join(downloads_folder, folder)
        os.makedirs(target_path, exist_ok=True)
        print(f"Created/verified folder: {target_path}")
    
    # Move files to their respective folders
    for filename in os.listdir(downloads_folder):
        file_path = os.path.join(downloads_folder, filename)
        
        # Skip directories and the script file itself
        if os.path.isdir(file_path) or filename == 'file_organizer.py':
            continue
        
        # Get the file extension
        _, file_extension = os.path.splitext(filename)
        
        # Move the file to the appropriate folder
        moved = False
        for folder, extensions in target_folders.items():
            if file_extension.lower() in extensions:
                destination = os.path.join(downloads_folder, folder, filename)
                shutil.move(file_path, destination)
                print(f"Moved: {filename} → {folder}")
                moved = True
                break
        
        # Unknown file types go to Others
        if not moved:
            others_folder = os.path.join(downloads_folder, 'Others')
            os.makedirs(others_folder, exist_ok=True)
            shutil.move(file_path, os.path.join(others_folder, filename))
            print(f"Moved: {filename} → Others")

organize_downloads()