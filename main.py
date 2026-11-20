#!/usr/bin/env python3
"""Entry program for make.fun news-image-20261120 (Aa / zoelicious4843).

Copies the entry image shipped in this repository to $MAKEFUN_OUTPUT_DIR.
The image was drawn at build time by render.py in this same repository
(Pillow + system DejaVu TrueType fonts — real TTF glyphs, no hand-made
font or PNG encoder): a deep-navy editorial page, "THE WORLD AT A
GLANCE", summing up Friday 20 November 2026 in one image - a hero globe,
three orbiting stories, six illustrated briefs, an ALSO ON list and a
DATE CHECK footer. Standard library only; deterministic; no network.
"""
import os
import shutil
import sys


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        print("MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 1
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    os.makedirs(outdir, exist_ok=True)
    shutil.copyfile(src, os.path.join(outdir, "entry.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
