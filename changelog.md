---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Version 1.2.4

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

## Version 1.2.3

* **Bug Fixes**

  * In versions ≤ 1.2.2, duplicates within the source directory were not detected when verification was disabled.
  * In versions ≥ 1.2.3, duplicates within the source directory are correctly detected and skipped, preventing them from being copied or moved unnecessarily.

* **Changes**

  * JSON files are now stored along with the database files in the .fylex folder inside the user's home directory.

---
