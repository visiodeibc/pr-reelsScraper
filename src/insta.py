from __future__ import annotations

import glob
import os
import shutil
from typing import Dict

import instaloader

from .config import Settings
from .urltools import normalize_permalink, shortcode_from_url


def build_loader(settings: Settings, verbose: bool = False) -> instaloader.Instaloader:
    """Create and configure an Instaloader instance.

    Notes (from Instaloader docs):
    - Post.from_shortcode(context, shortcode)
    - download_post(post, target)
    - Session management via load_session_from_file, login, save_session_to_file
    """
    loader = instaloader.Instaloader(
        dirname_pattern=f"{settings.OUT_DIR}/{{target}}",
        filename_pattern="{shortcode}",
        download_pictures=False,
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=True,
        post_metadata_txt_pattern="{caption}",
        compress_json=False,
        quiet=not verbose,
    )
    # Configure connection settings and UA via context for broader compatibility across versions
    loader.context.request_timeout = settings.REQUEST_TIMEOUT
    loader.context.max_connection_attempts = settings.MAX_CONNECTION_ATTEMPTS
    if settings.USER_AGENT:
        loader.context.user_agent = settings.USER_AGENT
    return loader


def login(loader: instaloader.Instaloader, settings: Settings, interactive: bool) -> None:
    """Login using session file, username/password, or interactive login.

    If no credentials are provided, continues anonymously (may fail on private or
    login-required content).
    """
    username = settings.IG_USERNAME
    password = settings.IG_PASSWORD
    session_file = settings.SESSION_FILE

    if session_file and username:
        loader.load_session_from_file(username, session_file)
        return

    if username and password:
        loader.login(username, password)
        loader.save_session_to_file(session_file or None)
        return

    if interactive and username:
        loader.interactive_login(username)
        loader.save_session_to_file(session_file or None)
        return

    # Anonymous mode – proceed without login
    return


def download_by_url(loader: instaloader.Instaloader, url: str) -> Dict[str, object]:
    """Download a Reel/Post by URL and return metadata describing the result.

    Raises ValueError if URL is invalid / shortcode cannot be extracted.
    """
    permalink = normalize_permalink(url)
    shortcode = shortcode_from_url(permalink)
    if not shortcode:
        raise ValueError("Invalid Instagram URL: could not extract shortcode")

    post = instaloader.Post.from_shortcode(loader.context, shortcode)
    owner_username = post.owner_username
    target = "reels"

    ok = loader.download_post(post, target=target)

    # Derive source directory from loader pattern and then consolidate files into per-shortcode folder
    source_dir = loader.dirname_pattern.replace("{target}", target)
    os.makedirs(source_dir, exist_ok=True)
    downloaded_files = sorted(glob.glob(os.path.join(source_dir, f"{shortcode}.*")))

    # Move into out/reels/{shortcode}/
    destination_dir = os.path.join(source_dir, shortcode)
    os.makedirs(destination_dir, exist_ok=True)
    moved_files = []
    for path in downloaded_files:
        dest = os.path.join(destination_dir, os.path.basename(path))
        try:
            if os.path.abspath(path) != os.path.abspath(dest):
                shutil.move(path, dest)
            else:
                # already in place
                pass
        finally:
            if os.path.exists(dest):
                moved_files.append(dest)

    return {
        "shortcode": shortcode,
        "owner_username": owner_username,
        "is_video": bool(getattr(post, "is_video", False)),
        "target_dir": destination_dir,
        "files_written": moved_files,
        "success": bool(ok),
    }


