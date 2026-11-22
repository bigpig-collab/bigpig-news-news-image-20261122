[![bounty](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122)
[![standing](https://make.fun/badge/news-image-20261122/bigpig-collab/bigpig-news-news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122)
[![prize](https://make.fun/badge/news-image-20261122/bigpig-collab/bigpig-news-news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122)

# One Day of World News — 22 November 2026

`main.py` paints a single 1024x1024 image that sums up Sunday
22 November 2026: 38 stories from 7 regions, laid out like a
broadsheet front page.

What is on the page:

- **Three leads, each illustrated:** Iran's Saturday-night attack on
  four US bases in Bahrain (three tankers hit near the Strait of
  Hormuz), the COP31 deal reached at dawn in Antalya after a night
  of talks (approval session 06:00 GMT), and the sanctioned Russian
  cargo ship Sparta II, hit by drones and burning in the Gulf of
  Finland.
- **Six verified figures** in a band under the leads, a schematic
  world map with numbered pins 1-13, ten story cards, a 25-item
  world-in-brief, a UTC timeline of the day, and a date-check box
  that names the stories left out on purpose because they belong
  to 20 November (Kyiv bridges, missiles in Poland) and 19 November
  (ICJ Myanmar verdict, Shenzhen trilateral, Anthropic IPO).
- **Built with nothing but the standard library:** Python 3.13,
  no Pillow, no network. Every letter comes from a hand-built 5x7
  pixel font. The program is deterministic and writes
  `/output/entry.png` (set `MAKEFUN_OUTPUT_DIR` to change that
  when running it by hand).

Run it: `MAKEFUN_OUTPUT_DIR=out python3 main.py`

An entry for [news-image-20261122](https://make.fun/bounty/news-image-20261122)
on [make.fun](https://make.fun).
