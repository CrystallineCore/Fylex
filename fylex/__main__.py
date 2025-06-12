import argparse
import sys
from .fylex import copy_files, move_files, spill, flatten, ON_CONFLICT_MODES
from .exceptions import FylexError

def parse_args():
    parser = argparse.ArgumentParser(
        description="Fylex: A smart file utility tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # ---------------- Copy Subcommand ----------------
    copy_parser = subparsers.add_parser("copy_files", help="Smartly copy files using hashing and filters")

    copy_parser.add_argument("src", help="Source directory or file")
    copy_parser.add_argument("dest", help="Destination directory")
    copy_parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    copy_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    copy_parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")
    copy_parser.add_argument("--delta-copy", action="store_true", help="Performs fast delta-copy")
    copy_parser.add_argument("--no-create", action="store_true", help="Don't create destination dirs")
    copy_parser.add_argument("--match-regex", default="", help="Regex to match filenames")
    copy_parser.add_argument("--match-glob", default="", help="Glob to match filenames")
    copy_parser.add_argument("--match-names", nargs="+", default=[], help="List of exact filenames to match")
    copy_parser.add_argument("--exclude-regex", default=None, help="Regex to exclude filenames")
    copy_parser.add_argument("--exclude-glob", default=None, help="Glob to exclude filenames")
    copy_parser.add_argument("--exclude-names", nargs="+", default=[], help="List of filenames to exclude")
    copy_parser.add_argument("--on-conflict", choices=["larger", "smaller", "newer", "older", "rename", "skip", "prompt", "replace"], 
                             help="Action on filename conflict")
    copy_parser.add_argument("--summary", default=None, help="Summary log path")
    copy_parser.add_argument("--max-workers", type=int, default=4, help="Number of threads to use")
    copy_parser.add_argument("--recursive-check", type=bool, default=False, help="Whether to check directories recursively for file existence")
    copy_parser.add_argument("--has-extension", type=bool, default=False, help="Whether these files have extensions")

    # ---------------- Move Subcommand ----------------
    move_parser = subparsers.add_parser("move_files", help="Smartly move files using hashing and filters")

    move_parser.add_argument("src", help="Source directory or file")
    move_parser.add_argument("dest", help="Destination directory")
    move_parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    move_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    move_parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")
    move_parser.add_argument("--no-create", action="store_true", help="Don't create destination dirs")
    move_parser.add_argument("--match-regex", default="", help="Regex to match filenames")
    move_parser.add_argument("--match-glob", default="", help="Glob to match filenames")
    move_parser.add_argument("--match-names", nargs="+", default=[], help="List of exact filenames to match")
    move_parser.add_argument("--exclude-regex", default=None, help="Regex to exclude filenames")
    move_parser.add_argument("--exclude-glob", default=None, help="Glob to exclude filenames")
    move_parser.add_argument("--exclude-names", nargs="+", default=[], help="List of filenames to exclude")
    move_parser.add_argument("--on-conflict", choices=["larger", "smaller", "newer", "older", "rename", "skip", "prompt", "replace"], 
                             help="Action on filename conflict")
    move_parser.add_argument("--summary", default=None, help="Summary log path")
    move_parser.add_argument("--max-workers", type=int, default=4, help="Number of threads to use")
    move_parser.add_argument("--recursive-check", type=bool, default=False, help="Whether to check directories recursively for file existence")
    move_parser.add_argument("--has-extension", type=bool, default=False, help="Whether these files have extensions")

    # ---------------- Refine Subcommand ----------------
    refine_parser = subparsers.add_parser("refine_files", help="Refine a directory")

    refine_parser.add_argument("target", help="Target directory to refine")
    refine_parser.add_argument("--strategy", choices=["dedup", "clean", "sort"], default="dedup", help="Refinement strategy")
    refine_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # ---------------- Spill Subcommand ----------------
    spill_parser = subparsers.add_parser("spill", help="Spills selective contents from a directory")

    spill_parser.add_argument("target", help="Target directory to refine")
    spill_parser.add_argument("--on-conflict", choices=["larger", "smaller", "newer", "older", "rename", "skip", "prompt", "replace"], 
                             help="Action on filename conflict")
    spill_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    spill_parser.add_argument("--summary", default=None, help="Summary log path")
    spill_parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")
    spill_parser.add_argument("--match-regex", default="", help="Regex to match filenames")
    spill_parser.add_argument("--match-glob", default="", help="Glob to match filenames")
    spill_parser.add_argument("--match-names", nargs="+", default=[], help="List of exact filenames to match")
    spill_parser.add_argument("--exclude-regex", default=None, help="Regex to exclude filenames")
    spill_parser.add_argument("--exclude-glob", default=None, help="Glob to exclude filenames")
    spill_parser.add_argument("--exclude-names", nargs="+", default=[], help="List of filenames to exclude")
    spill_parser.add_argument("--levels", type=int, default=-1, help="Number of threads to use")
    spill_parser.add_argument("--max-workers", type=int, default=4, help="Number of threads to use")

    # ---------------- Flatten Subcommand ----------------
    flatten_parser = subparsers.add_parser("flatten", help="Spills selective contents from a directory")

    flatten_parser.add_argument("target", help="Target directory to refine")
    flatten_parser.add_argument("--on-conflict", choices=["larger", "smaller", "newer", "older", "rename", "skip", "prompt", "replace"], 
                             help="Action on filename conflict")
    flatten_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    flatten_parser.add_argument("--summary", default=None, help="Summary log path")
    flatten_parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")
    flatten_parser.add_argument("--max-workers", type=int, default=4, help="Number of threads to use")

    return parser.parse_args()

def main():
    args = parse_args()

    try:
        if args.command == "copy_files":
            if args.dry_run and args.interactive:
                raise ValueError("Cannot use --dry-run with --interactive mode.")

            copy_files(
                src=args.src,
                dest=args.dest,
                interactive=args.interactive,
                dry_run=args.dry_run,
                no_create=args.no_create,
                match_regex=args.match_regex,
                match_names=args.match_names,
                match_glob=args.match_glob,
                exclude_regex=args.exclude_regex,
                exclude_names=args.exclude_names,
                exclude_glob=args.exclude_glob,
                on_conflict=args.on_conflict,
                summary=args.summary,
                max_workers=args.max_workers,
                verbose=args.verbose,
                recursive_check=args.recursive_check,
                has_extension=args.has_extension
            )
        
        elif args.command == "move_files":
            if args.dry_run and args.interactive:
                raise ValueError("Cannot use --dry-run with --interactive mode.")

            move_files(
                src=args.src,
                dest=args.dest,
                interactive=args.interactive,
                dry_run=args.dry_run,
                no_create=args.no_create,
                match_regex=args.match_regex,
                match_names=args.match_names,
                match_glob=args.match_glob,
                exclude_regex=args.exclude_regex,
                exclude_names=args.exclude_names,
                exclude_glob=args.exclude_glob,
                on_conflict=args.on_conflict,
                summary=args.summary,
                max_workers=args.max_workers,
                verbose=args.verbose
                recursive_check=args.recursive_check,
                has_extension=args.has_extension
            )

    except FylexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()

