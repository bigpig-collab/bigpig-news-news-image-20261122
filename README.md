[![news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/bigpig-collab/bigpig-news-news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/bigpig-collab/bigpig-news-news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122)

# The World in One Day — Sunday 22 November 2026

A program that draws one image summing up 22 November 2026's world news:
38 stories across 7 regions on a single broadsheet front page.

- **Lead stories:** Iran's Saturday-night strikes on four US bases in
  Bahrain (with three tankers hit in the Strait of Hormuz), the COP31
  deal at dawn in Antalya after all-night talks (approval session
  06:00 GMT), and the Russian cargo ship Sparta II hit by drones in
  the Baltic, on fire and drifting into Finnish waters.
- **Also:** a figures band of six verified numbers, a schematic world map
  with pins 1-13, ten story cards, a 25-item world in brief, a UTC
  day-in-order strip, and a date-check box naming 20 November stories
  deliberately excluded (Kyiv bridges hit, missiles landing in Poland)
  and 19 November stories (ICJ Myanmar verdict, Shenzhen trilateral,
  Anthropic IPO pricing).
- **How it is built:** pure Python 3.13 standard library only — no Pillow,
  no network. A hand-built 5x7 pixel font draws every letter; the program
  writes a deterministic 1024x1024 PNG to `/output/entry.png`
  (`MAKEFUN_OUTPUT_DIR` overrides the output directory for local runs).

Run it: `MAKEFUN_OUTPUT_DIR=out python3 main.py`

Entry for [news-image-20261122](https://make.fun/bounty/news-image-20261122)
on [make.fun](https://make.fun).
