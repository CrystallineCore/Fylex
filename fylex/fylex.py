#HAPPY
import os
import re
import sys
import pathlib
import xxhash  # For fast non-cryptographic hashing of files
import shutil  # For high-level file operations like copy and move
import datetime
import threading
import logging
import fnmatch  # For Unix-style filename pattern matching
from concurrent.futures import ThreadPoolExecutor, as_completed
from .exceptions import InvalidPathError, PermissionDeniedError

# A thread-safe lock to prevent garbled output when multiple threads are logging or prompting the user.
_io_lock = threading.Lock()

# A dictionary of file extensions and names categorized as "junk" or temporary.
# This can be used to exclude these files from operations.
JUNK_EXTENSIONS = {
    "fylex_artifacts": [
        ".fylex_deprecated", # For the directory itself
        ".fylex_quarantine",
        "fylex.deprecated" # For the specific folder created in no_change()
    ],
    "temporary_backup": [
        ".tmp", ".temp", ".bak", ".backup", ".bkp", ".old", ".orig", ".save", "~"
    ],
    "system_log": [
        ".log", ".dmp", ".mdmp", ".hdmp", ".ds_store", ".lnk", "thumbs.db",
        "desktop.ini"
    ],
    "dev_artifacts": [
        ".class", ".o", ".obj", ".pyc", ".pyo", ".pyd", ".elc",
        ".egg", ".egg-info", ".whl", ".map", ".coverage", ".gcda", ".gcno",
        ".aux", ".out", ".toc", ".synctex.gz"
    ],
    "platform_trash": [
        ".Trash", ".Trashes", ".Spotlight-V100", ".AppleDouble", ".fseventsd",
        ".apdisk", "ehthumbs.db", ".TemporaryItems", ".DocumentRevisions-V100"
    ],
    "browser_cache": [
        ".cache", ".cached", ".part", ".crdownload", ".download"
    ],
    "editor_ide_junk": [
        ".suo", ".user", ".ncb", ".sdf", ".dbmdl", ".project", ".classpath",
        ".sublime-workspace", ".idea", ".vscode"
    ],
    "ci_cd_test": [
        ".test", ".tmp", ".out", ".stackdump"
    ],
    "document_temp": [
        ".wbk", ".asd", ".tmp", ".~lock"
    ]
}

# --- Constants ---
MAX_RETRIES = 5  # Maximum number of times to retry a failed file operation.
ON_CONFLICT_MODES = ["larger", "smaller", "newer", "older", "rename", "skip", "prompt", "replace"]

# -------- Logger Setup --------
class PrintToLogger:
    """
    A file-like object that redirects stdout to the logging module.
    This allows capturing print statements from other libraries or parts of the code
    and routing them through the configured logger.
    """
    def __init__(self, verbose):
        self.verbose = verbose

    def write(self, msg):
        msg = msg.strip()
        if msg:
            logging.info(msg)
            # If verbose mode is on, also write to the actual standard output.
            if self.verbose:
                sys.__stdout__.write(msg + "\n")
                sys.__stdout__.flush()

    def flush(self):
        # This method is required for file-like objects.
        pass

# -------- Hashing --------
def hash_file(path):
    """
    Computes the xxHash64 hash of a file for fast and reliable identification.
    Reads the file in chunks to handle large files efficiently.
    """
    hasher = xxhash.xxh64()
    with open(path, "rb") as f:
        # Read the file in 64KB chunks
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# -------- Handle renames --------
def handle_rename(src_file, dest_path, src_name, dry_run, is_move):
    base, ext = os.path.splitext(src_name)
    for i in range(1, 1000):
        new_name = f"{base}({i}){ext}"
        new_path = dest_path / new_name
        if not new_path.exists():
            if dry_run:
                with _io_lock:
                    if is_move:
                        logging.info(f"[DRY RUN] Would rename and move to: {new_path}")
                    else:
                        logging.info(f"[DRY RUN] Would rename and copy to: {new_path}")
            else:
                with _io_lock:
                    if is_move:
                        logging.info(f"Renamed and moved to avoid conflict: {src_file.name} -> {new_name}")
                        shutil.move(src_file, new_path)
                    else:
                        shutil.copy2(src_file, new_path)
                        logging.info(f"Renamed and copied to avoid conflict: {src_file.name} -> {new_name}")
            return

