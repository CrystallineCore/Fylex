import argparse
import sys
from .fylex import smart_copy
from .exceptions import fylexError

def parse_args():
    parser = argparse.ArgumentParser(description="Fylex: A smart file copying mechanism using hashes", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    #group = parser.add_mutually_exclusive_group()
    # Positional arguments
    parser.add_argument("src", help="Source directory or file")
    parser.add_argument("dest", help="Destination directory")
    
    # Optional flags and options
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")
    parser.add_argument("--no-create", action="store_true", help="Does not create directories when destination path is non-existent")
    parser.add_argument("--match-regex", help="Regular expression to match filenames", default="")
    parser.add_argument("--match-glob", help="Glob expression to match filenames", default="")
    parser.add_argument("--match-names", nargs="+", help="List of filenames to copy", default=[])
    parser.add_argument("--exclude-regex", help="Regular expression to exclude filenames", default=None)
    parser.add_argument("--exclude-glob", help="Glob expression to exclude filenames", default=None)
    parser.add_argument("--exclude-names", nargs="+", help="List of filenames to exclude", default=[])
    parser.add_argument("--on-conflict", choices=["larger", "smaller", "newer", "older", "rename", "skip", "prompt"], 
                        help="Action on filename conflict")
    parser.add_argument("--summary", default=None, help="Summarizes the actions in a log file at this path")
    parser.add_argument("--max-workers", type=int, default=4, help="Number of threads to use for copying")
    
    return parser.parse_args()

def main():
    args = parse_args()
    try:
        if args.dry_run and args.interactive:
            parser.error("Cannot use --dry-run with --interactive mode.")
        smart_copy(
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
        )
    except FylexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

