# -*- coding: utf-8 -*-
"""第二步：按公开曲序把整轨分成十段，逐段量。

曲序时长引自公开发行信息（1973 原版 / 2011 重制的时间码一致，取整到秒）。
这是整套流程里唯一引用外部数字的地方——分段必须有个公认的对齐点，
否则十段边界全是主观的。

量到的东西：
  lufs_i   整段积分响度（EBU R128，ffmpeg ebur128）
  peak_db  采样峰值
  rms_db   均方根
  crest    峰值与 RMS 之差（dB）
  centroid 频谱重心（Hz），音色明暗的粗指标
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

SRC = r"C:\Users\BlueGold\Music\The Dark Side of the Moon.flac"
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

# 公开发行信息的曲序时长（秒）
TRACKS = [
    ("Speak to Me", 67),
    ("Breathe (In the Air)", 169),
    ("On the Run", 215),
    ("Time", 413),
    ("The Great Gig in the Sky", 284),
    ("Money", 383),
    ("Us and Them", 469),
    ("Any Colour You Like", 206),
    ("Brain Damage", 226),
    ("Eclipse", 130),
]

sys.stdout.reconfigure(encoding="utf-8")


def lufs(path, start, dur):
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
        "-i", path, "-af", "ebur128=framelog=quiet", "-f", "null", "NUL",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    m = re.search(r"I:\s*(-?\d+\.\d+)\s*LUFS", r.stderr)
    return float(m.group(1)) if m else None


def main():
    os.makedirs(DATA, exist_ok=True)
    info = sf.info(SRC)
    total = info.frames / info.samplerate

    gaps_path = os.path.join(DATA, "gaps.json")
    head = 5.5
    tail = 0.0
    if os.path.exists(gaps_path):
        gaps = json.load(open(gaps_path, encoding="utf-8"))
        if gaps and gaps[0]["start"] == 0:
            head = gaps[0]["end"]
        if gaps and gaps[-1]["end"] >= total - 0.5:
            tail = gaps[-1]["silence"]

    print(f"总长 {total:.2f}s  头部静默 {head:.2f}s  尾部 {tail:.2f}s  曲目合计 {sum(t[1] for t in TRACKS)}s")

    data, sr = sf.read(SRC, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)

    out = []
    t = head
    for i, (title, dur) in enumerate(TRACKS, 1):
        a, b = int(t * sr), int((t + dur) * sr)
        seg = mono[a:b]
        peak = float(np.abs(seg).max()) or 1e-9
        rms = float(np.sqrt((seg.astype(np.float64) ** 2).mean())) or 1e-9
        # 频谱重心：取中段 30 秒，避免边界
        mid = seg[len(seg) // 2 - 15 * sr: len(seg) // 2 + 15 * sr]
        spec = np.abs(np.fft.rfft(mid * np.hanning(len(mid))))
        freqs = np.fft.rfftfreq(len(mid), 1 / sr)
        centroid = float((spec * freqs).sum() / (spec.sum() or 1e-9))
        row = {
            "n": i,
            "title": title,
            "start": round(t, 2),
            "end": round(t + dur, 2),
            "dur": dur,
            "lufs_i": lufs(SRC, t, dur),
            "peak_db": round(20 * np.log10(peak), 2),
            "rms_db": round(20 * np.log10(rms), 2),
            "crest": round(20 * np.log10(peak / rms), 2),
            "centroid_hz": round(centroid, 1),
        }
        out.append(row)
        print(f"  {i:2d} {title[:26]:28s} {row['start']:7.1f}-{row['end']:7.1f}  "
              f"LUFS {row['lufs_i']}  crest {row['crest']:5.1f}  centroid {row['centroid_hz']:7.0f}Hz")
        t += dur

    covered = t - head
    print(f"\n十段合计 {covered}s ，文件剩余 {total - t:.2f}s")

    with open(os.path.join(DATA, "tracks.json"), "w", encoding="utf-8") as f:
        json.dump({"file": {"path": SRC, "duration": round(total, 2), "sample_rate": info.samplerate,
                            "channels": info.channels},
                   "head_silence": head, "tail_silence": round(total - t, 2),
                   "tracks": out}, f, ensure_ascii=False, indent=1)
    print(f"写入 {os.path.join(DATA, 'tracks.json')}")


if __name__ == "__main__":
    main()
