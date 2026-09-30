"""Download the eight audited NACDA final standings PDFs without changing provenance."""
import argparse

if __package__:
    from .download_sources import ROOT, SourceDownloadError, download_manifest
else:
    from download_sources import ROOT, SourceDownloadError, download_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="redownload even valid cached PDFs")
    arguments = parser.parse_args()
    try:
        downloaded, reused = download_manifest(ROOT / "data/sources.json", force=arguments.force)
    except SourceDownloadError as error:
        raise SystemExit(str(error)) from None
    print(f"Final standings: {downloaded} downloaded, {reused} reused.")


if __name__ == "__main__":
    main()
