

# Fylex: Linux file deduplication toolkit

[![PyPI](https://img.shields.io/pypi/v/fylex.svg)](https://pypi.org/project/fylex/)
[![Python 3.x](https://img.shields.io/badge/Python-3.x-orange.svg)](https://www.python.org/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/fylex?period=total\&units=INTERNATIONAL_SYSTEM\&left_color=black\&right_color=green\&left_text=downloads)](https://pepy.tech/projects/fylex)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Socket Badge](https://badge.socket.dev/pypi/package/fylex/1.2.2?artifact_id=tar-gz)](https://badge.socket.dev/pypi/package/fylex/1.2.4?artifact_id=tar-gz)
---

**Fylex** is a **production-ready, Linux-tailored file management tool** that combines the best of `rsync`, `cp`, and Python’s `shutil` — but goes **beyond** with:

* **Smart Copy & Move** with hashing (xxhash, blake3, SHA, MD5)
* **Advanced conflict resolution** (rename, skip, replace, larger/smaller, newer/older, prompt)
* **Filters**: regex, glob, exact filename matches, inclusion/exclusion
* **Safety nets**: undo, redo, backup of deprecated files
* **Data integrity**: hash verification, SQLite-backed hash cache for deduplication
* **Metadata preservation**: permissions, timestamps, xattrs, ACLs (Linux-specific)
* **CLI & Python API** for flexible usage

---

## What’s New in version 1.2.4

* **Bug Fixes**

  * `FYLEX_HOME` directory was created on disk at import time (inside the class body), breaking environments where `~/.fylex` should not be created eagerly. It is now created lazily on first use via `_ensure_fylex_home()`.

  * `fast_move` called `.unlink()` directly on its `src` argument without first casting it to `Path`, causing an `AttributeError` crash when `src` was passed as a string.

  * `try_remove` had the same uncast `Path | str` bug, also crashing with `AttributeError` when passed a string path.

  * In `copy_with_conflict_resolution`, the skip-branch for `move` operations constructed the deprecated-file destination by treating `src` (a file path) as a directory, producing nonsensical paths like `/path/to/file.txt/fylex.deprecated/…`. The destination is now correctly built from the `backup` directory.

  * `undo` and `redo` both silently returned a `ValueError` instance as a value instead of raising it. The dead `except ValueError` block (which could never be triggered by `dict.get()`) has been removed and the entries are now assigned directly.

  * `redo` returned `False` when no JSON record was found for a process ID, while the symmetric `undo` function returned `-1` for the same condition. `redo` now returns `-1` for consistency.

  * `redo` logged a `[UNDO]` prefix in its dry-run skip warning. The prefix has been corrected to `[REDO]`.

  * After a `replace`-mode conflict resolution, `dupe_candidates` was updated with the hash and size of `save_as` (the backup path holding the *old* file) rather than `dest_file` (the path where the new file was actually written). Future duplicates of the newly copied file therefore went undetected. The hash tracking now correctly references `dest_file`.

---

## Feature comparison

| Feature / Tool             | Fylex                                                                  | cp (coreutils)                | rsync                                             | shutil (Python stdlib)    |
| -------------------------- | ---------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------- | ------------------------- |
| Primary purpose            | Smart local copy/move with safety nets                                 | Basic copy                    | Fast sync (local/remote)                          | Library-level file ops    |
| Undo / Redo                | Yes — built-in JSON journaling                                         | No                            | No                                                | No                        |
| Hash verification          | Yes — xxhash, blake3, sha256, etc.                                     | No                            | Partial — checksums optional                      | No                        |
| Hash cache (SQLite)        | Yes — avoids rehashing unchanged files                                 | No                            | No                                                | No                        |
| Duplicate detection (dest) | Yes — size + hash                                                      | No                            | Partial — based on size/checksums                 | No                        |
| Conflict resolution        | Extensive — rename, replace, skip, newer/older, larger/smaller, prompt | None — overwrite only         | Limited — flags like `--backup`, `--suffix`       | None                      |
| Metadata preservation      | Yes — mtime, perms, xattrs, ACLs on Linux                              | Partial — `-a` preserves many | Partial — `-a` preserves many                     | Partial — `copystat` only |
| Atomic writes              | Yes — via `fylex.tmp`                                                  | No                            | Partial — temp options exist                      | No                        |
| Logging / audit trail      | Yes — JSON logs per process                                            | No                            | Partial — verbose logs only                       | No                        |
| CLI + Python API           | Yes — both                                                             | CLI only                      | CLI only (bindings exist)                         | Python API only           |
| Delta transfer (network)   | No — local only                                                        | No                            | Yes                                               | No                        |
| Remote / cloud support     | No — local-first                                                       | No                            | Yes — ssh/rsyncd                                  | No                        |
| Cross-platform             | Partial — Linux-first (xattrs/ACL best)                                | Yes                           | Yes                                               | Yes                       |
| Performance (local)        | Very good — uses `copy_file_range` / `sendfile`                        | Good                          | Very good — efficient I/O                         | Moderate                  |
| Learning curve             | Moderate — many options                                                | Very low                      | Moderate to high — many options                   | Low                       |
| Best fit                   | Local integrity-critical workflows, reversible ops                     | Quick one-off copies          | Local/remote sync and bandwidth-efficient backups | Small Python scripts      |

---

## Strengths

* **Undo / Redo** — Reversible operations by process ID.
* **JSON audit trail** — Logs stored per PID for reproducibility.
* **Hash verification + cache** — Prevents rehashing unchanged files.
* **Conflict resolution** — Multiple real-world strategies (rename, replace, skip, larger/smaller, newer/older, prompt).
* **Linux metadata handling** — Preserves xattrs/ACLs.
* **Atomic writes & backups** — Prevents partial corruption.
* **Good performance** — Uses `copy_file_range`/`sendfile`.

---

## Safety Nets

* **Undo**: Rollback any process (`undo(pid)`).
* **Redo**: Replay exactly (`redo(pid)`).
* **Backups**: Deprecated files → `fylex.deprecated/{pid}/`.
* **Logs**: JSON + JSONL under `json/{pid}.json`.
* **Verification**: Optional hash verification (`--verify`).
* **Retries**: Up to 5 retries on hash mismatch.
* **Protections**: Prevents unsafe recursive/self copies.

---

## Installation

```bash
pip install fylex
```

Requires **Python 3.8+**.
Linux recommended (for full xattr/ACL support).

---



## CLI Usage

### Copy

```bash
fylex copy ~/Downloads ~/Backup --resolve rename --algo xxhash --verify --verbose
```

### Move

```bash
fylex move ./data ./archive --resolve newer --match-glob "*.csv"
```

### Undo / Redo

```bash
fylex undo 1002
fylex redo 1002
```

---

## Python API

```python
from fylex import filecopy, filemove, undo, redo

# Copy with conflict resolution
pid = filecopy("photos", "backup/photos", resolve="newer", match_glob="*.png", verify=True)

# Undo
undo(pid)

# Move and undo in one line
undo(filemove("docs", "docs_archive", resolve="rename"))
```

---

##  Function Reference

### `filecopy(src, dest, ...)`

**Description:** Smartly copies files from `src` to `dest` with conflict handling, filters, and safety nets.

| Param             | Type         | Default              | Description                                                                                     |
| ----------------- | ------------ | -------------------- | ----------------------------------------------------------------------------------------------- |
| `src`             | `str\|Path` | required             | Source file or directory                                                                        |
| `dest`            | `str\|Path` | required             | Destination directory                                                                           |
| `resolve`         | `str`        | `"rename"`           | Conflict strategy: `rename`, `replace`, `skip`, `larger`, `smaller`, `newer`, `older`, `prompt` |
| `algo`            | `str`        | `"xxhash"`           | Hash algorithm: `xxhash`, `blake3`, `md5`, `sha256`, `sha512`                                   |
| `chunk_size`      | `int`        | `16 * 1024 * 1024`   | Buffer size (bytes) for reading files                                                           |
| `verbose`         | `bool`       | `True`               | Log operations to stdout                                                                        |
| `dry_run`         | `bool`       | `False`              | Simulate actions without making changes                                                         |
| `summary`         | `str\|Path` | `None`               | Path to copy `fylex.log` summary                                                                |
| `match_regex`     | `str`        | `None`               | Regex pattern to include files                                                                  |
| `match_names`     | `list[str]`  | `None`               | Exact filenames to include                                                                      |
| `match_glob`      | `list[str]`  | `None`               | Glob patterns to include                                                                        |
| `exclude_regex`   | `str`        | `None`               | Regex pattern to exclude files                                                                  |
| `exclude_names`   | `list[str]`  | `None`               | Exact filenames to exclude                                                                      |
| `exclude_glob`    | `list[str]`  | `None`               | Glob patterns to exclude                                                                        |
| `recursive_check` | `bool`       | `False`              | Deduplication check recursively in `dest`                                                       |
| `verify`          | `bool`       | `False`              | Verify file hashes after copying                                                                |
| `has_extension`   | `bool`       | `False`              | Include file extension in deduplication check                                                   |
| `no_create`       | `bool`       | `False`              | Do not create `dest` if it does not exist                                                       |
| `preserve_meta`   | `bool`       | `True`               | Preserve timestamps, permissions, xattrs, ACLs                                                  |
| `backup`          | `str\|Path` | `"fylex.deprecated"` | Folder for deprecated or conflicting files                                                      |
| `recurse`         | `bool`       | `False`              | Traverse subdirectories in `src`                                                                |

**Example:**

```python
filecopy("photos", "photos_backup", resolve="newer", match_glob="*.png", verify=True)
```

##

### `filemove(src, dest, ...)`

Same params as `filecopy`, but moves files instead.
If conflicts exist, originals are moved into deprecated folders within `src` or `dest` depending on the origin of the file being deprecated.

##

### `undo(p_id, verbose=True, force=False)`

Rollback a process by ID.

| Param     | Type   | Description                             |
| --------- | ------ | --------------------------------------- |
| `p_id`    | `str`  | Process ID (JSON log ID)                |
| `verbose` | `bool` | Enable logs                             |
| `force`   | `bool` | Continue undo even if some entries fail |
| `summary`   | `str \| Path` | Path to copy fylex.log summary |
| `dry_run`   | `bool` | Dry run feature to simulate operations |

##

### `redo(p_id, verbose=True, force=False)`

Replay a process by ID. Same parameters as `undo`.




---

## Migration Notes

* **Old behavior:**

  ```python
  success = filecopy("a", "b")  # returns True/False
  ```
* **New behavior (>=v1.2.0):**

  ```python
  pid = filecopy("a", "b")      # returns process ID
  undo(pid)                     # reversible
  ```

Update your code to capture process IDs instead of expecting booleans.

---

## Example Workflows

### Daily backup with rollback

```bash
fylex copy ~/work ~/backup --resolve newer --verify
# Oops
fylex undo 2023
```

### Reproducible replay

```bash
fylex redo 2023
```

### Direct chaining in Python

```python
fx.undo(fx.filemove("src/data", "archive/data"))
```

---

## License

MIT © 2025 Sivaprasad Murali

---

✨ With **Fylex**, file management on Linux is no longer just copying and moving — it’s **safe, verifiable, reversible, and smart**.

---


