## <div style="text-align:right">[![PyPI Downloads](https://static.pepy.tech/badge/fylex)](https://pepy.tech/projects/fylex)</div>

# fylex 


**Smart, Safe & Customizable File Operations Toolkit**


`fylex` is a Python-powered CLI utility and library that enables **high-performance file copying and moving** with content-aware logic, parallel execution, and advanced filtering. Built for developers, sysadmins, and data engineers who need **reliable and configurable file operations** across platforms.

##

##  Key Highlights

*  **Hash-Based File Comparison** — skip identical files using `xxhash`
*  **Multithreaded Copying** — speed up transfers using `ThreadPoolExecutor`
*  **Advanced Filtering** — include/exclude via glob, regex, or filenames
*  **Robust Conflict Handling** — resolve duplicates by size, time, rename, etc.
*  **Interactive + Dry-Run Modes** — test your actions before committing
*  **Logging & Summary Files** — track operations with optional logs
*  **Preserves Metadata** — timestamps and permissions retained

##

## Why `fylex`?

Most tools either **blindly copy everything** or **require complex scripting** to filter and verify safely. `fylex` offers a smarter alternative:


| Criteria                           | `fylex`                                   | `rsync`                       | `shutil` / `distutils`  | `robocopy` (Windows)       | Other Python libs (e.g. `send2trash`, `dirsync`) |
| ---------------------------------- | ------------------------------------------------------ | ----------------------------- | ----------------------- | -------------------------- | ------------------------------------------------ |
| **Hash-based change detection**    | ✅ Uses `xxhash` to skip identical files efficiently    |  Optional via checksum      | ❌ Metadata only         | ❌ File size/time only      |  Varies per lib                                |
| **Multi-threaded copy**            | ✅ `ThreadPoolExecutor`-based parallelism               | ❌ Mostly single-threaded      | ❌ Single-threaded       | ✅ Parallelization possible | ❌ Usually sequential                             |
| **Regex + Glob + Name filtering**  | ✅ Supports all three (rare combo)                      |  Basic include/exclude      | ❌ Minimal support       |  Mask-based filtering    |  Usually only glob                             |
| **Conflict resolution strategies** | ✅ `skip`, `replace`, `rename`, `larger`, `newer`, etc. |  `--update`, overwrite-only | ❌ Must handle manually  |  Some file age support   | ❌ Very limited logic                             |
| **Smart move**                     | ✅ Adds verified delete after copy                      | ❌ Requires manual delete      | ❌ No move-and-check     | ❌ Overwrites or fails      | ❌ Not built-in                                   |
| **Interactive prompts**            | ✅ Asks on conflict (optional)                          | ❌ No CLI interactivity        | ❌ No interactivity      | ❌ Batch/script-oriented    | ❌ Rare                                           |
| **Dry-run mode**                   | ✅ Simulates full operation                             | ✅ `--dry-run`                 | ❌ Not available         | ✅ `/L` option              |  Sometimes                                     |
| **Preserves metadata**             | ✅ Via `shutil.copy2()`                                 | ✅ Preserves most metadata     |  Partial (copy2 only) | ✅ Full metadata support    |  Limited                                       |
| **Logging and Summary**            | ✅ Optional logs and summary file                       |  Logs via stdout            | ❌ No logs               | ✅ Built-in logs            | ❌ Rare                                           |
| **CLI + API support**              | ✅ Both available                                       | ❌ CLI-only                    |  Python-only          | ✅ CLI only                 |  API only                                      |
| **Cross-platform**                 | ✅ Full (Linux, macOS, Windows)                         | ✅ Mostly                      | ✅ Yes                   | ❌ Windows-only             |  Varies                                        |
| **Extensibility / Modularity**     | ✅ Modular design, easy to plug in new behaviors        | ❌ Hard to extend              | ✅ For basic scripting   | ❌ Not scriptable           |  Sometimes messy                               |
| **Active UI feedback (UX)**        | ✅ Supports verbose/dry-run interactions                | ❌ Silent unless verbose       | ❌ No feedback           |  Some progress reports   | ❌ Often silent                                   |

##

## Positioning Strategy for `fylex`

| Target Audience              | How `fylex` Fits Them                                                |
| ---------------------------- | -------------------------------------------------------------------- |
| **Developers / Engineers**   | Precise control via regex/glob/API, great for devops/data copying    |
| **Data Analysts**            | Safe bulk copy/move of large datasets, with dry-run + summary        |
| **Researchers / Archivists** | Reliable deduplication & backup tool for sensitive files             |
| **Open Source Users**        | A modern `rsync` alternative with user-friendly interface            |
| **Sysadmins / Automators**   | CLI + script combo makes it usable in crons or custom Python scripts |


##

##  Main Functions

```python
fylex.copy_files(src, dest, **options)
fylex.move_files(src, dest, **options)
```
##

##  Parameters

