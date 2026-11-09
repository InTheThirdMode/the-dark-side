# -*- coding: utf-8 -*-
"""自检：README 里手抄的表格，跟 data/*.json 里算出来的数字，逐格对。

手抄一定会错。这个脚本存在的意义就是让错自己浮出来。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
README = open(os.path.join(BASE, "README.md"), encoding="utf-8").read()
DATA = os.path.join(BASE, "data")

sys.stdout.reconfigure(encoding="utf-8")

problems = []


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def rows_of(section_header):
    """取某个 ## 小节里的表格行（| 开头），返回去掉表头和分隔线的数据行。"""
    idx = README.find(section_header)
    if idx < 0:
        return []
    tail = README[idx:]
    nxt = tail.find("\n## ", 1)
    body = tail[: nxt if nxt > 0 else len(tail)]
    lines = [l.strip() for l in body.splitlines() if l.strip().startswith("|")]
    return [l for l in lines if not re.match(r"^\|[\s\-:|]+\|$", l)][1:]  # 去掉表头行


def cells(line):
    return [c.strip() for c in line.strip("|").split("|")]


def cmp_num(label, got, want, tol=0.06):
    if want is None:
        return
    try:
        g = float(str(got).replace("−", "-").replace("+", ""))
    except ValueError:
        problems.append(f"{label}: 读不出数字 {got!r}")
        return
    if abs(g - float(want)) > tol:
        problems.append(f"{label}: README {g} ≠ data {want}")


# --- 1. 分段表 ---
tracks = load("tracks.json")["tracks"]
seg_rows = rows_of("## 1. Segmentation")
if len(seg_rows) != len(tracks):
    problems.append(f"分段表行数 {len(seg_rows)} ≠ 曲目数 {len(tracks)}")
for row, tr in zip(seg_rows, tracks):
    c = cells(row)
    if c[1] != tr["title"] and not tr["title"].startswith(c[1]):
        problems.append(f"分段表 第{tr['n']}行 标题 {c[1]!r} ≠ {tr['title']!r}")
    cmp_num(f"分段 {tr['n']} start", c[2], tr["start"])
    cmp_num(f"分段 {tr['n']} end", c[3], tr["end"])
    cmp_num(f"分段 {tr['n']} dur", c[4], tr["dur"], tol=0.6)

# --- 2. 响度表 ---
loud_rows = rows_of("## 2. Loudness")
if len(loud_rows) != len(tracks):
    problems.append(f"响度表行数 {len(loud_rows)} ≠ 曲目数 {len(tracks)}")
for row, tr in zip(loud_rows, tracks):
    c = cells(row)
    cmp_num(f"响度 {tr['n']} LUFS", c[2], tr["lufs_i"], tol=0.15)
    cmp_num(f"响度 {tr['n']} peak", c[3], tr["peak_db"], tol=0.15)
    cmp_num(f"响度 {tr['n']} rms", c[4], tr["rms_db"], tol=0.15)
    cmp_num(f"响度 {tr['n']} crest", c[5], tr["crest"], tol=0.15)
    cmp_num(f"响度 {tr['n']} centroid", c[6], tr["centroid_hz"], tol=1.5)

# --- 3. 拍与调表 ---
music = {m["n"]: m for m in load("music.json")}
tempo_rows = rows_of("## 3. Tempo and key")
for row in tempo_rows:
    c = cells(row)
    try:
        n = int(c[0])
    except ValueError:
        continue
    m = music.get(n)
    if not m:
        continue
    cmp_num(f"tempo {n}", c[2], m["bpm_raw"], tol=0.15)
    if c[3] != m["key"]:
        problems.append(f"key {n}: README {c[3]!r} ≠ data {m['key']!r}")
    cmp_num(f"keycorr {n}", c[4], m["key_corr"], tol=0.006)

# --- 4. 小节长度表 ---
meter = load("meter.json")
mrow = rows_of("## 4. Meter (Money)")
if mrow:
    c = cells(mrow[0])
    vals = [x for x in c if x]
    # 行结构：| lag (beats) | 1 | 2 | 3 | 4 | 7 | 8 | 14 | 16 |
    lags = ["1", "2", "3", "4", "7", "8", "14", "16"]
    acf = meter["Money"]["acf_by_beats"]
    for lag, cell in zip(lags, c[1:]):
        want = acf.get(f"{lag} 拍")
        cmp_num(f"Money acf {lag}", cell.replace("*", ""), want, tol=0.002)

# --- 5. 总时长对账 ---
total = load("tracks.json")["file"]["duration"]
s = sum(t["dur"] for t in tracks) + 5.5 + 8.5
if abs(s - total) > 0.6:
    problems.append(f"总时长对不上：曲目和 {s} vs 文件 {total}")

# --- 6. 静默那几句断言 ---
gaps = load("gaps.json")
head_detected = gaps[0]["end"] if gaps and gaps[0]["start"] == 0 else None
tail_detected = gaps[-1]["silence"] if gaps and gaps[-1]["end"] >= total - 0.5 else None

m = re.search(r"Start and end padding add two more \(([\d.]+) s / ([\d.]+) s\)", README)
if m and head_detected is not None:
    cmp_num("head silence", m.group(1), head_detected, tol=0.02)
    if tail_detected is not None:
        cmp_num("tail silence", m.group(2), tail_detected, tol=0.02)
else:
    problems.append("README 里找不到首尾静默的那句（Start and end padding…）")

m = re.search(r"`(\d+):(\d+\.\d+) → (\d+):(\d+\.\d+)` \(([\d.]+) s\)", README)
if m and len(gaps) >= 3:
    mid = gaps[1:3]
    start_s = mid[0]["start"]
    end_s = mid[-1]["end"]
    dur_s = end_s - start_s
    cmp_num("中缝 start", int(m.group(1)) * 60 + float(m.group(2)), start_s, tol=0.02)
    cmp_num("中缝 end", int(m.group(3)) * 60 + float(m.group(4)), end_s, tol=0.02)
    cmp_num("中缝 时长", m.group(5), dur_s, tol=0.02)
else:
    problems.append("README 里找不到中缝那句，或 gaps.json 少于三段")

# --- 7. 判定文字与 meter.json 一致 ---
mv = meter.get("Money", {}).get("verdict", "")
if "7-beat" in mv and "`7/8`" not in README:
    problems.append("meter.json 判 7/8，README 没写")
tv = meter.get("Time", {}).get("verdict", "")
if "inconclusive" in tv and "inconclusive" not in README:
    problems.append("meter.json 判 inconclusive，README 没写")

print(f"检查完毕，问题 {len(problems)} 条")
for p in problems:
    print("  ✗", p)
sys.exit(1 if problems else 0)
