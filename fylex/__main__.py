import argparse
import sys
from .fylex import filecopy, filemove, undo, redo, FylexConfig


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fylex: A smart linux file utility tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---------------- Copy ----------------
    copy_parser = subparsers.add_parser("copy", help="Smartly copy files with hashing, filters, and conflict resolution")
    copy_parser.add_argument("src", help="Source directory or file")
    copy_parser.add_argument("dest", help="Destination directory")
    copy_parser.add_argument("--resolve", choices=FylexConfig.ON_CONFLICT_MODES, default="rename",
                             help="Conflict resolution strategy")
    copy_parser.add_argument("--algo", default=FylexConfig.DEFAULT_HASH_ALGO,
                             help="Hash algorithm (xxhash, blake3, md5, sha256, sha512)")
    copy_parser.add_argument("--chunk-size", type=int, default=FylexConfig.DEFAULT_CHUNK_SIZE,
                             help="Read buffer size in bytes")
    copy_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    copy_parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")
    copy_parser.add_argument("--summary", default=None, help="Path to save a summary copy of the log")
    copy_parser.add_argument("--match-regex", default=None, help="Regex to match filenames")
    copy_parser.add_argument("--match-names", nargs="+", default=None, help="Exact filenames to match")
    copy_parser.add_argument("--match-glob", nargs="+", default=None, help="Glob patterns to match filenames")
    copy_parser.add_argument("--exclude-regex", default=None, help="Regex to exclude filenames")
    copy_parser.add_argument("--exclude-names", nargs="+", default=None, help="Exact filenames to exclude")
    copy_parser.add_argument("--exclude-glob", nargs="+", default=None, help="Glob patterns to exclude")
    copy_parser.add_argument("--recursive-check", action="store_true", help="Check duplicates recursively in destination")
    copy_parser.add_argument("--verify", action="store_true", help="Verify copy by comparing hashes")
    copy_parser.add_argument("--has-extension", action="store_true", help="Consider file extension when checking duplicates")
    copy_parser.add_argument("--no-create", action="store_true", help="Do not create destination directory if missing")
    preserve_group = copy_parser.add_mutually_exclusive_group()
    preserve_group.add_argument("--preserve-meta", dest="preserve_meta", action="store_true",
                                help="Preserve metadata (mtime, permissions, xattrs, ACLs)")
    preserve_group.add_argument("--no-preserve-meta", dest="preserve_meta", action="store_false",
                                help="Do not preserve metadata")
    copy_parser.set_defaults(preserve_meta=True)
    copy_parser.add_argument("--backup", default="fylex.deprecated", help="Backup folder for replaced files")
    copy_parser.add_argument("--recurse", action="store_true", help="Traverse subdirectories")

    # ---------------- Move ----------------
    move_parser = subparsers.add_parser("move", help="Smartly move files with hashing, filters, and conflict resolution")
    move_parser.add_argument("src", help="Source directory or file")
    move_parser.add_argument("dest", help="Destination directory")
    move_parser.add_argument("--resolve", choices=FylexConfig.ON_CONFLICT_MODES, default="rename",
                             help="Conflict resolution strategy")
    move_parser.add_argument("--algo", default=FylexConfig.DEFAULT_HASH_ALGO,
                             help="Hash algorithm (xxhash, blake3, md5, sha256, sha512)")
    move_parser.add_argument("--chunk-size", type=int, default=FylexConfig.DEFAULT_CHUNK_SIZE,
                             help="Read buffer size in bytes")
    move_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    move_parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")
    move_parser.add_argument("--summary", default=None, help="Path to save a summary copy of the log")
    move_parser.add_argument("--match-regex", default=None, help="Regex to match filenames")
    move_parser.add_argument("--match-names", nargs="+", default=None, help="Exact filenames to match")
    move_parser.add_argument("--match-glob", nargs="+", default=None, help="Glob patterns to match filenames")
    move_parser.add_argument("--exclude-regex", default=None, help="Regex to exclude filenames")
    move_parser.add_argument("--exclude-names", nargs="+", default=None, help="Exact filenames to exclude")
    move_parser.add_argument("--exclude-glob", nargs="+", default=None, help="Glob patterns to exclude")
    move_parser.add_argument("--recursive-check", action="store_true", help="Check duplicates recursively in destination")
    move_parser.add_argument("--verify", action="store_true", help="Verify move by comparing hashes")
    move_parser.add_argument("--has-extension", action="store_true", help="Consider file extension when checking duplicates")
    move_parser.add_argument("--no-create", action="store_true", help="Do not create destination directory if missing")
    preserve_group = move_parser.add_mutually_exclusive_group()
    preserve_group.add_argument("--preserve-meta", dest="preserve_meta", action="store_true",
                                help="Preserve metadata (mtime, permissions, xattrs, ACLs)")
    preserve_group.add_argument("--no-preserve-meta", dest="preserve_meta", action="store_false",
                                help="Do not preserve metadata")
    move_parser.set_defaults(preserve_meta=True)
    move_parser.add_argument("--backup", default="fylex.deprecated", help="Backup folder for replaced files")
    move_parser.add_argument("--recurse", action="store_true", help="Traverse subdirectories")

    # ---------------- Undo ----------------
    undo_parser = subparsers.add_parser("undo", help="Undo a previous fylex process")
    undo_parser.add_argument("process_id", help="Process ID to undo")
    undo_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    undo_parser.add_argument("--force", action="store_true", help="Force undo even if errors occur")
    undo_parser.add_argument("--summary", default=None, help="Path to save a summary copy of the log")
    undo_parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")

    # ---------------- Redo ----------------
    redo_parser = subparsers.add_parser("redo", help="Redo a previous fylex process")
    redo_parser.add_argument("process_id", help="Process ID to redo")
    redo_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    redo_parser.add_argument("--force", action="store_true", help="Force redo even if errors occur")
    redo_parser.add_argument("--summary", default=None, help="Path to save a summary copy of the log")
    redo_parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        if args.command == "copy":
            filecopy(
                src=args.src,
                dest=args.dest,
                resolve=args.resolve,
                algo=args.algo,
                chunk_size=args.chunk_size,
                verbose=args.verbose,
                dry_run=args.dry_run,
                summary=args.summary,
                match_regex=args.match_regex,
                match_names=args.match_names,
                match_glob=args.match_glob,
                exclude_regex=args.exclude_regex,
                exclude_names=args.exclude_names,
                exclude_glob=args.exclude_glob,
                recursive_check=args.recursive_check,
                verify=args.verify,
                has_extension=args.has_extension,
                no_create=args.no_create,
                preserve_meta=args.preserve_meta,
                backup=args.backup,
                recurse=args.recurse,
            )

        elif args.command == "move":
            filemove(
                src=args.src,
                dest=args.dest,
                resolve=args.resolve,
                algo=args.algo,
                chunk_size=args.chunk_size,
                verbose=args.verbose,
                dry_run=args.dry_run,
                summary=args.summary,
                match_regex=args.match_regex,
                match_names=args.match_names,
                match_glob=args.match_glob,
                exclude_regex=args.exclude_regex,
                exclude_names=args.exclude_names,
                exclude_glob=args.exclude_glob,
                recursive_check=args.recursive_check,
                verify=args.verify,
                has_extension=args.has_extension,
                no_create=args.no_create,
                preserve_meta=args.preserve_meta,
                backup=args.backup,
                recurse=args.recurse,
            )

        elif args.command == "undo":
            undo(
                p_id=args.process_id,
                verbose=args.verbose,
                force=args.force,
                summary=args.summary,
                dry_run=args.dry_run,
            )

        elif args.command == "redo":
            redo(
                p_id=args.process_id,
                verbose=args.verbose,
                force=args.force,
                summary=args.summary,
                dry_run=args.dry_run,
            )
    except ValueError as e:
        print(f"Argument Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
