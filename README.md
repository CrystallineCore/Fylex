---

# fylex

**Smart, Fast & Customizable File Copier**
A Python-based file copying utility with hashing, filtering, multi-threading, and intelligent conflict resolution. Designed for developers, data engineers, and power users.

---

##  What is `fylex`?

`fylex` is a command-line tool and Python module that simplifies and enhances the task of copying files and directories. Unlike standard copy tools, `fylex` offers powerful filtering options, safe hashing to avoid redundant operations, multi-threaded execution for performance, and customizable conflict handling strategies.

---

##  Features with Examples

---

### 1. **Hash-Based Copying (xxHash)**

Files are compared using **fast checksums** to avoid copying files that already exist unchanged.

**Example:**
```bash
fylex --src ./project --dest ./backup
````

If files in `project/` already exist in `backup/` with the same content, `fylex` skips them.

---

### 2. **File Filtering with Regex and Glob**

#### 🔹 Include only `.txt` files using glob:

```bash
fylex --match-glob '*.txt' --src ./src --dest ./dest
```

#### 🔹 Use regex to copy only files with digits:

```bash
fylex --match-regex '.*\d+.*\.txt$' --src ./logs --dest ./data
```

#### 🔹 Exclude by filename list:

```bash
fylex --exclude-names temp.txt,debug.log --src ./src --dest ./dest
```

Combine multiple filters to fine-tune your selection.

---

### 3. **Conflict Resolution Modes**

Specify what happens if a file with the same name already exists at the destination:

| Mode    | Description                          |
| ------- | ------------------------------------ |
| replace | Overwrite the existing file          |
| skip    | Skip copying this file               |
| rename  | Create a new name like `file(1).txt` |
| newer   | Keep the newest version              |
| older   | Keep the older version               |
| larger  | Keep the larger file                 |
| smaller | Keep the smaller file                |
| prompt  | Ask the user what to do              |

**Example (rename on conflict):**

```bash
fylex --on-conflict rename --src ./files --dest ./archive
```

---

### 4. **Interactive Mode**

Prompts the user before copying each file. Ideal when you need precise control.

```bash
fylex --interactive --src ./important --dest ./external_drive
```

---

### 5. **Dry Run Mode**

Simulates the entire copy process without actually moving files. Very useful for testing.

```bash
fylex --dry-run --src ./project --dest ./backup
```

Output will show which files would be copied or skipped, without changing anything.

---

###  6. **Multithreaded Copying**

Use all available CPU cores (or specify how many) to speed up the copying of many files.

```bash
fylex --max-workers 8 --src ./bigdata --dest ./transfer
```

---

###  7. **(File-Based) Copying with Custom Folder Support**

`fylex` currently operates on **files only** — directories themselves are **not copied recursively** by default.

However, users can easily walk through directories using Python and pass files to `fylex` programmatically.

#### Example: Recursively Copy an Entire Directory Tree

You can combine `fylex.smart_copy()` with Python’s `os.walk()` to copy all files while preserving the directory structure:

```python
import os
from fylex import smart_copy

src_root = "./mydir"
dest_root = "./backup"

for root, _, files in os.walk(src_root):
    for file in files:
        abs_src_dir = root
        rel_path = os.path.relpath(root, src_root)
        dest_dir = os.path.join(dest_root, rel_path)

        smart_copy(
            src=abs_src_dir,
            dest=dest_dir,
            match_names=[file],
            on_conflict="rename",  # or 'skip', 'prompt', etc.
            interactive=False,
            max_workers=4
        )
```

This allows `fylex` to:

* Walk through all nested directories
* Preserve folder structure
* Avoid unnecessary copies using hash-based checks
* Apply your desired conflict strategy

> In future releases, native support for recursive directory copying will be included.

---

###  8. **Preserve File Metadata**

`fylex` uses `shutil.copy2()` which retains:

* Access/modification times
* File permissions (on Unix)
* File ownership (when permitted)

This is done **automatically** — no flags needed.

---

###  9. **Logging and Summary Files**

Enable verbose logging to console, and optionally save logs to a file.

```bash
fylex --verbose --summary logs/summary.log --src ./src --dest ./dest
```

This generates a human-readable log with all actions taken by `fylex`.

---

## Installation

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

---

##  Full Command Reference

```bash
fylex [OPTIONS]
```

| Option                                                 | Description                                 |
| ------------------------------------------------------ | ------------------------------------------- |
| `--src`                                                | Source directory or file                    |
| `--dest`                                               | Destination directory                       |
| `--match-regex`                                        | Regex pattern to include                    |
| `--match-glob`                                         | Glob pattern to include                     |
| `--match-names`                                        | Comma-separated filenames to include        |
| `--exclude-regex`, `--exclude-glob`, `--exclude-names` | Filters to exclude files                    |
| `--on-conflict`                                        | Conflict strategy (`replace`, `skip`, etc.) |
| `--interactive`                                        | Ask user before copying each file           |
| `--dry-run`                                            | Simulate without copying                    |
| `--max-workers`                                        | Number of threads to use                    |
| `--summary`                                            | Output log file                             |
| `--verbose`                                            | Show log messages in terminal               |

---

##  Dependencies

* Python 3.8+
* `xxhash` (for ultra-fast hashing)

Install with:

```bash
pip install xxhash
```

---

##  License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for full terms.

> xxhash is used under BSD License. Visit [https://github.com/Cyan4973/xxHash](https://github.com/Cyan4973/xxHash) for details.

---

## Author

**Sivaprasad Murali:**
 [sivaprasad.off@gmail.com](mailto:sivaprasad.off@gmail.com)

---

##  Why fylex Might Be the Best in Market
✔ Combines glob, regex, and name filtering — most tools support only one.

✔ Detects duplicates based on content hashing, not metadata.

✔ Re-hashes and verifies the copies to ensure data integrity.

✔ Conflict resolution goes **beyond overwrite/skip** — with logic-based decisions.

✔ No platform lock-in — works on **Linux**, **Windows**, and **macOS**.

✔ Clean API structure for future expansion (GUI, networking, etc.)

✔ Practical logging and dry-run mode — rarely seen in open-source file tools.

✔ Performance boost via parallel threads and fast hashing.


---

> "Don’t just copy. fylex it."

---
