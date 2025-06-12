
# Fylex: Your Intelligent File & Directory Orchestrator


[![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![PyPI Downloads](https://static.pepy.tech/badge/fylex)](https://pepy.tech/projects/fylex)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Fylex is a powerful and flexible Python utility designed to simplify complex file management tasks. From intelligent copying and moving to flattening chaotic directory structures and resolving file conflicts, Fylex provides a robust, concurrent, and log-detailed solution for organizing your digital life.

## Table of Contents

1.  [Introduction](#introduction)
2.  [Key Features](#key-features)
3.  [Installation](#installation)
4.  [Usage](#usage)
    * [Core Functions Overview](#core-functions-overview)
    * [Common Parameters](#common-parameters)
    * [Conflict Resolution Modes (`on_conflict`)](#conflict-resolution-modes-on_conflict)
    * [Examples](#examples)
        * [`copy_files`: Smart Copying](#copy_files-smart-copying)
        * [`move_files`: Smart Moving](#move_files-smart-moving)
        * [`spill`: Consolidating Files from Subdirectories](#spill-consolidating-files-from-subdirectories)
        * [`flatten`: Flattening Directory Structures](#flatten-flattening-directory-structures)
        * [Handling Junk Files](#handling-junk-files)
        * [Dry Run and Interactive Modes](#dry-run-and-interactive-modes)
        * [Working with Regex and Glob Patterns](#working-with-regex-and-glob-patterns)
5.  [Why Fylex is Superior](#why-fylex-is-superior)
6.  [Error Handling](#error-handling)
7.  [Logging](#logging)
8.  [Development & Contributing](#development--contributing)
9.  [License](#license)

## 1. Introduction

Managing files can quickly become a tedious and error-prone process, especially when dealing with large collections, duplicate files, or disorganized directory structures. Traditional command-line tools offer basic copy/move functionalities, but often lack the intelligence to handle conflicts, filter effectively, or automate complex reorganization patterns.

Fylex steps in to fill this gap. It's built on a foundation of robust error handling, concurrent processing, and intelligent decision-making, ensuring your file operations are efficient, safe, and tailored to your needs.

## 2. Key Features

* **Smart Copy (`copy_files`)**: Copy files with advanced filtering, conflict resolution, and integrity verification.
* **Smart Move (`move_files`)**: Move files, similar to copying, but with source file deletion upon successful transfer and verification.
* **File Hashing for Reliability**: Utilizes `xxhash` for fast, non-cryptographic hashing to ensure file integrity post-transfer and detect true content duplicates.
* **Sophisticated Conflict Resolution**: Offers a comprehensive set of strategies to handle name collisions at the destination (e.g., rename, replace, keep larger/smaller/newer/older, skip, or prompt).
* **Accident Prevention with Deprecated Folders**: **Crucially, when an `on_conflict` mode leads to an existing destination file being replaced (e.g., by a "newer" or "larger" incoming file), Fylex automatically moves the *superseded* file into a timestamped `.fylex_deprecated/` subfolder within the destination directory. This acts as a robust safety net against accidental data loss, allowing you to recover older versions if needed.** Additionally, if a source file is skipped because its identical counterpart already exists at the destination, it is also moved to `fylex.deprecated/` by default.
* **Flexible File Filtering**:
    * **Inclusion**: Specify files to process using regular expressions (`match_regex`), exact names (`match_names`), or glob patterns (`match_glob`).
    * **Exclusion**: Prevent specific files from being processed using `exclude_regex`, `exclude_names`, or `exclude_glob`.
    * **Junk File Awareness**: Predefined `JUNK_EXTENSIONS` helps easily exclude common temporary, system, and development artifacts.
* **Directory Reorganization Utilities**:
    * **`spill`**: Consolidate files from nested subdirectories up to a specified depth into a parent directory.
    * **`flatten`**: Move all files from an entire directory tree into a single target directory, then automatically delete the empty subdirectories.
* **Concurrency for Speed**: Leverages Python's `ThreadPoolExecutor` to perform file operations in parallel, significantly speeding up tasks involving many files.
* **Dry Run Mode**: Simulate any operation without making actual changes to the filesystem. Essential for verifying complex commands before execution.
* **Interactive Mode**: Prompts for user confirmation before each file operation, providing fine-grained control.
* **Comprehensive Logging**: All actions, warnings, and errors are meticulously logged to `fylex.log` for easy auditing and debugging.
* **Robust Path Validation**: Prevents common pitfalls like attempting to copy a directory into itself, or operating on non-existent paths.
* **Retry Mechanism**: Failed file operations are retried up to `MAX_RETRIES` to handle transient network issues or temporary file locks.

## 3. Installation

Fylex is designed to be integrated into your Python projects or run as a standalone script.

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/your-repo/fylex.git](https://github.com/your-repo/fylex.git) # Replace with your actual repo
    cd fylex
    ```
2.  **Install dependencies**:
    Fylex requires `xxhash`.
    ```bash
    pip install xxhash
    ```
3.  **Include in your project**:
    You can import Fylex functions directly into your Python scripts:
    ```python
    from fylex import copy_files, move_files, spill, flatten, delete_empty_dirs
    from fylex.exceptions import InvalidPathError, PermissionDeniedError
    ```

## 4. Usage

Fylex functions are designed to be intuitive. Here's a breakdown of the core functions and their parameters.

### Core Functions Overview

* `copy_files(src, dest, **kwargs)`: Copies files from `src` to `dest`.
* `move_files(src, dest, **kwargs)`: Moves files from `src` to `dest`.
* `spill(target, **kwargs)`: Moves files from subdirectories within `target` to `target`.
* `flatten(target, **kwargs)`: Moves all files from subdirectories within `target` to `target` and deletes empty subdirectories.
* `delete_empty_dirs(target)`: Recursively deletes all empty subdirectories within `target`.

### Common Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `src` | `str` | `N/A` | **Source path** (file or directory) for `copy_files` and `move_files`. |
| `dest` | `str` | `N/A` | **Destination path** (directory) for `copy_files` and `move_files`. |
| `target` | `str` | `N/A` | **Target directory path** for `spill`, `flatten`, and `delete_empty_dirs`. |
| `no_create` | `bool` | `False` | If `True`, prevents Fylex from creating the `dest` directory if it doesn't exist. An `InvalidPathError` will be raised. |
| `interactive` | `bool` | `False` | If `True`, Fylex will prompt the user for confirmation before each file operation. |
| `dry_run` | `bool` | `False` | If `True`, Fylex will simulate all operations without making any changes to the filesystem. Useful for testing and verification. Logs will indicate what *would* have happened. |
| `match_regex` | `str` | `None` | A regular expression string to include files whose names fully match the pattern. Overrides `match_glob`. |
| `match_names` | `list[str]` | `None` | A list of exact file names to include. Case-sensitive. |
| `match_glob` | `str` | `None` | A Unix-style glob pattern to include files whose names match. Converted to regex internally. |
| `exclude_regex` | `str` | `None` | A regular expression string to exclude files whose names fully match the pattern. Overrides `exclude_glob`. |
| `exclude_names` | `list[str]` | `None` | A list of exact file names to exclude. Case-sensitive. |
| `exclude_glob` | `str` | `None` | A Unix-style glob pattern to exclude files whose names match. Converted to regex internally. |
| `summary` | `str` | `None` | Path where the `fylex.log` file should be copied after the operation completes. If `None`, the log remains only in `fylex.log` in the current working directory. |
| `on_conflict` | `str` | `"rename"` | Defines how Fylex handles name collisions at the destination. See [Conflict Resolution Modes](#conflict-resolution-modes-on_conflict) below. |
| `max_workers` | `int` | `4` | The maximum number of threads to use for concurrent file operations. Adjust based on your system's capabilities and disk I/O. |
| `verbose` | `bool` | `False` | If `True`, log messages will also be printed to the console in real-time. Otherwise, they are only written to `fylex.log`. |
| `recursive_check` | `bool` | `False` | If `True`, `copy_files` and `move_files` will scan source and destination subdirectories for matching files. **Crucial for deep scans.** |
| `has_extension` | `bool` | `False` | If `True` for `copy_files` and `move_files`, file filtering and duplicate checks will also consider the file extension in addition to size. Useful for more precise duplicate detection of files with identical sizes but different types. |
| `levels` | `int` | `-1` | For `spill`, defines the maximum subdirectory depth to scan. `-1` means infinite depth (all subdirectories). `0` means only the target directory itself (no subdirectories). `1` means immediate subdirectories, and so on. |

### Conflict Resolution Modes (`on_conflict`)

Fylex offers smart handling of file name conflicts at the destination. The `on_conflict` parameter accepts one of the following string values:

* **`"rename"` (Default)**: If a file with the same name exists, the incoming file will be renamed (e.g., `document.txt` becomes `document(1).txt`, `document(2).txt`, etc.) to avoid overwriting.
* **`"replace"`**: The incoming file will unconditionally overwrite the existing file at the destination. **The original file will be moved to a timestamped `.fylex_deprecated/` folder within the destination for safety.**
* **`"larger"`**: The file with the larger file size will be kept. If the existing file is larger or equal, the incoming file is skipped. **If skipped, the source file is moved to `fylex.deprecated/`**. If the incoming file is larger, it replaces the existing one, and the **original file is moved to `.fylex_deprecated/`**.
* **`"smaller"`**: The file with the smaller file size will be kept. If the existing file is smaller or equal, the incoming file is skipped. **If skipped, the source file is moved to `fylex.deprecated/`**. If the incoming file is smaller, it replaces the existing one, and the **original file is moved to `.fylex_deprecated/`**.
* **`"newer"`**: The file with the more recent modification timestamp will be kept. If the existing file is newer or has the same timestamp, the incoming file is skipped. **If skipped, the source file is moved to `fylex.deprecated/`**. If the incoming file is newer, it replaces the existing one, and the **original file is moved to `.fylex_deprecated/`**.
* **`"older"`**: The file with the older modification timestamp will be kept. If the existing file is older or has the same timestamp, the incoming file is skipped. **If skipped, the source file is moved to `fylex.deprecated/`**. If the incoming file is older, it replaces the existing one, and the **original file is moved to `.fylex_deprecated/`**.
* **`"skip"`**: The incoming file will be skipped entirely if a file with the same name exists at the destination. **The skipped source file is moved to `fylex.deprecated/` for review.**
* **`"prompt"`**: Fylex will ask the user interactively (via console) whether to replace the existing file or skip the incoming one. If "replace" is chosen, the **original file is moved to `.fylex_deprecated/`**. If "skip" is chosen, the **skipped source file is moved to `fylex.deprecated/`**.

### Examples

Let's assume the following directory structure for the examples:

````

/data/
├── project\_A/
│   ├── main.py
│   ├── config.ini
│   └── docs/
│       ├── readme.md
│       └── images/
│           └── img\_01.png
├── project\_B/
│   ├── index.html
│   └── style.css
├── temp/
│   ├── .tmp
│   ├── old\_data.bak
│   └── report.log
├── my\_files/
│   ├── photo.jpg
│   ├── document.pdf
│   └── sub\_folder/
│       └── nested\_file.txt
└── important\_notes.txt

````

And your destination directory is initially empty: `/backup/`

#### `copy_files`: Smart Copying

```python
from fylex import copy_files

# Example 1: Copy all Python files from project_A to /backup, resolving conflicts by renaming.
# Only scans the top-level files of project_A if recursive_check=False
copy_files(src="/data/project_A", dest="/backup",
           match_glob="*.py", on_conflict="rename", verbose=True)
# Result: /backup/main.py

# Example 2: Copy all files from /data/my_files including subdirectories,
# excluding .txt files, and keep the newer version on conflict.
# If a file like 'photo.jpg' exists in /backup/my_backup and is older,
# the existing 'photo.jpg' would be moved to '/backup/my_backup/.fylex_deprecated/YYYY-MM-DD_HH-MM-SS/'
# before the new 'photo.jpg' is copied.
copy_files(src="/data/my_files", dest="/backup/my_backup",
           recursive_check=True, exclude_glob="*.txt", on_conflict="newer", verbose=True)
# Result: /backup/my_backup/photo.jpg, /backup/my_backup/document.pdf
# (nested_file.txt would be skipped due to exclusion)

# Example 3: Copy only 'important_notes.txt' from /data to /backup
copy_files(src="/data", dest="/backup",
           match_names=["important_notes.txt"], verbose=True)
# Result: /backup/important_notes.txt
````

#### `move_files`: Smart Moving

`move_files` works identically to `copy_files` but deletes the source file after successful transfer.

```python
from fylex import move_files

# Example: Move all .html and .css files from project_B to /web_files,
# prompting on conflict.
# If the user chooses to replace, the existing file in /web_files would be moved
# to '/web_files/.fylex_deprecated/YYYY-MM-DD_HH-MM-SS/'.
# If the user chooses to skip, the source file (e.g., /data/project_B/index.html)
# would be moved to 'fylex.deprecated/' (in the current working directory).
move_files(src="/data/project_B", dest="/web_files",
           match_glob="*.{html,css}", on_conflict="prompt", interactive=True, verbose=True)
# User would be prompted for each file if it already exists in /web_files.
# After successful move: /data/project_B will no longer contain index.html or style.css
```

#### `spill`: Consolidating Files from Subdirectories

`spill` moves files from nested directories into the `target` root directory.

```python
from fylex import spill
import os
import shutil

# Setup for spill example:
os.makedirs("/data/temp_spill/level1/level2", exist_ok=True)
with open("/data/temp_spill/fileA.txt", "w") as f: f.write("A")
with open("/data/temp_spill/level1/fileB.txt", "w") as f: f.write("B")
with open("/data/temp_spill/level1/level2/fileC.txt", "w") as f: f.write("C")
with open("/data/temp_spill/level1/level2/image.jpg", "w") as f: f.write("C")

# Example 1: Spill all files from subdirectories (infinite levels) into /data/temp_spill.
# If fileB.txt already existed in /data/temp_spill, it would be deprecated based on conflict mode.
spill(target="/data/temp_spill", levels=-1, verbose=True)
# Result: /data/temp_spill/fileA.txt, /data/temp_spill/fileB.txt, /data/temp_spill/fileC.txt, /data/temp_spill/image.jpg
# (fileA.txt is already at root, so not moved)
# The empty subdirectories /data/temp_spill/level1 and /data/temp_spill/level1/level2 will remain.

# Clean up for next example:
shutil.rmtree("/data/temp_spill")
os.makedirs("/data/temp_spill/level1/level2", exist_ok=True)
with open("/data/temp_spill/fileA.txt", "w") as f: f.write("A")
with open("/data/temp_spill/level1/fileB.txt", "w") as f: f.write("B")
with open("/data/temp_spill/level1/level2/fileC.txt", "w") as f: f.write("C")

# Example 2: Spill only files from immediate subdirectories (level 1), excluding .txt files.
spill(target="/data/temp_spill", levels=1, exclude_glob="*.txt", verbose=True)
# Result: Only files from /data/temp_spill/level1 (like fileB.txt if not excluded) would be considered.
# In this specific setup, since only .txt files are present, nothing would move.
# If image.jpg was in level1, it would move.
```

#### `flatten`: Flattening Directory Structures

`flatten` is ideal for taking a messy, deeply nested folder and putting all its files into one level, then cleaning up the empty folders.

```python
from fylex import flatten
import os
import shutil

# Setup for flatten example (same as spill setup):
os.makedirs("/data/temp_flatten/level1/level2", exist_ok=True)
with open("/data/temp_flatten/fileX.log", "w") as f: f.write("X") # Will be ignored by default junk filter
with open("/data/temp_flatten/level1/fileY.jpg", "w") as f: f.write("Y")
with open("/data/temp_flatten/level1/level2/fileZ.pdf", "w") as f: f.write("Z")

# Example: Flatten the entire /data/temp_flatten directory.
# Any files in subdirectories that would overwrite an existing file in /data/temp_flatten
# would first cause the existing file to be moved to '/data/temp_flatten/.fylex_deprecated/'.
flatten(target="/data/temp_flatten", verbose=True)
# Result: /data/temp_flatten/fileX.log, /data/temp_flatten/fileY.jpg, /data/temp_flatten/fileZ.pdf
# After operation, /data/temp_flatten/level1/ and /data/temp_flatten/level1/level2/ will be deleted.
```

#### Handling Junk Files

Fylex comes with a predefined list of common "junk" file extensions and names. You can leverage this via the `exclude_names` and `exclude_glob` parameters or modify the `JUNK_EXTENSIONS` dictionary in the source.

```python
from fylex import copy_files, JUNK_EXTENSIONS

# Combine all junk extensions and names into lists for exclusion
all_junk_extensions = [ext for sublist in JUNK_EXTENSIONS.values() for ext in sublist if ext.startswith(".")]
all_junk_names = [name for sublist in JUNK_EXTENSIONS.values() for name in sublist if not name.startswith(".")]

# Example: Copy all files from /data/temp to /archive, excluding all known junk.
# Note: You'd typically want to specify target directory for JUNK_EXTENSIONS if using.
# For simplicity, let's use common examples.
copy_files(src="/data/temp", dest="/archive",
           exclude_glob="*.tmp", # Exclude temporary files
           exclude_names=["thumbs.db", "desktop.ini"], # Exclude specific names
           recursive_check=True, verbose=True)
# Result: .tmp, old_data.bak, report.log would be excluded based on these specific exclusions.
```

#### Dry Run and Interactive Modes

```python
from fylex import copy_files

# Example: See what would happen if you were to copy all .txt files without actually doing it.
copy_files(src="/data/project_A", dest="/backup",
           match_glob="*.md", dry_run=True, verbose=True)
# Output in log/console: "[DRY RUN] Would have copied: /data/project_A/docs/readme.md -> /backup/readme.md"
# No files are actually copied.

# Example: Be prompted for every action
copy_files(src="/data/project_A", dest="/backup",
           match_glob="*.ini", interactive=True, verbose=True)
# Console: "Copy /data/project_A/config.ini to /backup/config.ini? [y/N]:"
# User input determines if the copy proceeds.
```

#### Working with Regex and Glob Patterns

Fylex allows you to combine regex and glob patterns for precise filtering.

```python
from fylex import copy_files

# Example 1: Copy files that are either .jpg OR start with 'report'
copy_files(src="/data/my_files", dest="/backup",
           match_regex=r".*\.jpg$", # Matches any .jpg
           match_glob="report*", # Matches files starting with 'report'
           verbose=True)

# Example 2: Exclude files that are either log files or contain 'temp' in their name
copy_files(src="/data/", dest="/filtered_data",
           recursive_check=True,
           exclude_regex=r".*\.log$",
           exclude_glob="*temp*", # Matches files containing 'temp'
           verbose=True)
```

## 5\. Why Fylex is Superior

Compared to standard shell commands (`cp`, `mv`, `rm`, `find`, `robocopy` / `rsync`) or even basic scripting, Fylex offers significant advantages:

1.  **Intelligent Conflict Resolution (Beyond Overwrite/Rename) *with Accident Prevention***:

      * **Shell**: `cp -f` overwrites, `cp -n` skips. `robocopy` offers more, but still lacks integrated safe-guards.
      * **Fylex**: Provides `rename`, `replace`, `larger`, `smaller`, `newer`, `older`, `skip`, and `prompt`. **Crucially, when Fylex replaces an existing file at the destination or skips a source file (due to a conflict), it first moves the affected file into a dedicated, timestamped `.fylex_deprecated/` folder.** This virtually eliminates the risk of accidental data loss, allowing users to review and retrieve superseded or skipped files later. This safety net is a major leap beyond simple overwrite/skip options in other tools.

2.  **Built-in Data Integrity Verification (Hashing):**

      * OS commands perform a basic copy. You'd need to manually run `md5sum` or `sha256sum` after the copy and compare.
      * `Fylex` uses `xxhash` for fast post-copy verification, ensuring that the copied file is an exact, uncorrupted duplicate of the source. This is crucial for critical data.

3.  **Unified and Advanced Filtering:**

      * `find` combined with `grep`, `xargs`, and `egrep` is powerful but often requires complex, multi-stage commands. Glob patterns are simpler but less flexible than regex.
      * `Fylex` integrates regex, glob, and exact name matching/exclusion directly into its functions, allowing for highly specific and readable filtering with a single API call.

4.  **Specialized Directory Reorganization (`spill`, `flatten`):**

      * Achieving "spill" or "flatten" with OS commands means chaining `find`, `mv`, `rmdir`, and potentially `xargs` with very specific and often platform-dependent syntax. This is notoriously difficult to get right and can lead to accidental data loss if a mistake is made.
      * `Fylex` provides these as high-level, single-function operations with built-in safety (like dry run and empty directory cleanup), making them much safer and easier to use.

5.  **Concurrency Out-of-the-Box:**

      * Basic OS commands are single-threaded. Parallelization requires advanced shell scripting with `xargs -P` or similar, which adds complexity.
      * `Fylex` automatically utilizes a `ThreadPoolExecutor` to process files concurrently, significantly boosting performance for large datasets without any extra effort from the user.

6.  **Comprehensive Logging & Dry Run Safety Net:**

      * OS commands typically dump output to stdout/stderr. Comprehensive logging requires redirection and parsing. Dry run is often simulated or requires specific flags that may not exist for all commands.
      * `Fylex` generates detailed `fylex.log` for every operation, providing an auditable trail. The `dry_run` mode is a built-in safeguard, allowing you to preview complex operations safely.

7.  **Python Integration & Extensibility:**

      * While powerful, shell scripts can be less maintainable and harder to integrate into larger software systems.
      * `Fylex`, being a Python library, is easily callable from any Python application, making it highly extensible and automatable within existing Python workflows.

8.  **User Interactivity:**

      * Shell: Limited options for user prompts during bulk operations.
      * `Fylex`: `interactive` mode provides a safety net by prompting for confirmation before each file transfer, giving you granular control.

In essence, Fylex transforms common, complex, and risky file management scenarios into straightforward, reliable, and efficient operations, saving time, preventing data loss, and simplifying automation.

## 6\. Error Handling

Fylex implements robust error handling to ensure operations are performed safely and to provide clear feedback when issues arise.

  * `InvalidPathError`: Raised if a specified source path does not exist, or if `no_create` is `True` and the destination path does not exist.
  * `PermissionDeniedError`: Raised if Fylex lacks the necessary read or write permissions for a given path.
  * `ValueError`: Raised for logical inconsistencies, such as trying to copy a directory into itself when `recursive_check` is enabled.
  * **Retry Mechanism**: Transient errors during file copy/move operations are automatically retried up to `MAX_RETRIES` (default: 5). If retries are exhausted, an error is logged.

## 7\. Logging

Fylex provides detailed logging to `fylex.log` in the current working directory by default.

  * **INFO**: Records successful operations, dry run simulations, and significant events, including deprecation actions.
  * **WARNING**: Indicates potential issues, such as hash mismatches requiring retries.
  * **ERROR**: Logs failures, permissions issues, or unhandled exceptions.

You can control log output:

  * `verbose=True`: Prints log messages to the console in real-time, in addition to the file.
  * `summary="path/to/my_log.log"`: Copies the `fylex.log` file to the specified summary path upon completion.

## 8\. Development & Contributing

Fylex is open to contributions\! If you have ideas for new features, bug fixes, or improvements, feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Write clear commit messages.
5.  Submit a Pull Request.

## 9\. License

Fylex is released under the [MIT License](https://www.google.com/search?q=LICENSE)

xxHash used under BSD License
##

## 10\. Author

**Sivaprasad Murali** —
[sivaprasad.off@gmail.com](mailto:sivaprasad.off@gmail.com)


##
<center>Your files. Your rules. Just smarter.</center>