# -------- Input Prompt --------
def ask_user(question):
    """
    Prompts the user with a question and returns their stripped, lowercase response.
    Uses a lock to ensure thread-safe I/O.
    """
    with _io_lock:
        sys.__stdout__.write(question)
        sys.__stdout__.flush()
        return input().strip().lower()

# -------- Delete Empty Directories --------
def delete_empty_dirs(target):
    """
    Recursively deletes all empty subdirectories within a given target directory.
    It traverses the directory tree from the bottom up to ensure child directories
    are removed before their parents.
    """
    root_path = pathlib.Path(target)
    if not root_path.is_dir():
        raise ValueError(f"{target} is not a valid directory.")
    deleted_count = 0
    # Traverse from the bottom up (sorted reverse) to delete empty children first.
    for dir_path in sorted(root_path.rglob('*'), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            try:
                dir_path.rmdir()
                deleted_count += 1
            except OSError as e:
                logging.error(f"Failed to delete {dir_path}: {e}")
    return deleted_count

# -------- Validators --------
def is_subpath(src: pathlib.Path, dest: pathlib.Path) -> bool:
    """
    Checks if the source path is a subpath of the destination path.
    This is important to prevent infinite recursion, e.g., copying a folder into itself.
    """
    try:
        src = pathlib.Path(src).resolve()
        dest = pathlib.Path(dest).resolve()
        # This will raise a ValueError if src is not a subpath of dest.
        src.relative_to(dest)
        return src != dest
    except ValueError:
        return False

def validator(src, dest, no_create, recursive_check):
    """
    Validates source and destination paths before starting any operation.
    Raises errors for common issues like source not existing, destination being the same as source,
    or being unable to create the destination directory.
    """
    src_path = pathlib.Path(src)
    dest_path = pathlib.Path(dest)
    abs_src_path = src_path.resolve(strict=False)

    if abs_src_path == dest_path.resolve(strict=False):
        raise ValueError(f"Source and destination are the same file: {abs_src_path}")
    if not src_path.exists():
        raise InvalidPathError(str(src_path))
    if not dest_path.exists():
        if no_create:
            raise InvalidPathError(str(dest_path), "Destination does not exist and creation is disabled.")
        try:
            dest_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise PermissionDeniedError(str(dest_path), "write")
    if recursive_check and is_subpath(src, dest):
        raise ValueError("Cannot enable recursive_check when src is inside dest — this can cause unintended behavior.")

# -------- Metadata Gathering --------
def file_filter(directory, match_regex=None, match_names=None, exclude_regex=None, exclude_names=None, recursive_check=False, has_extension=False, is_nest=False, nest_filter=None):
    """
    Scans a directory for files, applying various filters.
    It can operate in two modes:
    1. is_nest=False: Gathers file data and creates a `_filter` set based on size or size+extension.
    2. is_nest=True: Uses a pre-existing `nest_filter` to find matching files in the destination.
    """
    file_data, _filter = {}, set()
    match_re = re.compile(match_regex) if match_regex else None
    exclude_re = re.compile(exclude_regex) if exclude_regex else None
    dir_path = pathlib.Path(directory)
    
    # Decide whether to scan recursively or just the top level.
    entries = dir_path.rglob("*") if (recursive_check and not is_nest) else dir_path.iterdir()
    
    for entry in entries:
        if entry.is_dir():
            continue
        name = entry.name
        # Apply exclusion filters
        if exclude_re and exclude_re.fullmatch(name):
            continue
        if exclude_names and name in exclude_names:
            continue
        # Apply inclusion filters
        if not ((match_re and match_re.fullmatch(name)) or (match_names and name in match_names)):
            continue
            
        file_size = entry.stat().st_size
        file_suffix = entry.suffix.lower()
        
        # When checking the destination ('nest'), use the filter from the source scan.
        if is_nest:
            if has_extension:
                if (file_size, file_suffix) not in nest_filter:
                    continue
            else:
                if file_size not in nest_filter:
                    continue
        
        # Hash the file to get a unique identifier.
        file_hash = hash_file(entry)
        file_data[(file_hash, file_size)] = {"name": name, "path": entry.resolve()}
        
        # When scanning the source, build up the filter for the destination scan.
        if not is_nest:
            if has_extension:
                _filter.add((file_size, file_suffix))
            else:
                _filter.add(file_size)
                
    return (file_data, _filter) if not is_nest else file_data

def folder_filter(target, match_regex, match_names, exclude_regex, exclude_names, levels):
    """
    Recursively finds all files within subdirectories up to a specified depth (`levels`).
    This is used by the `spill` function.
    """
    match_re = re.compile(match_regex) if match_regex else None
    exclude_re = re.compile(exclude_regex) if exclude_regex else None
    dir_path = pathlib.Path(target)
    
    def recursive(_path, current_level, processed):
        try:
            entries = _path.iterdir()
        except PermissionError:
            pass # Ignore directories we can't read.
        else:
            for entry in entries:
                name = entry.name
                if entry.is_dir():
                    # Recurse if we are within the specified level depth.
                    if levels == -1 or current_level < levels:
                        recursive(entry, current_level + 1, processed)
                # Apply filters
                if exclude_re and exclude_re.fullmatch(name):
                    continue
                if exclude_names and name in exclude_names:
                    continue
                if not ((match_re and match_re.fullmatch(name)) or (match_names and name in match_names)):
                    continue
                # We only want files from subdirectories, not the root.
                if entry.is_file() and current_level > 0:
                    processed.append(entry)

    result = []
    recursive(target, 0, result)
    return result

# -------- Regex compilation --------
def sanitize_glob_regex(glob_pattern):
    """Converts a glob pattern into a regex pattern, stripping the default anchors."""
    glob_re = fnmatch.translate(glob_pattern)
    # fnmatch.translate wraps the pattern in `(?s:...)` and `\Z`
    if glob_re.startswith("(?s:") and glob_re.endswith(")\\Z"):
        return glob_re[4:-3]
    return glob_re

def extract_global_flags(regex):
    """Separates global regex flags (e.g., `(?i)`) from the regex pattern itself."""
    match = re.match(r"^\(\?([aiLmsux]+)\)", regex)
    if match:
        return match.group(1), regex[match.end():]
    return "", regex

def combine_regex_with_glob(user_regex, glob_pattern):
    """Combines a user-provided regex and a glob pattern into a single regex."""
    glob_part = sanitize_glob_regex(glob_pattern) if glob_pattern else ""
    user_flags, user_core = extract_global_flags(user_regex or "")
    
    combined_core = ""
    if user_core and glob_part:
        # Combine with a non-capturing group OR
        combined_core = f"(?:{user_core})|(?:{glob_part})"
    elif user_core:
        combined_core = user_core
    elif glob_part:
        combined_core = glob_part
    
    # Re-apply the global flags if they existed.
    if user_flags:
        return f"(?{user_flags}:{combined_core})"
    else:
        return combined_core

# -------- File Copying/Moving Task --------
def copy_or_move_task(file_key, src_path, dest_path, src_name, file_nest, on_conflict, interactive, verbose, dry_run, summary, move):
    src_file = src_path / src_name
    dest_file = dest_path / src_name
    retries, proceed = 0, True

    if interactive:
        response = ""
        if move:
            response = ask_user(f"Move {src_file} to {dest_file}? [y/N]: ")
        else:
            response = ask_user(f"Copy {src_file} to {dest_file}? [y/N]: ")
        proceed = response == "y"
        if not proceed:
            with _io_lock:
                if move:
                    logging.info(f"Moving of {dest_file} was skipped by user.")
                else:
                    logging.info(f"Copying of {dest_file} was skipped by user.")
                return True

    while retries < MAX_RETRIES and proceed:
        try:
            if file_key in file_nest:
                existing_name = file_nest[file_key]["name"]
                existing_file = dest_path / existing_name
                if dry_run:
                    with _io_lock:
                        logging.info(f"[DRY RUN] Duplicate would have been renamed: {existing_name} to {src_name}")
                    return True  
                else:
                    if ( existing_name != src_name ):
                        shutil.move(existing_file, dest_file)
                        with _io_lock:
                            logging.info(f"Duplicate renamed: {existing_name} to {src_name}")
                            if move:
                                os.remove(src_file)
                        return True
                    else:
                        with _io_lock:
                            logging.info(f"File already present: {file_nest[file_key]['path']}")
                            if move:
                                os.remove(src_file)
                        return True

            if dest_file.exists():
                # Conflict handling
                native_size = dest_file.stat().st_size
                immigrant_size = src_file.stat().st_size
                native_time = dest_file.stat().st_mtime
                immigrant_time = src_file.stat().st_mtime

                def replace():
                    try:
                        backup_dir = dest_path / "fylex.deprecated"
                        backup_dir.mkdir(parents=True, exist_ok=True)

                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        backup_file = backup_dir / f"{dest_file.stem}.{timestamp}{dest_file.suffix}"

                        if not dry_run:
                            shutil.move(dest_file, backup_file)
                    except Exception as e:
                        with _io_lock:
                            logging.error(f"Could not back up {dest_file} to {backup_file}: {e}")

                    with _io_lock:
                        if dry_run:
                            logging.info(f"[DRY RUN] Would have replaced: {dest_file} with {src_file}")
                        else:
                            logging.info(f"Replacing: {dest_file} with {src_file}")
                            shutil.copy2(src_file, dest_file)


                def no_change():
                    try:
                        backup_dir = src_path / "fylex.deprecated"
                        backup_dir.mkdir(parents=True, exist_ok=True)

                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        backup_file = backup_dir / f"{src_file.stem}.{timestamp}{src_file.suffix}"

                        if not dry_run:
                            shutil.move(src_file, backup_file)
                    except Exception as e:
                        with _io_lock:
                            logging.error(f"Could not back up {src_file} to {backup_file}: {e}")

                    with _io_lock:
                        if dry_run:
                            logging.info(f"[DRY RUN] No changes to: {dest_file}")
                        else:
                            logging.info(f"No changes to: {dest_file}")

                            
                if dest_file.is_dir():
                    logging.info(f"A folder with the same name exists in the destination directory: {dest_file}")
                    base, ext = os.path.splitext(src_name)
                    i = 1
                    new_name = f"{base}({i}){ext}"
                    new_file = dest_path / new_name
                    while new_file.exists():
                        i += 1
                        new_name = f"{base}({i}){ext}"
                        new_file = dest_path / new_name
                    if dry_run:
                        with _io_lock:
                            logging.info(f"[DRY RUN] Would have renamed: {base} to {new_file}")
                    else:
                        with _io_lock:
                            logging.info(f"Renaming: {base} to {new_file}")
                        shutil.copy2(src_file, new_file)
                    return True
                
                elif dest_file.is_file():
                    if on_conflict == "replace":
                        replace()
                    elif on_conflict == "larger":
                        if native_size >= immigrant_size:
                            no_change()
                            return True
                        replace()
                    elif on_conflict == "smaller":
                        if native_size <= immigrant_size:
                            no_change()
                            return True
                        replace()
                    elif on_conflict == "newer":
                        if native_time >= immigrant_time:
                            no_change()
                            return True
                        replace()
                    elif on_conflict == "older":
                        if native_time <= immigrant_time:
                            no_change()
                            return True
                        replace()
                    elif on_conflict == "skip":
                        with _io_lock:
                            if dry_run:
                                logging.info(f"[DRY RUN] Would have been skipped due to conflict: {dest_file}")
                            else:
                                logging.info(f"Skipping due to conflict: {dest_file}")
                        return True
                    elif on_conflict == "rename":
                        base, ext = os.path.splitext(src_name)
                        i = 1
                        new_name = f"{base}({i}){ext}"
                        new_file = dest_path / new_name
                        while new_file.exists():
                            i += 1
                            new_name = f"{base}({i}){ext}"
                            new_file = dest_path / new_name
                        if dry_run:
                            with _io_lock:
                                logging.info(f"[DRY RUN] Would have renamed: {base} to {new_file}")
                        else:
                            with _io_lock:
                                logging.info(f"Renaming: {base} to {new_file}")
                            shutil.copy2(src_file, new_file)
                        return True
                    elif on_conflict == "prompt":
                        response = ask_user(f"Replace {dest_file} with {src_file}? [y/N]: ")
                        if response == "y":
                            if dry_run:
                                with _io_lock:
                                    logging.info(f"[DRY RUN] Would have replaced: {dest_file} with {src_file}")
                            else:
                                replace()
                        else:
                            if dry_run:
                                with _io_lock:
                                    logging.info(f"Would have been skipped by user: {dest_file}")
                            else:
                                with _io_lock:
                                    logging.info(f"Skipped by user: {dest_file}")
                            return True
                    else:
                        logging.error(f"Unrecognized on_conflict mode supplied: {on_conflict}\nChoose from: {ON_CONFLICT_MODES}")
            else:
                if dry_run:
                    with _io_lock:
                        if move:
                            logging.info(f"[DRY RUN] Would have moved: {src_file} -> {dest_file}")
                        else:
                            logging.info(f"[DRY RUN] Would have copied: {src_file} -> {dest_file}")
                    return True
                shutil.copy2(src_file, dest_file)

            
            if not dry_run:
                new_hash = hash_file(dest_file)
                new_size = dest_file.stat().st_size
                if (new_hash, new_size) != file_key:
                    logging.warning(f"Hash mismatch: {dest_file}. Retrying...")
                    retries += 1
                    try:
                        dest_file.unlink(missing_ok=True)
                    except Exception as e:
                        logging.warning(f"Could not clean up file {dest_file}: {e}")
                    continue
                with _io_lock:
                    if move:
                        os.remove(src_file)
                        logging.info(f"Moved and verified: {src_file} -> {dest_file}")
                    else:
                        logging.info(f"Copied and verified: {src_file} -> {dest_file}")
                    return True
            else:
                with _io_lock:
                    if move:
                        logging.info(f"[DRY RUN] Would have moved and verified: {src_file} -> {dest_file}")
                    else:
                        logging.info(f"[DRY RUN] Would have copied and verified: {src_file} -> {dest_file}")
                return True

        except Exception as e:
            retries += 1
            if retries >= MAX_RETRIES:
                if move:
                    logging.error(f"Failed to move {src_file} after MAX_RETRIES. \nError: {e}")
                else:
                    logging.error(f"Failed to copy {src_file} after MAX_RETRIES. \nError: {e}")
                return False

# -------- Main fileprocess --------
def fileprocess(src, dest, no_create=False, interactive=False, dry_run=False, match_regex=None, match_names=None, match_glob=None,
                exclude_regex=None, exclude_names=None, exclude_glob=None, summary=None, on_conflict="rename", 
                max_workers=4, verbose=False, recursive_check=False, has_extension=False, move=False):
    """
    The main orchestrator function. It sets up logging, validates paths,
    gathers file metadata from source and destination, and then dispatches
    the copy/move tasks to a thread pool.
    """
    # --- Setup ---
    match_regex = combine_regex_with_glob(match_regex, match_glob)
    exclude_regex = combine_regex_with_glob(exclude_regex, exclude_glob)

    if not (match_regex or match_names):
        match_regex = r".+" # Match all files if no specific match pattern is given

    # Reset and configure logging for this run.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("fylex.log", mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.__stdout__) if verbose else logging.NullHandler()
        ]
    )
    
    # Redirect stdout to the logger to capture all output.
    sys.stdout = PrintToLogger(verbose)

    src_path = pathlib.Path(src)
    dest_path = pathlib.Path(dest)

    # If a single file is provided as the source, adjust parameters to handle it correctly.
    if src_path.is_file():
        match_names = [src_path.name]
        src_path = src_path.parent
        match_regex = None
    
    # --- Execution ---
    validator(src, dest, no_create, recursive_check)

    # Scan source and destination directories
    file_birds, nest_filter = file_filter(src_path, match_regex, match_names, exclude_regex, exclude_names, recursive_check, has_extension, False, None)
    file_nest = file_filter(dest_path, ".+", [], None, [], recursive_check, has_extension, True, nest_filter)
    logging.info(f"Collected {len(file_birds)} source file(s)")
    logging.info(f"Nested filter has {len(nest_filter)} entries: {nest_filter}")
    logging.info(f"Matched {len(file_nest)} file(s) at destination")

    # Create a list of tasks for the thread pool.
    tasks = []
    for file_key, info in file_birds.items():
        tasks.append((file_key, src_path, dest_path, info["name"], file_nest, on_conflict, interactive, verbose, dry_run, summary, move))

    # Execute tasks concurrently.
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(copy_or_move_task, *task) for task in tasks]
        for future in as_completed(futures):
            _ = future.result() # Wait for each task to complete.
            
    # --- Finalization ---
    if summary:
        shutil.copy2("fylex.log", summary) # Save the log file to a specified path.

