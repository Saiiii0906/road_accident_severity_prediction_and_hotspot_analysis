#!/usr/bin/env python3
"""
Model Acquisition & Integrity Verification Utility for Vantage.

Handles deterministic, production-safe acquisition of Student A's
Random Forest model artifact (student_A/models/accident_severity_model.pkl).

Key Invariants:
1. Skips download if the model file is already present and passes integrity checks.
2. Streams large files (7.80 GB) in fixed-size chunks (default 8MB) to keep memory usage minimal.
3. Downloads to a temporary file (<target>.tmp) and atomically renames upon completion.
4. Validates SHA-256 checksum when configured (VANTAGE_MODEL_SHA256).
5. Never prints or logs credentials, presigned URL tokens, or private parameters.
6. Returns non-zero exit code on any failure; never silently falls back to mock/dummy data.
"""

import argparse
import hashlib
import logging
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | [model_acquisition] %(message)s",
)
logger = logging.getLogger("model_acquisition")

DEFAULT_TARGET_PATH = "student_A/models/accident_severity_model.pkl"
DEFAULT_CHUNK_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB
DEFAULT_TIMEOUT_SECONDS = 3600  # 1 hour for large files


def sanitize_url(url: str) -> str:
    """Mask sensitive query parameters (signatures, tokens) for safe logging."""
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        # Return URL with masked query parameters
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            "REDACTED_PARAMS",
            parsed.fragment,
        ))
    except Exception:
        return "<url-redacted>"


def compute_file_sha256(file_path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE_BYTES) -> str:
    """Compute SHA-256 checksum of a file using streaming reads."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_existing_model(
    target_path: Path,
    expected_sha256: str | None = None,
    min_size_bytes: int = 1024,
) -> bool:
    """Verify whether an existing file meets integrity requirements."""
    if not target_path.is_file():
        return False

    size = target_path.stat().st_size
    if size < min_size_bytes:
        logger.warning(
            "Existing model file at %s is suspiciously small (%d bytes). Considering invalid.",
            target_path,
            size,
        )
        return False

    if expected_sha256:
        logger.info("Verifying SHA-256 checksum of existing model at %s...", target_path)
        actual_hash = compute_file_sha256(target_path)
        if actual_hash.lower() != expected_sha256.lower():
            logger.warning(
                "Existing model checksum mismatch: expected %s, got %s",
                expected_sha256,
                actual_hash,
            )
            return False
        logger.info("Existing model passed SHA-256 verification: %s...", actual_hash[:16])

    logger.info(
        "Valid model file already present at %s (size: %.2f GB). Skipping acquisition.",
        target_path,
        size / (1024**3),
    )
    return True


def acquire_model(
    source_url: str | None,
    target_path: Path,
    expected_sha256: str | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE_BYTES,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> int:
    """Acquire the model artifact from the configured source URL."""
    # Ensure target parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if target already exists and is valid
    if verify_existing_model(target_path, expected_sha256):
        return 0

    if not source_url or not source_url.strip():
        logger.error(
            "CRITICAL: Student A model artifact missing at '%s' and VANTAGE_MODEL_SOURCE_URL is not set.",
            target_path,
        )
        logger.error(
            "To resolve: Mount the model volume to '%s' or configure VANTAGE_MODEL_SOURCE_URL.",
            target_path,
        )
        return 1

    clean_url = source_url.strip()
    safe_log_url = sanitize_url(clean_url)
    temp_path = target_path.with_name(f"{target_path.name}.tmp.{os.getpid()}")

    logger.info("Starting model acquisition: %s -> %s", safe_log_url, target_path)

    hasher = hashlib.sha256() if expected_sha256 else None
    bytes_downloaded = 0
    start_time = time.monotonic()
    last_log_time = start_time

    req = urllib.request.Request(
        clean_url,
        headers={"User-Agent": "Vantage-ModelAcquisition/1.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            content_length = response.headers.get("Content-Length")
            total_bytes = int(content_length) if content_length and content_length.isdigit() else None
            total_gb_str = f"{total_bytes / (1024**3):.2f} GB" if total_bytes else "unknown size"

            logger.info("Connected to remote source. Expected transfer size: %s", total_gb_str)

            with open(temp_path, "wb") as out_f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if hasher:
                        hasher.update(chunk)

                    now = time.monotonic()
                    if now - last_log_time >= 15.0:  # log progress every 15s
                        speed_mb = (bytes_downloaded / (1024 * 1024)) / (now - start_time)
                        pct_str = (
                            f" ({100.0 * bytes_downloaded / total_bytes:.1f}%)"
                            if total_bytes
                            else ""
                        )
                        logger.info(
                            "Downloaded %.2f MB%s at %.1f MB/s",
                            bytes_downloaded / (1024 * 1024),
                            pct_str,
                            speed_mb,
                        )
                        last_log_time = now

        duration = time.monotonic() - start_time
        logger.info(
            "Download completed in %.1f seconds (%.2f MB total, %.2f MB/s avg).",
            duration,
            bytes_downloaded / (1024 * 1024),
            (bytes_downloaded / (1024 * 1024)) / max(duration, 0.1),
        )

        # Integrity check
        if expected_sha256:
            actual_sha256 = hasher.hexdigest()
            if actual_sha256.lower() != expected_sha256.lower():
                logger.error(
                    "CRITICAL: Checksum verification failed! Expected %s, calculated %s",
                    expected_sha256,
                    actual_sha256,
                )
                if temp_path.exists():
                    temp_path.unlink()
                return 1
            logger.info("SHA-256 verification passed: %s", actual_sha256)

        # Atomic replacement
        os.replace(temp_path, target_path)
        logger.info("Successfully acquired and verified model at: %s", target_path)
        return 0

    except urllib.error.HTTPError as e:
        logger.error("HTTP error downloading model: HTTP %d %s", e.code, e.reason)
        if temp_path.exists():
            temp_path.unlink()
        return 1
    except urllib.error.URLError as e:
        logger.error("Network error connecting to model source: %s", e.reason)
        if temp_path.exists():
            temp_path.unlink()
        return 1
    except Exception as exc:
        logger.error("Unexpected error during model acquisition: %s", exc)
        if temp_path.exists():
            temp_path.unlink()
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vantage Production Model Acquisition & Integrity Utility"
    )
    parser.add_argument(
        "--target-path",
        default=os.getenv("VANTAGE_MODEL_TARGET_PATH", DEFAULT_TARGET_PATH),
        help="Path where the model artifact should reside.",
    )
    parser.add_argument(
        "--source-url",
        default=os.getenv("VANTAGE_MODEL_SOURCE_URL"),
        help="Remote URL (S3/GCS/HTTP) to acquire the model from if not present.",
    )
    parser.add_argument(
        "--sha256",
        default=os.getenv("VANTAGE_MODEL_SHA256"),
        help="Expected SHA-256 checksum for integrity validation.",
    )
    parser.add_argument(
        "--chunk-size-mb",
        type=int,
        default=int(os.getenv("VANTAGE_MODEL_CHUNK_SIZE_MB", "8")),
        help="Streaming chunk size in megabytes (default 8MB).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=int(os.getenv("VANTAGE_MODEL_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))),
        help="Network timeout in seconds.",
    )

    args = parser.parse_args()

    target_path = Path(args.target_path)
    chunk_size = max(args.chunk_size_mb, 1) * 1024 * 1024

    exit_code = acquire_model(
        source_url=args.source_url,
        target_path=target_path,
        expected_sha256=args.sha256,
        chunk_size=chunk_size,
        timeout_seconds=args.timeout_seconds,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
