#!/usr/bin/env python3
"""Organize Downloads and report duplicates (Python 3.10+, Linux).

    python3 file_organizer.py                 # Preview; changes nothing
    python3 file_organizer.py --apply         # Organize loose files
    python3 file_organizer.py --duplicates    # Read-only file/folder report
    python3 file_organizer.py --folder /path  # Preview another folder

Existing folders remain intact. Duplicate scans include subfolders but never
delete or move anything. No extra packages are required. Moves use hard links
followed by unlinking the original name, preventing overwrites without making
an extra copy on a full disk. Categories must support hard links on the same
filesystem as the source. Unsupported moves fail and retain the original.
"""

import argparse
import hashlib
import json
import os
import stat
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = {
    "Documents": (".pdf", ".doc", ".docx", ".odt", ".txt", ".md", ".rtf",
                  ".xls", ".xlsx", ".ods", ".csv", ".tsv", ".ppt", ".pptx",
                  ".odp", ".epub"),
    "Images": (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp",
               ".tif", ".tiff", ".avif", ".heic", ".ico"),
    "Videos": (".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mpeg",
               ".mpg", ".wmv"),
    "Music": (".mp3", ".wav", ".flac", ".ogg", ".opus", ".aac", ".m4a",
              ".wma", ".aiff"),
    "Archives": (".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst", ".zip",
                 ".rar", ".7z", ".tar", ".tgz", ".tbz2", ".txz", ".gz",
                 ".bz2", ".xz", ".zst"),
}
EXTENSIONS = sorted(
    ((extension, category) for category, extensions in CATEGORIES.items()
     for extension in extensions), key=lambda pair: len(pair[0]), reverse=True,
)
UNFINISHED = (".part", ".partial", ".crdownload", ".download", ".tmp",
              ".temp", ".swp", ".swx")
SCRIPT = Path(__file__).resolve()


def label(path, root):
    """Quote paths to display spaces and control characters unambiguously."""
    return repr(str(path.relative_to(root)))


def human_size(size):
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024


def content_signature(info):
    # A move using hard links changes ctime/link count, but not these fields.
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns)


def signature(info):
    return content_signature(info) + (info.st_ctime_ns,)


def skip_reason(path):
    if path.is_symlink():
        return "symbolic link"
    if path.name.startswith("."):
        return "hidden entry"
    if path.name.lower().endswith(UNFINISHED):
        return "unfinished/temporary entry"
    if path == SCRIPT or path.name == "file_organizer.py":
        return "organizer script"
    return None


def category_for(filename):
    return next((category for extension, category in EXTENSIONS
                 if filename.lower().endswith(extension)), "Others")


def unused_destination(path, reserved):
    """Keep both files, using 'name (2).ext' when a name is already taken."""
    suffix = next((extension for extension, _ in EXTENSIONS
                   if path.name.lower().endswith(extension)), path.suffix)
    suffix = path.name[-len(suffix):] if suffix else ""  # Preserve capitalization.
    stem = path.name[:-len(suffix)] if suffix else path.name
    candidate, number = path, 2
    while os.path.lexists(candidate) or candidate in reserved:
        candidate = path.with_name(f"{stem} ({number}){suffix}")
        number += 1
    return candidate


@dataclass
class Move:
    source: Path
    destination: Path
    original: os.stat_result


def plan_moves(root):
    moves, skipped, errors, reserved = [], [], [], set()
    for source in sorted(root.iterdir()):
        try:
            reason = skip_reason(source)
            if reason:
                skipped.append(f"{label(source, root)}: {reason}")
                continue
            info = source.lstat()
            if stat.S_ISDIR(info.st_mode):
                continue  # Do not split up existing project or category folders.
            if not stat.S_ISREG(info.st_mode):
                skipped.append(f"{label(source, root)}: not a regular file")
                continue
            category = root / category_for(source.name)
            if os.path.lexists(category) and not stat.S_ISDIR(category.lstat().st_mode):
                raise OSError(f"category {category.name!r} is not a real directory")
            destination = unused_destination(category / source.name, reserved)
            reserved.add(destination)
            moves.append(Move(source, destination, info))
        except OSError as error:
            errors.append(f"{label(source, root)}: {error}")
    return moves, skipped, errors


