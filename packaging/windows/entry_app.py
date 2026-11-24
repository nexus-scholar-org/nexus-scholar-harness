"""The windowed program of the Windows bundle: the installed app (M13 Part A, `console/desktop.py`).

It also runs the approval-code window and the folder dialog when started with
their flags (`--approval-window`, `--choose-folder`): frozen, the app is its own
child process (M13 Part A, B).
"""

from scholar_harness.console.desktop import run

if __name__ == "__main__":
    run()
