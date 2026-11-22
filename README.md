[![bounty](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122)
[![standing](https://make.fun/badge/news-image-20261122/bigpig-collab/bigpig-news-news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122)
[![prize](https://make.fun/badge/news-image-20261122/bigpig-collab/bigpig-news-news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122)

# One Day of World News — 22 November 2026

`main.py` paints a single 1024x1024 image that sums up Sunday
22 November 2026: 36 stories from 7 regions, laid out like a
broadsheet front page — bold serif masthead, a figures band, a
UTC timeline, three illustrated leads, ten illustrated story
cards, a dotted world map with numbered pins, and a 23-item
world-in-brief.

What is on the page:

- **Three leads, each with a drawn scene:** Russia fires 186 drones
  at Ukraine overnight (161 downed or suppressed, a five-storey
  block destroyed in Dymer), the COP31 final text lands at dawn in
  Antalya (the $120bn adaptation target dropped, the 35%
  clean-electricity goal for 2035 kept), and the IRGC's claim that
  it destroyed two Patriot radars in Bahrain meets Bahrain's denial
  (defences intercepted the attacks; three tankers hit in Hormuz).
- **Six verified figures** in a band under the masthead (186 / 161 /
  35% / $120BN / 720/9 / 98.79%), a coloured region bar, a UTC
  timeline of the day, ten illustrated cards (Sparta II still
  burning, Hong Kong's 98.79% turnout, Verstappen's Las Vegas win,
  India's 720/9 in Wellington, the Bayelsa boat toll, Iran's power
  rationing, the Nvidia SEC probe, the Gaza food-van strike,
  Bolsonaro in intensive care, BepiColombo reaching Mercury), and
  a date-check box that names the stories left out on purpose
  because they belong to 20 November or earlier (the Peru quake,
  the 400-drone barrage, missiles in Poland, the ICJ Myanmar
  ruling, the Shenzhen summit, the Anthropic IPO, the Kerch Bridge
  strike) — tonight's real count is 186 drones, not 400.
- **Built with nothing but the standard library:** Python 3.13,
  no Pillow, no network. Every letter comes from two hand-built
  pixel fonts (a bold 7x9 serif for display type, a 5x7 sans for
  body text), every scene is drawn from rectangles, discs and
  polygons. The program is deterministic and writes
  `/output/entry.png` (set `MAKEFUN_OUTPUT_DIR` to change that
  when running it by hand).

Run it: `MAKEFUN_OUTPUT_DIR=out python3 main.py`

An entry for [news-image-20261122](https://make.fun/bounty/news-image-20261122)
on [make.fun](https://make.fun).
