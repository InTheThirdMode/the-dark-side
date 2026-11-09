# The Dark Side of the Moon — dissection

Input: `The Dark Side of the Moon.flac` · 44.1 kHz · 16-bit · 2 ch · 2576.00 s

Everything below is measured from that file. Segmentation is the one place where an outside number is used (published track lengths); it is stated in §1.

---

## 1. Segmentation

Method: 20 ms-frame RMS envelope, silence = RMS below 2% of the 95th percentile, minimum 1.2 s.

The whole album contains **one** silence long enough to split: `19:09.20 → 19:23.00` (13.80 s). Start and end padding add two more (5.50 s / 8.16 s). The ten tracks are otherwise continuous.

Boundaries therefore come from published track lengths, offset by the 5.50 s head. Sum of published lengths = 2562 s; file = 2576.00 s; head 5.50 + tracks 2562.00 + tail 8.50 = 2576.00. (That 8.50 s tail is what remains after the tenth track; 8.16 s of it falls below the silence threshold — the other 0.34 s is fade-out above it.)

| # | Track | Start | End | Dur |
|---|---|---|---|---|
| 1 | Speak to Me | 5.50 | 72.50 | 67 |
| 2 | Breathe (In the Air) | 72.50 | 241.50 | 169 |
| 3 | On the Run | 241.50 | 456.50 | 215 |
| 4 | Time | 456.50 | 869.50 | 413 |
| 5 | The Great Gig in the Sky | 869.50 | 1153.50 | 284 |
| 6 | Money | 1153.50 | 1536.50 | 383 |
| 7 | Us and Them | 1536.50 | 2005.50 | 469 |
| 8 | Any Colour You Like | 2005.50 | 2211.50 | 206 |
| 9 | Brain Damage | 2211.50 | 2437.50 | 226 |
| 10 | Eclipse | 2437.50 | 2567.50 | 130 |

Check: the single real silence (19:09.20–19:23.00) straddles the 5/6 boundary at 1153.50 s.

---

## 2. Loudness

Integrated loudness by ffmpeg `ebur128` per segment; peak/RMS/crest from the decoded PCM; spectral centroid from a 30 s window at each segment's midpoint.

| # | Track | LUFS-I | Peak dBFS | RMS dBFS | Crest dB | Centroid Hz |
|---|---|---|---|---|---|---|
| 1 | Speak to Me | -21.9 | -5.27 | -22.80 | 17.52 | 1588.4 |
| 2 | Breathe | -14.5 | -3.64 | -18.70 | 15.07 | 2174.6 |
| 3 | On the Run | -16.9 | -4.10 | -20.72 | 16.62 | 2603.2 |
| 4 | Time | -13.4 | -2.21 | -18.14 | 15.93 | 2633.1 |
| 5 | The Great Gig in the Sky | -15.1 | -4.62 | -21.42 | 16.79 | 2541.8 |
| 6 | Money | -13.0 | -2.77 | -18.44 | 15.67 | 2700.5 |
| 7 | Us and Them | -16.6 | -4.12 | -21.34 | 17.22 | 2377.3 |
| 8 | Any Colour You Like | -13.6 | -2.74 | -17.53 | 14.80 | 1770.9 |
| 9 | Brain Damage | -16.3 | -3.10 | -20.56 | 17.45 | 2801.6 |
| 10 | Eclipse | -12.5 | -2.69 | -17.63 | 14.93 | 2735.3 |

Whole-track mean RMS: −21.3 dBFS. Crest range across segments: 14.8 → 17.5 dB (spread 2.7 dB).

Chart: `img/album.png`

---

## 3. Tempo and key

90 s window per segment, `librosa` onset envelope → tempo; chroma_cqt → Krumhansl-Schmuckler correlation over 24 keys.

| # | Track | tempo (BPM) | key | corr |
|---|---|---|---|---|
| 1 | Speak to Me | 112.3 | C# minor | 0.31 |
| 2 | Breathe | 129.2 | A major | 0.80 |
| 3 | On the Run | 83.4 | D major | 0.42 |
| 4 | Time | 136.0 | C# minor | 0.76 |
| 5 | The Great Gig in the Sky | 129.2 | G major | 0.67 |
| 6 | Money | 136.0 | B minor | 0.49 |
| 7 | Us and Them | 143.6 | D major | 0.80 |
| 8 | Any Colour You Like | 152.0 | D major | 0.60 |
| 9 | Brain Damage | 136.0 | D major | 0.88 |
| 10 | Eclipse | 136.0 | D minor | 0.76 |

Tempo is the unstable half: the same segment gives 123.0 or 136.0 depending on window length. Treat as ±10% and do not read half/double from it.

---

## 4. Meter (Money)

60 s window at `1194–1254 s` (drums settled, no transition). Onset-envelope autocorrelation at beat multiples:

| lag (beats) | 1 | 2 | 3 | 4 | 7 | 8 | 14 | 16 |
|---|---|---|---|---|---|---|---|---|
| ACF | +0.577 | +0.418 | +0.291 | +0.212 | **+0.197** | +0.149 | +0.094 | +0.020 |

7-beat periodicity exceeds 8-beat by a factor of 1.32 → `7/8`.

Same test on Time (`496–536 s`): 7-beat −0.104, 8-beat −0.110, 16-beat +0.173 → no bar-level periodicity at 7 or 8; the only repeat is four bars. Reported as inconclusive, not as 7/8.

---

## Run it

```bash
pip install soundfile librosa matplotlib numpy
python 01_gaps.py      # → data/gaps.json
python 02_analyze.py   # → data/tracks.json
python 03_plot.py      # → img/album.png
python 04_tempo.py     # → data/music.json
python 05_meter.py     # → data/meter.json
python verify.py       # 把 README 里的表格和 data/*.json 逐格对一遍
```

`verify.py` exists because the tables in this file were typed by hand, and hand-typed tables are wrong until proven otherwise. It exits non-zero on any mismatch.

Edit the `SRC` constant in each script to point at your own copy. No audio is redistributed here.

## Caveats

Tempo: see §3. Key: Krumhansl correlation below 0.5 is weak — the C# minor reading on *Speak to Me* (0.31) is close to meaningless.

Loudness numbers are EBU R128 integrated; different masters (1973 UK, 1992 remaster, 2003 SACD, 2011 remaster) will differ and are not interchangeable.
