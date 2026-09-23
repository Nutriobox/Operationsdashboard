"""
One-job-at-a-time lock for the shared browser profile (added 2026-09-23).

Problem: when the laptop wakes up, Windows starts every job it missed at the
same moment (e.g. 21 Sep 14:34 — Weekly Sales + Weekly KOT in the same second).
They all open secrets/browser-profile together; Chrome allows ONE process per
profile, so the losers crash or read a half-loaded page and report "LOGGED OUT".

Fix: every Playwright launch on that profile first takes a cross-process file
lock and waits its turn (up to WAIT_MIN minutes). Installed automatically from
config.py, so no job script had to change.
"""
from __future__ import annotations

import atexit
import os
import sys
import time
from pathlib import Path

WAIT_MIN = 45
_state = {"fh": None, "depth": 0}


def _lock_file(profile_dir: Path) -> Path:
    return profile_dir.parent / (profile_dir.name + ".joblock")


def _try_lock(fh) -> bool:
    try:
        if sys.platform == "win32":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock(fh) -> None:
    try:
        if sys.platform == "win32":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def acquire(profile_dir: Path) -> None:
    if _state["depth"] > 0:              # already held by this process
        _state["depth"] += 1
        return
    path = _lock_file(profile_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a+")
    if fh.tell() == 0:
        fh.write(" ")
        fh.flush()
    deadline = time.time() + WAIT_MIN * 60
    announced = False
    while not _try_lock(fh):
        if not announced:
            print(f"[profile-lock] another job is using the browser profile — "
                  f"waiting (up to {WAIT_MIN} min)...", flush=True)
            announced = True
        if time.time() > deadline:
            fh.close()
            raise RuntimeError(
                f"browser profile busy for {WAIT_MIN} min — another job seems stuck. "
                "Check Task Manager for a leftover python/chrome process.")
        time.sleep(5)
    if announced:
        print("[profile-lock] got it, continuing.", flush=True)
    _state["fh"] = fh
    _state["depth"] = 1


def release() -> None:
    if _state["depth"] == 0:
        return
    _state["depth"] -= 1
    if _state["depth"] == 0 and _state["fh"] is not None:
        _unlock(_state["fh"])
        _state["fh"].close()
        _state["fh"] = None


atexit.register(lambda: (_state.update(depth=1), release()) if _state["fh"] else None)


def install(profile_dir: Path) -> None:
    """Wrap Playwright's launch_persistent_context for `profile_dir`."""
    try:
        from playwright.sync_api._generated import BrowserType
    except Exception:
        return
    if getattr(BrowserType.launch_persistent_context, "_nutrio_locked", False):
        return
    orig = BrowserType.launch_persistent_context
    target = os.path.normcase(os.path.abspath(str(profile_dir)))

    def wrapped(self, user_data_dir, *a, **kw):
        mine = os.path.normcase(os.path.abspath(str(user_data_dir))) == target
        if not mine:
            return orig(self, user_data_dir, *a, **kw)
        acquire(profile_dir)
        try:
            ctx = orig(self, user_data_dir, *a, **kw)
        except Exception:
            release()
            raise
        orig_close = ctx.close
        done = {"v": False}

        def close(*ca, **ckw):
            try:
                return orig_close(*ca, **ckw)
            finally:
                if not done["v"]:
                    done["v"] = True
                    release()
        ctx.close = close
        return ctx

    wrapped._nutrio_locked = True
    BrowserType.launch_persistent_context = wrapped