# -------- Main Smart Copy --------
def copy_files(src, dest, no_create=False, interactive=False, dry_run=False, match_regex=None, match_names=None, match_glob=None,
               exclude_regex=None, exclude_names=None, exclude_glob=None, summary=None,
               on_conflict="rename", max_workers=4, verbose=False, recursive_check=False, has_extension=False):
    """Public-facing function for copying files. A wrapper around `fileprocess`."""
    fileprocess(src, dest, no_create, interactive, dry_run, match_regex, match_names, match_glob,
                exclude_regex, exclude_names, exclude_glob, summary, on_conflict.lower(), max_workers, verbose, recursive_check, has_extension, move=False)

# -------- Main Smart Move --------
def move_files(src, dest, no_create=False, interactive=False, dry_run=False, match_regex=None, match_names=None, match_glob=None,
               exclude_regex=None, exclude_names=None, exclude_glob=None, summary=None,
               on_conflict="rename", max_workers=4, verbose=False, recursive_check=False, has_extension=False):
    """Public-facing function for moving files. A wrapper around `fileprocess`."""
    fileprocess(src, dest, no_create, interactive, dry_run, match_regex, match_names, match_glob,
                exclude_regex, exclude_names, exclude_glob, summary, on_conflict.lower(), max_workers, verbose, recursive_check, has_extension, move=True)