def move_without_overwriting(move):
    """Move on Linux without overwriting a destination or copying file data."""
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root_fd = os.open(move.source.parent, directory_flags)
    category_fd = None
    try:
        category_name = move.destination.parent.name
        try:
            os.mkdir(category_name, dir_fd=root_fd)
        except FileExistsError:
            pass
        # Recheck the category when applying: never follow a category symlink.
        category_fd = os.open(category_name, directory_flags, dir_fd=root_fd)
        current = os.stat(move.source.name, dir_fd=root_fd, follow_symlinks=False)
        expected = content_signature(move.original)
        if content_signature(current) != expected:
            raise OSError("source changed since the preview; run the preview again")
        destination = move.destination
        while True:
            try:
                os.link(move.source.name, destination.name,
                        src_dir_fd=root_fd, dst_dir_fd=category_fd,
                        follow_symlinks=False)
                break
            except FileExistsError:
                destination = unused_destination(
                    move.destination.parent / move.source.name, set())
        linked = os.stat(destination.name, dir_fd=category_fd, follow_symlinks=False)
        current = os.stat(move.source.name, dir_fd=root_fd, follow_symlinks=False)
        if content_signature(linked) != expected or content_signature(current) != expected:
            raise OSError("source changed during the move; original retained; "
                          f"inspect possible extra link {str(destination)!r}")
        os.unlink(move.source.name, dir_fd=root_fd)
        return destination
    finally:
        if category_fd is not None:
            os.close(category_fd)
        os.close(root_fd)


def show_notes(skipped, errors):
    if skipped:
        print(f"\nSkipped {len(skipped)} entries:")
        for message in skipped[:20]:
            print(f"  {message}")
        if len(skipped) > 20:
            print(f"  ... and {len(skipped) - 20} more")
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)


def organize(root, apply):
    moves, skipped, errors = plan_moves(root)
    print("MOVE PLAN" if apply else "PREVIEW — nothing will be changed")
    for move in moves:
        print(f"  {label(move.source, root)} -> {label(move.destination, root)}")
    total = sum(move.original.st_size for move in moves)
    print(f"\n{len(moves)} loose files to organize ({human_size(total)}).")
    if apply:
        moved = 0
        for move in moves:
            try:
                destination = move_without_overwriting(move)
                print(f"MOVED: {label(move.source, root)} -> {label(destination, root)}")
                moved += 1
            except OSError as error:
                errors.append(f"{label(move.source, root)}: {error}")
        print(f"\nMoved {moved}/{len(moves)} files. Existing folders kept intact.")
    else:
        print("Run with --apply to perform these moves.")
    print("Organizing does not free disk space. Use --duplicates for a read-only report.")
    show_notes(skipped, errors)
    return 1 if errors else 0


