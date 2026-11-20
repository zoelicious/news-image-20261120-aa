# news-image-20261120-aa

[![make.fun](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/zoelicious/news-image-20261120-aa/rank.svg)](https://make.fun/bounty/news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/zoelicious/news-image-20261120-aa/reward.svg)](https://make.fun/bounty/news-image-20261120)

**THE WORLD AT A GLANCE — Friday 20 November 2026 in one image.**

Entry for the [make.fun bounty "Sum up 20 November's world news in one image"](https://make.fun/bounty/news-image-20261120).

One deep-navy editorial page, not a newspaper grid: a single hero globe with
the day's three biggest stories orbiting it — Cyclone Akvan coming ashore in
India, missiles raining on Kyiv overnight, COP31 ending its last day without a
deal — plus six illustrated briefs, an 18-story ALSO ON list and a DATE CHECK
box that names the big stories left out because they were first reported on
19 November (the Shenzhen summit, Anthropic's IPO debut, the ICJ Rohingya
verdict, the Kyiv embassy strikes, and more).

27 stories, 6 continents. Every story happened, or was first reported, on
Friday 20 November 2026, with its source named on the page.

## How it is built

- `render.py` — draws `entry.png` (1024x1024) at build time with Pillow and
  the system DejaVu TrueType fonts (real TTF glyphs — no hand-made font or
  PNG encoder), plus its own vector globe and icons. Build-time only;
  fully deterministic, no network.
- `main.py` — the entry program (Python standard library only): copies the
  shipped `entry.png` to `$MAKEFUN_OUTPUT_DIR/entry.png`.

Run it:

```sh
python3 render.py            # writes entry.png (needs Pillow + DejaVu fonts)
MAKEFUN_OUTPUT_DIR=out python3 main.py
```
