# File Organizer Script (MintOS)

A simple Python script that automatically sorts files in your Downloads folder into categorized subfolders based on file type.

## What it does

Downloads folders get messy fast. This script scans your Downloads directory and moves each file into a matching subfolder based on its extension, so PDFs land in Documents, images land in Images, and so on.

## Folder categories

- **Documents**: .pdf, .docx, .txt, .xlsx
- **Images**: .jpg, .jpeg, .png, .gif
- **Videos**: .mp4, .mov, .avi
- **Music**: .mp3, .wav, .flac
- **Archives**: .zip, .rar, .tar.gz
- **Others**: anything that doesn't match the categories above

Target folders are created automatically the first time the script runs, if they don't already exist.

## Requirements

- Python 3
- No external dependencies. The script only uses `os` and `shutil`, both part of Python's standard library.

## How to run it

1. Clone or download this repository.
2. Open a terminal and navigate to the folder containing `file_organizer.py`.
3. Run:

```bash
python3 file_organizer.py
```

The script scans your Downloads folder, creates the category subfolders if needed, and moves each file into the right place. It prints out what it's doing as it goes, so you can see exactly which files moved where.

## Notes

- The script runs manually right now. It does not watch the Downloads folder in real time, so it needs to be run by hand whenever you want files organized.
- It skips directories, and skips itself if the script happens to be sitting in Downloads when run.
- This was also my first project pushed to GitHub, so getting comfortable with git basics like init, add, commit, and push was part of the process.

## Possible future improvements

- Add a config file so folder categories and extensions can be customized without editing the script directly.
- Add real-time monitoring so files get sorted the moment they're downloaded instead of needing a manual run; might consider using a tool like `inotifywait` or Python's `watchdog` library.
- Add a `--dry-run` flag to preview what would move without actually moving anything.
