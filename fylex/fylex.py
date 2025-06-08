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
def file_size_and_time(directory, match_regex=None, match_names=None, exclude_regex=None, exclude_names=None):
    file_data = {}
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
        file_hash = hash_file(entry)
        file_size = entry.stat().st_size
        file_data[(file_hash, file_size)] = {"name": name}

    return file_data
    
# -------- Regex compilation --------
import fnmatch
import re

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

# -------- File Copying Task --------
def _copy_task(file_key, src_path, dest_path, src_name, file_nest, on_conflict, interactive, verbose, dry_run, summary):
    src_file = src_path / src_name
    dest_file = dest_path / src_name
    retries, proceed = 0, True

    if interactive:
        response = ask_user(f"Copy {src_file} to {dest_file}? [y/N]: ")
        proceed = response == "y"
        if not proceed:
            with _io_lock:
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
                    os.rename(existing_file, dest_file)
                    with _io_lock:
                        logging.info(f"Duplicate renamed: {existing_name} to {src_name}")
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
                    logging.info(f"Copied and verified: {src_file} -> {dest_file}")
                    return True
            else:
                with _io_lock:
                    logging.info(f"[DRY RUN] Would have copied and verified: {src_file} -> {dest_file}")
                return True

        except Exception as e:
            retries += 1
            if retries >= 5:
                logging.error(f"Failed to copy {src_file} after retries. Error: {e}")
                return False

# -------- Main Smart Copy --------
def smart_copy(src, dest, no_create=False, interactive=False, dry_run=False, match_regex=None, match_names=None, match_glob=None,
                exclude_regex=None, exclude_names=None, exclude_glob=None, summary=None,
               on_conflict=None, max_workers=4, verbose=False):
    
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
    
    validator(src, dest, no_create)

    src_path = pathlib.Path(src)
    dest_path = pathlib.Path(dest)

    if match_names and match_regex == r".+":
        match_regex = None

    if src_path.is_file():
        match_names = [src_path.name]
        src_path = src_path.parent
        match_regex = None

    file_birds = file_size_and_time(src_path, match_regex, match_names, exclude_regex, exclude_names)
    file_nest = file_size_and_time(dest_path, ".+", [], None, [])

    tasks = []
    for file_key, info in file_birds.items():
        tasks.append((file_key, src_path, dest_path, info["name"], file_nest, on_conflict, interactive, verbose, dry_run, summary))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_copy_task, *task) for task in tasks]
        for future in as_completed(futures):
            _ = future.result()
            
    if summary:
        shutil.copy2("fylex.log", summary)