| Parameter       | Type        | Description                                                                                          |
| --------------- | ----------- | ---------------------------------------------------------------------------------------------------- |
| `src`           | `str`       | Source directory or file                                                                             |
| `dest`          | `str`       | Destination directory                                                                                |
| `no_create`     | `bool`      | If `True`, do not create destination if missing                                                      |
| `interactive`   | `bool`      | Prompt before each operation                                                                         |
| `dry_run`       | `bool`      | Simulate operation without modifying files                                                           |
| `match_regex`   | `str`       | Regex pattern to include files                                                                       |
| `match_names`   | `list[str]` | Exact filenames to include                                                                           |
| `match_glob`    | `str`       | Glob pattern to include files                                                                        |
| `exclude_regex` | `str`       | Regex pattern to exclude files                                                                       |
| `exclude_names` | `list[str]` | Exact filenames to exclude                                                                           |
| `exclude_glob`  | `str`       | Glob pattern to exclude files                                                                        |
| `summary`       | `str`       | Output path for log summary                                                                          |
| `on_conflict`   | `str`       | Conflict resolution: `"larger"`, `"smaller"`, `"newer"`, `"older"`, `"rename"`, `"skip"`, `"prompt"` |
| `max_workers`   | `int`       | Number of threads (default 4)                                                                        |
| `verbose`       | `bool`      | Show logs in console                                                                                 |
| `has_extension` | `bool`      | Track extensions in duplicate detection                                                              |

##

##  Example: `copy_files()` 

```python
from fylex import copy_files

copy_files(
    src="input_folder",
    dest="output_folder",
    match_regex=r".*\.(txt|md)$",
    exclude_names=["README.md"],
    on_conflict="rename",
    verbose=True
)
```

###  Explanation

* Copies only `.txt` and `.md` files
* Skips `"README.md"`
* If a file already exists, renames the new one to avoid overwrite
* Logs will show in the terminal

##

##  Example: `move_files()` 

```python
from fylex import move_files

move_files(
    src="raw_images",
    dest="processed_images",
    match_glob="*.png",
    dry_run=True,
    summary="move_summary.log"
)
```

###  Explanation

* Moves all `.png` files (simulated due to `dry_run=True`)
* Outputs actions to `move_summary.log`
* Existing files are not overwritten by default

##

##  Combined Filtering Example

```python
copy_files(
    src="data",
    dest="backup",
    match_glob="*.csv",
    match_regex=r"(?i)^data_\d{4}\.csv$",
    exclude_glob="*_old.csv",
    on_conflict="larger"
)
```

###  Explanation

* Includes files like `data_2023.csv` or `DATA_2022.csv`
* Excludes those matching `*_old.csv`
* Replaces destination file only if the source is larger

##

## Conflict Handling Modes

| Mode      | Behavior                            |
| --------- | ----------------------------------- |
| `larger`  | Keep the larger file                |
| `smaller` | Keep the smaller file               |
| `newer`   | Keep the more recently modified     |
| `older`   | Keep the older one                  |
| `rename`  | Renames new file like `name(1).ext` |
| `skip`    | Skips the file silently             |
| `prompt`  | Asks the user for each conflict     |

##

##  Interactive Example

```python
copy_files(
    src="docs",
    dest="usb",
    interactive=True,
    verbose=True
)
```

###  Explanation

* Asks for confirmation on each file copy
* Shows logs in the terminal

##

##  Parallelism Example

```python
move_files(
    src="media",
    dest="external_drive",
    max_workers=8
)
```

###  Explanation

* Moves files using 8 threads for speed
* Ensures verification with hash+size match

##

##  Logging and Summary

```python
copy_files(
    src="music",
    dest="phone",
    summary="music_transfer.log",
    verbose=False
)
```

* Logs written to `fylex.log` and copied to `music_transfer.log`
* Console stays silent (`verbose=False`)

##

##  Junk Filtering (Advanced Use)

Use `JUNK_EXTENSIONS` with `exclude_names` or `exclude_glob`:

```python
from fylex import copy_files, JUNK_EXTENSIONS

copy_files(
    src="project",
    dest="clean_project",
    exclude_glob="*"+",".join(JUNK_EXTENSIONS["temporary_backup"]),
    on_conflict="skip"
)
```

##

##  Single File Example

```python
copy_files(
    src="mydoc.txt",
    dest="~/backup/",
    verbose=True
)
```

* Handles single files by treating parent as `src` and filtering by name


##

##  Installation

Install via PyPI:

```bash
pip install fylex
```

Or install from source:

```bash
git clone https://github.com/Crystallinecore/fylex
cd fylex
pip install .
```

##

##  Dependencies

* Python 3.8+
* `xxhash`: For high-speed hashing

```bash
pip install xxhash
```

##

## License

MIT License © Sivaprasad Murali — https://github.com/Crystallinecore/fylex

xxHash used under BSD License — [https://github.com/Cyan4973/xxHash](https://github.com/Cyan4973/xxHash)

##

##  Author

**Sivaprasad Murali** —
[sivaprasad.off@gmail.com](mailto:sivaprasad.off@gmail.com)


##
>  *“Your files. Your rules. Just smarter.”*
##


