from __future__ import annotations

import argparse
import sys
from typing import List

from .config import load_settings
from .insta import build_loader, download_by_url, login as ig_login
from .log import get_console, info, warn, error, success
from .urltools import shortcode_from_url, normalize_permalink
from .pipeline.understand import run_understanding
from .pipeline.map_places import run_mapping
from .export.csv_writer import write_full_csv, write_mymaps_csv


EXIT_OK = 0
EXIT_ANY_FAILED = 2
EXIT_INVALID_URL = 64


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and process Instagram Reels",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    # Run command (download + process) — default if no subcommand
    p_run = sub.add_parser("run", help="Download and process reels by URL (end-to-end)")
    p_run.add_argument("--urls", nargs="+", required=True, help="One or more Instagram URLs (reels or posts)")
    p_run.add_argument("--out-dir", dest="out_dir", default=None)
    p_run.add_argument("--session-file", dest="session_file", default=None)
    p_run.add_argument("--username", dest="username", default=None)
    p_run.add_argument("--password", dest="password", default=None)
    p_run.add_argument("--interactive-login", action="store_true", dest="interactive_login")
    p_run.add_argument("--user-agent", dest="user_agent", default=None)
    p_run.add_argument("--verbose", action="store_true")

    # Download command
    p_dl = sub.add_parser("download", help="Download reels by URL only")
    p_dl.add_argument("--urls", nargs="+", required=True, help="One or more Instagram URLs (reels or posts)")
    p_dl.add_argument("--out-dir", dest="out_dir", default=None)
    p_dl.add_argument("--session-file", dest="session_file", default=None)
    p_dl.add_argument("--username", dest="username", default=None)
    p_dl.add_argument("--password", dest="password", default=None)
    p_dl.add_argument("--interactive-login", action="store_true", dest="interactive_login")
    p_dl.add_argument("--user-agent", dest="user_agent", default=None)
    p_dl.add_argument("--verbose", action="store_true")

    # Process command
    p_proc = sub.add_parser("process", help="Process a downloaded reel (transcribe → OCR → extract → map → CSV)")
    p_proc.add_argument("shortcode", help="The reel shortcode")
    p_proc.add_argument("--out-dir", dest="out_dir", default=None)
    p_proc.add_argument("--verbose", action="store_true")

    # If no subcommand provided, treat as 'run' (end-to-end)
    if argv and argv[0] not in {"run", "download", "process"}:
        argv = ["run", *argv]
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    console = get_console(verbose=args.verbose)

    if args.command == "run":
        settings = load_settings(
            overrides={
                "out_dir": getattr(args, "out_dir", None),
                "session_file": getattr(args, "session_file", None),
                "username": getattr(args, "username", None),
                "password": getattr(args, "password", None),
                "user_agent": getattr(args, "user_agent", None),
            }
        )

        loader = build_loader(settings, verbose=args.verbose)
        if getattr(args, "username", None) or getattr(args, "password", None) or getattr(args, "session_file", None) or getattr(args, "interactive_login", False):
            try:
                ig_login(loader, settings, interactive=getattr(args, "interactive_login", False))
                if getattr(args, "username", None):
                    info(console, f"Logged in as {args.username} (or session loaded)")
            except Exception as exc:  # noqa: BLE001
                error(console, f"Login/session failed: {exc}")
                return EXIT_ANY_FAILED
        else:
            warn(console, "Proceeding without login; public posts may still fail.")

        overall_ok = True
        invalid_found = False
        for raw_url in getattr(args, "urls", []):
            try:
                norm = normalize_permalink(raw_url)
                code = shortcode_from_url(norm)
                if not code:
                    error(console, f"Invalid URL (no shortcode): {raw_url}")
                    overall_ok = False
                    invalid_found = True
                    continue

                info(console, f"Downloading {code} …")
                result = download_by_url(loader, norm)
                if not result.get("success"):
                    error(console, f"Download failed for {code}")
                    overall_ok = False
                    continue
                written = ", ".join(result.get("files_written", [])) or "(no files detected)"
                success(console, f"Downloaded {code} → {written}")

                # Process
                info(console, f"Understanding {code} …")
                video_path = f"{settings.OUT_DIR}/reels/{code}.mp4"
                caption_text = None
                # Try caption at top-level, then consolidated folder
                try:
                    with open(f"{settings.OUT_DIR}/reels/{code}.txt", "r", encoding="utf-8") as f:
                        caption_text = f.read()
                except FileNotFoundError:
                    try:
                        with open(f"{settings.OUT_DIR}/reels/{code}/{code}.txt", "r", encoding="utf-8") as f:
                            caption_text = f.read()
                    except FileNotFoundError:
                        caption_text = None

                transcript, overlays, extraction = run_understanding(settings, code, video_path, caption_text)

                info(console, f"Resolving places for {code} …")
                matches = run_mapping(settings, code, extraction)

                outdir = f"{settings.OUT_DIR}/reels/{code}"
                write_full_csv(f"{outdir}/results_full.csv", matches)
                write_mymaps_csv(f"{outdir}/results_mymaps.csv", matches)
                success(console, f"Completed end-to-end for {code}")

            except ValueError as ve:
                error(console, f"Invalid URL: {raw_url} ({ve})")
                invalid_found = True
                overall_ok = False
            except Exception as exc:  # noqa: BLE001
                error(console, f"Failed processing {raw_url}: {exc}")
                overall_ok = False

        if invalid_found:
            return EXIT_INVALID_URL
        return EXIT_OK if overall_ok else EXIT_ANY_FAILED

    if args.command in (None, "download"):
        settings = load_settings(
            overrides={
                "out_dir": getattr(args, "out_dir", None),
                "session_file": getattr(args, "session_file", None),
                "username": getattr(args, "username", None),
                "password": getattr(args, "password", None),
                "user_agent": getattr(args, "user_agent", None),
            }
        )
        loader = build_loader(settings, verbose=args.verbose)
        if getattr(args, "username", None) or getattr(args, "password", None) or getattr(args, "session_file", None) or getattr(args, "interactive_login", False):
            try:
                ig_login(loader, settings, interactive=getattr(args, "interactive_login", False))
                if getattr(args, "username", None):
                    info(console, f"Logged in as {args.username} (or session loaded)")
            except Exception as exc:  # noqa: BLE001
                error(console, f"Login/session failed: {exc}")
                return EXIT_ANY_FAILED
        else:
            warn(console, "Proceeding without login; public posts may still fail.")

        overall_ok = True
        invalid_found = False
        for raw_url in getattr(args, "urls", []):
            try:
                norm = normalize_permalink(raw_url)
                code = shortcode_from_url(norm)
                if not code:
                    error(console, f"Invalid URL (no shortcode): {raw_url}")
                    overall_ok = False
                    invalid_found = True
                    continue

                info(console, f"Fetching {code} …")
                result = download_by_url(loader, norm)
                written = ", ".join(result.get("files_written", [])) or "(no files detected)"
                if result.get("success") and result.get("files_written"):
                    success(console, f"Downloaded {code} → {written}")
                else:
                    warn(console, f"Download completed but no files detected for {code}.")
            except ValueError as ve:
                error(console, f"Invalid URL: {raw_url} ({ve})")
                invalid_found = True
                overall_ok = False
            except Exception as exc:  # noqa: BLE001
                error(console, f"Failed to download {raw_url}: {exc}")
                overall_ok = False

        if invalid_found:
            return EXIT_INVALID_URL
        return EXIT_OK if overall_ok else EXIT_ANY_FAILED

    if args.command == "process":
        settings = load_settings(overrides={"out_dir": getattr(args, "out_dir", None)})
        sc = args.shortcode
        video_path = f"{settings.OUT_DIR}/reels/{sc}.mp4"
        caption_text = None
        try:
            with open(f"{settings.OUT_DIR}/reels/{sc}.txt", "r", encoding="utf-8") as f:
                caption_text = f.read()
        except FileNotFoundError:
            try:
                with open(f"{settings.OUT_DIR}/reels/{sc}/{sc}.txt", "r", encoding="utf-8") as f:
                    caption_text = f.read()
            except FileNotFoundError:
                caption_text = None

        info(console, f"Understanding reel {sc} …")
        transcript, overlays, extraction = run_understanding(settings, sc, video_path, caption_text)

        info(console, f"Resolving places for {sc} …")
        matches = run_mapping(settings, sc, extraction)

        outdir = f"{settings.OUT_DIR}/reels/{sc}"
        write_full_csv(f"{outdir}/results_full.csv", matches)
        write_mymaps_csv(f"{outdir}/results_mymaps.csv", matches)
        success(console, f"Wrote CSVs under {outdir}")
        return EXIT_OK

    error(console, "Unknown command")
    return EXIT_ANY_FAILED


if __name__ == "__main__":
	sys.exit(main())


