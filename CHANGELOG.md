

# 📦 CHANGELOG

## \[0.3.2] - 2025-06-11

### 🔁 Major Enhancements



The `recursive_check` flag allows `fylex` to **scan the destination directory recursively** to detect if any of the source files already exist **anywhere inside the destination tree**, even in nested subdirectories.

#### ✅ When Enabled (`recursive_check=True`)

* `fylex` uses `Path.rglob("*")` to **recursively traverse the destination folder**.
* It checks the hash and size of **all files**, not just those in the top-level destination directory.
* If a file from the source already exists **anywhere in the destination tree** (based on content, not just name).
* Prevents duplicate copies even when the destination is deeply structured or already contains organized data.

#### 🚫 When Disabled (`recursive_check=False`)

* Only the **top-level of the destination** is scanned for possible conflicts.
* Faster, but may allow duplicate content to be copied into subdirectories if not explicitly filtered.

#### 🧠 Why It Matters

This feature is essential when:

* You're syncing scattered files to a nested archive.
* You want to ensure a file is **not already present anywhere** in the destination.
* You care about **content-level deduplication** beyond just name-based checks.

#### 🧪 Example:

```python
fylex.copy_files(
    src="/media/dump",
    dest="/archive/yearly/",
    recursive_check=True,
    match_regex=r".*\.(jpg|png)$",
    on_conflict="rename",
    dry_run=True
)
```

In this example, even if `file123.jpg` already exists in a deep subfolder of `/archive/yearly/`, `fylex` will detect it and handle the conflict accordingly.

---

## \[0.3.1] - 2025-06-10
* **Improved Nest Filtering System**

  * Nest filters are now based on `(file_size, suffix)` or just `file_size`, dynamically switching based on `has_extension` flag.
  * Prevents duplicate work when handling multiple similar files with common extensions.

##
### 🧼 Junk File Detection

* Junk file categories like `temporary_backup`, `system_log`, `dev_artifacts`, etc., now structured for future smart deletion/skip features.

---
## [0.1.0 - 0.3.0] - 2025-05-28

* Initial release of `fylex` with:

  * Fast hash-based file comparison
  * Smart multithreaded copy engine
  * Regex, name, glob filtering
  * Basic logger and validator

---
