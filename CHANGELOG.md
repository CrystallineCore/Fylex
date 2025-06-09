# Changelog

## [0.1.2] – 2025-06-09

### Fixed
- 🐞 **Resolved critical bug where the same source and destination path would lead to unexpected behavior.**
  - The module now correctly detects when the source and destination are identical, and halts the operation with a clear error message.
  - Added normalization using `Path.resolve()` to ensure paths are compared accurately across relative/absolute formats and symlinks.
