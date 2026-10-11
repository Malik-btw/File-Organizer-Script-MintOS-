# File Organizer for Linux

A preview-first Python command-line utility that organizes loose files and
reports duplicate files and folders without automatically deleting anything.

I started this project while learning Python, Linux, and Git. The first version
was a small extension-based organizer for my Downloads folder. I later revisited
it as an experiment in AI-assisted development: I wanted to see how well
"vibe coding" could work on a real utility when paired with deliberate review
and testing.

## What it does

- Previews planned moves before changing files.
- Sorts loose files into category folders inside Downloads.
- Keeps existing project folders intact.
- Preserves both files when destination names conflict.
- Recognizes common document, image, video, audio, and archive formats.
- Handles compound extensions such as `.tar.gz`.
- Reports duplicate files by comparing SHA-256 content hashes.
- Reports folders with matching relative names, structure, and contents.
- Skips hidden entries, symbolic links, temporary downloads, and the script
  itself.
- Uses only the Python standard library.

## Quick start

### Requirements

- Linux
- Python 3.10 or newer

Clone the repository and enter its directory:

```bash
git clone https://github.com/Malik-btw/File-Organizer-Script-MintOS-.git
cd File-Organizer-Script-MintOS-
```

Preview how loose files in `~/Downloads` would be organized:

```bash
python3 file_organizer.py
```

Review the preview, then apply the moves:

```bash
python3 file_organizer.py --apply
```

Generate a read-only duplicate report:

```bash
python3 file_organizer.py --duplicates
```

Use a different folder:

```bash
python3 file_organizer.py --folder "/path/to/folder"
python3 file_organizer.py --folder "/path/to/folder" --duplicates
```

View every available option:

```bash
python3 file_organizer.py --help
```

## Categories

| Folder | Examples |
| --- | --- |
| `Documents` | PDF, DOCX, TXT, Markdown, spreadsheets, presentations, CSV, EPUB |
| `Images` | JPG, PNG, GIF, WebP, SVG, TIFF, HEIC, AVIF |
| `Videos` | MP4, MOV, AVI, MKV, WebM, MPEG, WMV |
| `Music` | MP3, WAV, FLAC, OGG, Opus, AAC, M4A |
| `Archives` | ZIP, RAR, 7Z, TAR, TAR.GZ, TAR.XZ, GZ, Zstandard |
| `Others` | Files that do not match another category |

## Safety behavior

Running the script without an action flag creates a preview and makes no
changes. Duplicate scans are also read-only; the script never chooses which
copy to delete.

When `--apply` is used, the script creates a hard link at the destination,
verifies the source and destination, and then removes the original directory
entry. This approach prevents accidental overwrites and avoids creating a
second full copy on a nearly full drive. Because it relies on Linux filesystem
features, the source and category folders must support hard links on the same
filesystem.

If a destination name already exists, the script keeps both files and chooses
a name such as `report (2).pdf`. Existing directories are left in place so
projects are not split apart.

Duplicate folder groups can overlap, so their displayed sizes should not be
added together as an estimate of recoverable space. Review every reported group
before removing files manually.

## AI-assisted development disclosure

This repository is intentionally open about its use of generative AI.

I wrote the original organizer as an early Python and Linux project. For the
current revision, curiosity led me to test "vibe coding" with GPT-6 Astra. I
defined the desired behavior and safety requirements, and the model contributed
substantial implementation and refactoring work.

I did not treat generated code as automatically correct. I read through and
audited the revised script, compared its behavior with my requirements, ran it
in preview mode, exercised its organization and duplicate-reporting paths, and
reviewed how it handled filename collisions, symbolic links, temporary files,
and existing folders. I was impressed by what GPT-6 Astra produced, especially
the jump from a basic sorting script to a more defensive command-line utility.

This experiment also reinforced a practical lesson: AI can accelerate
implementation, but the developer still owns the requirements, review,
validation, and consequences of running the code. I am publishing the project
as both a useful tool and an honest record of that learning process.

## What I learned

- How to turn a one-purpose script into a command-line utility with explicit
  preview and apply modes.
- Why filesystem automation needs collision handling and repeated checks before
  modifying user data.
- How content hashing differs from comparing filenames.
- How Git fetch, rebase, commit, and push fit into a normal update workflow.
- How to review AI-generated code instead of relying on it blindly.

## Current limitations

- File categories are defined in the source code rather than a configuration
  file.
- The script is designed for Linux and depends on same-filesystem hard links
  when applying moves.
- Duplicate detection hashes file contents, so a large directory may take time
  to scan.
- Duplicate reports require manual review and cleanup.

## Possible next steps

- Move category definitions into a user-editable configuration file.
- Add an export option for duplicate reports.
- Add automated tests to the repository.
- Package the utility so it can be installed and run as a normal shell command.

## License

No license has been added yet. Until one is selected, the code remains under
standard copyright protection.
