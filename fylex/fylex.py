import os
import re
import sys
import pathlib
import xxhash
import shutil
import datetime
import threading
import logging
import fnmatch
from concurrent.futures import ThreadPoolExecutor, as_completed
from .exceptions import InvalidPathError, PermissionDeniedError

_io_lock = threading.Lock()
JUNK_EXTENSIONS = {
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



# -------- Logger Setup --------
class PrintToLogger:
    def __init__(self, verbose):
        self.verbose = verbose

    def write(self, msg):
        msg = msg.strip()
        if msg:
            logging.info(msg)
            if self.verbose:
                sys.__stdout__.write(msg + "\n")
                sys.__stdout__.flush()

    def flush(self):
        pass

# -------- Hashing --------
def hash_file(path):
    hasher = xxhash.xxh64()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# -------- Input Prompt --------
def ask_user(question):
    with _io_lock:
        sys.__stdout__.write(question)
        sys.__stdout__.flush()
        return input().strip().lower()

# -------- Validators --------
def validator(src, dest, no_create):
    src_path = pathlib.Path(src)
    dest_path = pathlib.Path(dest)
    abs_src_path = pathlib.Path(src_path).resolve(strict=False)
    if abs_src_path == pathlib.Path(dest_path).resolve(strict=False):
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

# -------- Metadata Gathering --------
def file_size_and_time(directory, match_regex=None, match_names=None, exclude_regex=None, exclude_names=None, has_extension=False, is_nest=False, nest_filter=None):
    file_data, _filter = {}, set()
    match_re = re.compile(match_regex) if match_regex else None
    exclude_re = re.compile(exclude_regex) if exclude_regex else None
    dir_path = pathlib.Path(directory)

    for entry in dir_path.iterdir():
        if entry.is_dir():
            continue
        name = entry.name
        if exclude_re and exclude_re.fullmatch(name):
            continue
        if exclude_names and name in exclude_names:
            continue
        if not ((match_re and match_re.fullmatch(name)) or (match_names and name in match_names)):
            continue
        file_size = entry.stat().st_size       
        file_suffix = entry.suffix.lower()
        if is_nest:
            if has_extension:
                if (file_size,file_suffix) not in nest_filter:
                    continue
            else:
                if file_size not in nest_filter:
                    continue
            
        file_hash = hash_file(entry)
        file_data[(file_hash, file_size)] = {"name": name}
        if not is_nest:
            if has_extension:
                _filter.add((file_size,file_suffix))
            else:
                _filter.add(file_size)
    return (file_data, _filter) if not is_nest else file_data
    
# -------- Regex compilation --------
def sanitize_glob_regex(glob_pattern):
    glob_re = fnmatch.translate(glob_pattern)
    if glob_re.startswith("(?s:") and glob_re.endswith(")\\Z"):
        return glob_re[4:-3]  # Strip (?s: ... )\Z
    return glob_re

def extract_global_flags(regex):
    # Find leading global flags like (?iLmsux)
    match = re.match(r"^\(\?([aiLmsux]+)\)", regex)
    if match:
        return match.group(1), regex[match.end():]
    return "", regex

def combine_regex_with_glob(user_regex, glob_pattern):
    glob_part = sanitize_glob_regex(glob_pattern) if glob_pattern else ""
    user_flags, user_core = extract_global_flags(user_regex or "")
    
    combined_core = ""
    if user_core and glob_part:
        combined_core = f"(?:{user_core})|(?:{glob_part})"
    elif user_core:
        combined_core = user_core
    elif glob_part:
        combined_core = glob_part
    
    if user_flags:
        return f"(?{user_flags}:{combined_core})"
    else:
        return combined_core

# -------- File Copying/Moving Task --------
def _task(file_key, src_path, dest_path, src_name, file_nest, on_conflict, interactive, verbose, dry_run, summary, move):
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

    while retries < 5 and proceed:
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
                        os.rename(existing_file, dest_file)
                        with _io_lock:
                            logging.info(f"Duplicate renamed: {existing_name} to {src_name}")
                            if move:
                                os.remove(src_file)
                        return True
                    else:
                        with _io_lock:
                            logging.info(f"File already present : {existing_name}")
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
                    with _io_lock:
                        if dry_run:
                            logging.info(f"[DRY RUN] Would have replaced: {dest_file} with {src_file}")
                        else:
                            logging.info(f"Replacing: {dest_file} with {src_file}")
                            shutil.copy2(src_file, dest_file)
                            
                def no_change():
                    with _io_lock:
                        if dry_run:
                            logging.info(f"[DRY RUN] No changes to: {dest_file}")  
                        else:
                            logging.info(f"No changes to: {dest_file}")
                            
                if on_conflict == "larger":
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
                    if not dry_run:
                        replace()
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
                    dest_file.unlink(missing_ok=True)
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
            if retries >= 5:
                if move:
                    logging.error(f"Failed to move {src_file} after retries. Error: {e}")
                else:
                    logging.error(f"Failed to copy {src_file} after retries. Error: {e}")
                return False


# -------- Main fileprocess --------

def fileprocess(src, dest, no_create=False, interactive=False, dry_run=False, match_regex=None, match_names=None, match_glob=None,
                exclude_regex=None, exclude_names=None, exclude_glob=None, summary=None, on_conflict=None, max_workers=4, verbose=False, has_extension=False, move=False):
    match_regex = combine_regex_with_glob(match_regex, match_glob)
    exclude_regex = combine_regex_with_glob(exclude_regex, exclude_glob)

    if not (match_regex or match_names):
        match_regex = r".+"
        
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
    
    # Override print only for this run, and respect verbose flag
    sys.stdout = PrintToLogger(verbose)

    src_path = pathlib.Path(src)
    dest_path = pathlib.Path(dest)

    if match_names and match_regex == r".+":
        match_regex = None

    if src_path.is_file():
        match_names = [src_path.name]
        src_path = src_path.parent
        match_regex = None
        
    validator(src, dest, no_create)

    file_birds, nest_filter = file_size_and_time(src_path, match_regex, match_names, exclude_regex, exclude_names, has_extension, False, None)
    file_nest = file_size_and_time(dest_path, ".+", [], None, [], has_extension, True, nest_filter)
    #print(f"******{file_birds}******{file_nest}*******{_filter}")
    tasks = []
    for file_key, info in file_birds.items():
        tasks.append((file_key, src_path, dest_path, info["name"], file_nest, on_conflict, interactive, verbose, dry_run, summary, move))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_task, *task) for task in tasks]
        for future in as_completed(futures):
            _ = future.result()
            
    if summary:
        shutil.copy2("fylex.log", summary)

# -------- Main Smart Copy --------
def copy_files(src, dest, no_create=False, interactive=False, dry_run=False, match_regex=None, match_names=None, match_glob=None,
                exclude_regex=None, exclude_names=None, exclude_glob=None, summary=None,
               on_conflict=None, max_workers=4, verbose=False, has_extension=False):
    fileprocess(src, dest, no_create, interactive, dry_run, match_regex, match_names, match_glob,
                exclude_regex, exclude_names, exclude_glob, summary, on_conflict, max_workers, verbose, has_extension, move=False)
    
# -------- Main Smart Move --------
def move_files(src, dest, no_create=False, interactive=False, dry_run=False, match_regex=None, match_names=None, match_glob=None,
                exclude_regex=None, exclude_names=None, exclude_glob=None, summary=None,
               on_conflict=None, max_workers=4, verbose=False, has_extension=False):
    fileprocess(src, dest, no_create, interactive, dry_run, match_regex, match_names, match_glob,
                exclude_regex, exclude_names, exclude_glob, summary, on_conflict, max_workers, verbose, has_extension, move=True)