# -------- Main Spill --------
def spill(target, interactive=False, dry_run=False, match_regex=None, match_names=None, match_glob=None,
          exclude_regex=None, exclude_names=None, exclude_glob=None, summary=None,
          on_conflict="rename", max_workers=4, levels=-1, verbose=False):
    """
    Moves files from subdirectories into the parent `target` directory.
    `levels` controls the depth of subdirectories to scan (-1 for infinite).
    """
    target = pathlib.Path(target)
    if not target.is_dir():
        raise ValueError(f"Invalid path or not a directory: {target}")

    match_regex = combine_regex_with_glob(match_regex, match_glob)
    exclude_regex = combine_regex_with_glob(exclude_regex, exclude_glob)

    if not (match_regex or match_names):
        match_regex = r".+"

    # Setup logging
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s",
                        handlers=[logging.FileHandler("fylex.log", mode="w", encoding="utf-8"),
                                  logging.StreamHandler(sys.__stdout__) if verbose else logging.NullHandler()])
    sys.stdout = PrintToLogger(verbose)
    
    # Find all files in subfolders that match the criteria.
    files_to_move = folder_filter(target, match_regex, match_names, exclude_regex, exclude_names, levels)
    logging.info(f"Found {len(files_to_move)} files to spill.")
    
    # Use the `move_files` function for each file found.
    for file_path in files_to_move:
        # Note: This calls move_files for each individual file.
        # It could be slightly more efficient to batch them, but this is simpler and safer.
        move_files(str(file_path), str(target), True, interactive, dry_run, None, [file_path.name], None, 
                   None, None, None, summary, on_conflict, max_workers, verbose, False, False)

# -------- Main flatten --------
def flatten(target, interactive=False, dry_run=False, summary=None, on_conflict="rename", max_workers=4, verbose=False):
    """
    Flattens a directory structure by moving all files from all subdirectories
    into the root `target` directory and then deleting the now-empty subdirectories.
    """
    # First, spill all files from all levels.
    spill(target, interactive, dry_run, None, None, None, None, None, None, summary, on_conflict, max_workers, -1, verbose)
    
    # Then, clean up the empty directories left behind.
    if not dry_run:
        empty_dirs_count = delete_empty_dirs(target)
        logging.info(f"Removed {empty_dirs_count} empty directories from {target} after flattening.")
    else:
        logging.info(f"[DRY RUN] Would have removed empty directories from {target}.")

