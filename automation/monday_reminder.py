"""
Monthly dashboard publish/reminder -> port of the Claude
"nutriobox-dashboard-monday-reminder" task.

The original picks the newest NutrioBox_Dashboard_*.html from the Application folder
and OPENS the GitHub upload page for a MANUAL drag-drop (GitHub blocks programmatic
uploads to that repo). The unattended port instead git-commits + pushes the newest
HTML into the PowerBI portfolio repo IF it is cloned locally; otherwise it prints the
file + the manual-upload URL (no automation can bypass GitHub's upload security for a
browser drag-drop, but a local git push is fully scriptable).

    python monday_reminder.py               # push if repo cloned, else print manual steps
    python monday_reminder.py --dry-run     # just locate + report

VALIDATE:
  * PORTFOLIO_REPO: set to the local clone of github.com/Nutriobox/PowerBI-Dashboard-Portfolio
    if one exists on this laptop. If it isn't cloned, leave as-is and the script prints
    the manual GitHub-upload instructions (the original behaviour).
  * APP_DIR: the Application folder holding NutrioBox_Dashboard_*.html.
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys

# New laptop (user hp). Original SKILL referenced C:\Users\mayank\... (old laptop).
APP_DIR = r"C:\Users\hp\Downloads\Application"
PORTFOLIO_REPO = None   # e.g. r"C:\Users\hp\Documents\GitHub\PowerBI-Dashboard-Portfolio"
UPLOAD_URL = "https://github.com/Nutriobox/PowerBI-Dashboard-Portfolio/upload/main"


def newest_html(folder: str):
    cands = sorted(glob.glob(os.path.join(folder, "NutrioBox_Dashboard_*.html")),
                   key=os.path.getmtime)
    return cands[-1] if cands else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = newest_html(APP_DIR)
    if not src:
        print(f"ABORT: no NutrioBox_Dashboard_*.html in {APP_DIR} — nothing to publish.")
        return 1
    size_kb = os.path.getsize(src) / 1024
    print(f"latest dashboard: {src}  ({size_kb:,.0f} KB)")

    if args.dry_run:
        print("(dry) located only.")
        return 0

    if not PORTFOLIO_REPO or not os.path.isdir(os.path.join(PORTFOLIO_REPO, ".git")):
        print("\nPortfolio repo not cloned locally (PORTFOLIO_REPO unset). Manual step:")
        print(f"  1. Open {UPLOAD_URL}")
        print(f"  2. Drag in {os.path.basename(src)}")
        print("  3. Add a commit message and click 'Commit changes'.")
        print("(GitHub blocks programmatic browser upload; a local clone would let this push automatically.)")
        return 0

    # Local git push (author must be the Vercel-verified email, like the other deploys).
    dst = os.path.join(PORTFOLIO_REPO, os.path.basename(src))
    import shutil
    shutil.copyfile(src, dst)
    def git(*a):
        subprocess.run(["git", *a], cwd=PORTFOLIO_REPO, check=True)
    lock = os.path.join(PORTFOLIO_REPO, ".git", "index.lock")
    if os.path.exists(lock):
        os.remove(lock)
    git("config", "user.email", "mayank@nutriobox.com")
    git("config", "user.name", "Mayank")
    git("add", os.path.basename(src))
    git("commit", "-m", f"Dashboard: {os.path.basename(src)}")
    git("push", "origin", "main")
    print(f"OK — pushed {os.path.basename(src)} to the portfolio repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
