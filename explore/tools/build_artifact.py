#!/usr/bin/env python3
"""Build Runmon Explore into a hosted Artifact page.

The host wraps a page in its own <!doctype>/<html>/<head>/<body>, so the build
strips ours and keeps everything inside: the title, the font link, the style,
the markup and the script. The game itself is unchanged - the same file plays
the same game from the repo or from the link.

    python3 explore/tools/build_artifact.py OUT_DIR

Writes OUT_DIR/index.html and copies art/ beside it, then prints the list of
files the page loads, to publish with it.
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))


def main(out):
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    for pat in (r"<!doctype html>\s*", r"<html[^>]*>\s*", r"</html>\s*", r"<head>\s*", r"</head>\s*",
                r"<body>\s*", r"</body>\s*", r'<meta charset="utf-8">\s*', r'<meta name="viewport"[^>]*>\s*',
                r'<meta name="theme-color"[^>]*>\s*', r'<meta name="robots"[^>]*>\s*'):
        src = re.sub(pat, "", src, flags=re.I)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(src.strip() + "\n")
    files = []
    for sub in ("art", os.path.join("art", "game")):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
        for name in sorted(os.listdir(os.path.join(ROOT, sub))):
            if name.endswith(".png"):
                shutil.copy2(os.path.join(ROOT, sub, name), os.path.join(out, sub, name))
                files.append(os.path.join(sub, name).replace(os.sep, "/"))
    print("\n".join(files))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist"))