def hash_file(path, cache):
    """Hash stable regular files; never follow a symlink or block on a FIFO."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise OSError("not a regular file")
        key = signature(before)
        if key not in cache:
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
            if signature(os.fstat(stream.fileno())) != key:
                raise OSError("file changed while being read")
            cache[key] = digest.hexdigest()
        if signature(path.lstat()) != key:
            raise OSError("file changed while being read")
        return cache[key], before


def duplicate_report(root):
    files, folders, cache = defaultdict(list), defaultdict(list), {}
    skipped, errors = [], []
    scanned_files = 0

    def scan(directory):
        """A folder matches only when every entry is scanned successfully."""
        nonlocal scanned_files
        records, complete, count, size = [], True, 0, 0
        try:
            before = directory.lstat()
            if not stat.S_ISDIR(before.st_mode):
                raise OSError("directory changed or became a symbolic link")
            children = sorted(directory.iterdir())
        except OSError as error:
            errors.append(f"{label(directory, root)}: {error}")
            return None, 0, 0
        for child in children:
            try:
                reason = skip_reason(child)
                if reason:
                    skipped.append(f"{label(child, root)}: {reason}")
                    complete = False
                    continue
                info = child.lstat()
                if stat.S_ISDIR(info.st_mode):
                    digest, child_count, child_size = scan(child)
                    if digest is None:
                        complete = False
                    else:
                        records.append(("directory", child.name, digest))
                        count += child_count
                        size += child_size
                elif stat.S_ISREG(info.st_mode):
                    digest, info = hash_file(child, cache)
                    records.append(("file", child.name, info.st_size, digest))
                    files[(info.st_size, digest)].append(
                        (child, (info.st_dev, info.st_ino)))
                    count += 1
                    size += info.st_size
                    scanned_files += 1
                    if scanned_files % 100 == 0:
                        print(f"Scanned {scanned_files} files...", file=sys.stderr, flush=True)
                else:
                    skipped.append(f"{label(child, root)}: not a regular file/directory")
                    complete = False
            except OSError as error:
                errors.append(f"{label(child, root)}: {error}")
                complete = False
        try:
            if signature(directory.lstat()) != signature(before):
                errors.append(f"{label(directory, root)}: directory changed during scan")
                complete = False
        except OSError as error:
            errors.append(f"{label(directory, root)}: {error}")
            complete = False
        if not complete:
            return None, count, size
        digest = hashlib.sha256(json.dumps(records, ensure_ascii=True,
                               separators=(",", ":")).encode("utf-8")).hexdigest()
        # Empty directories contribute to a parent's structure but are not
        # listed separately as duplicates worth clearing for storage space.
        if directory != root and count:
            folders[digest].append((directory, count, size))
        return digest, count, size

    print("DUPLICATE REPORT — read only; scanning file contents...", flush=True)
    scan(root)
    file_groups, aliases = 0, 0
    print("\nMatching files (SHA-256 contents, regardless of filename):")
    for (size, _), entries in sorted(files.items()):
        distinct = {}
        for path, inode in entries:
            if inode in distinct:
                aliases += 1
            else:
                distinct[inode] = path
        if len(distinct) < 2:
            continue
        file_groups += 1
        print(f"  Group {file_groups}: {len(distinct)} files, {human_size(size)} each")
        for path in distinct.values():
            print(f"    {label(path, root)}")
    if not file_groups:
        print("  None found among successfully scanned files.")
    folder_groups = 0
    print("\nMatching folders (relative names, structure, and file contents):")
    for entries in folders.values():
        if len(entries) < 2:
            continue
        folder_groups += 1
        _, count, size = entries[0]
        print(f"  Group {folder_groups}: {count} files, {human_size(size)} per folder")
        for path, _, _ in entries:
            print(f"    {label(path, root)}")
    if not folder_groups:
        print("  None found among completely scanned nonempty folders.")
    print(f"\nScanned {scanned_files} files. Found {file_groups} file groups and "
          f"{folder_groups} folder groups.")
    if aliases:
        print(f"Ignored {aliases} additional hard-link names in file groups; "
              "they already share storage.")
    print("No files or folders were changed. Folder matches ignore permissions and dates.")
    print("Folders with skipped/unreadable entries are excluded from folder matching.")
    print("Groups can overlap; their sizes are not a total of reclaimable disk space.")
    show_notes(skipped, errors)
    return 1 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Preview Downloads organization, apply it, or report duplicates.",
        epilog="Default: preview only. Duplicate reports never delete anything.")
    parser.add_argument("--folder", type=Path, default=Path.home() / "Downloads",
                        help="folder to organize/scan (default: ~/Downloads)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="perform the previewed file moves")
    mode.add_argument("--duplicates", action="store_true", help="read-only recursive duplicate report")
    args = parser.parse_args(argv)
    try:
        root = args.folder.expanduser().resolve(strict=True)
        if not root.is_dir():
            parser.error("--folder must be an existing directory")
        print(f"Folder: {str(root)!r}")
        return duplicate_report(root) if args.duplicates else organize(root, args.apply)
    except (OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped. Review the output for any moves already completed.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
