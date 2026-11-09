# -*- coding: utf-8 -*-
"""第一步：找出十首歌的交界。

方法：整轨解码成单声道，按 20ms 帧算 RMS，标出能量低于阈值的连续区间，
再把长于 1.2 秒的静默当中缝候选。输出候选时间点，人工核对。

不做任何"理解"，只报数。
"""
import json
import sys

import numpy as np
import soundfile as sf

SRC = r"C:\Users\BlueGold\Music\The Dark Side of the Moon.flac"
SR = 22050
FRAME = 0.02          # 20ms
MIN_SIL = 1.2         # 中缝最短时长（秒）
REL_THR = 0.02        # 相对整轨 95 分位的能量比

sys.stdout.reconfigure(encoding="utf-8")


def main():
    data, sr = sf.read(SRC, dtype="float32", always_2d=True)
    if sr != SR:
        # 简单降采样：取均值到目标采样率（只用于能量包络，够用）
        n = int(round(data.shape[0] * SR / sr))
        idx = np.linspace(0, data.shape[0] - 1, n).astype(np.int64)
        data = data[idx]
        sr = SR
    mono = data.mean(axis=1)

    hop = int(SR * FRAME)
    frames = len(mono) // hop
    rms = np.sqrt((mono[: frames * hop].reshape(frames, hop).astype(np.float64) ** 2).mean(axis=1))

    loud = np.percentile(rms, 95)
    thr = loud * REL_THR
    quiet = rms < thr

    print(f"时长 {len(mono)/sr:.1f}s  帧 {frames}  95分位 RMS {loud:.4f}  阈值 {thr:.4f}")

    gaps = []
    i = 0
    while i < frames:
        if quiet[i]:
            j = i
            while j + 1 < frames and quiet[j + 1]:
                j += 1
            dur = (j - i + 1) * FRAME
            if dur >= MIN_SIL:
                gaps.append((i * FRAME, (j + 1) * FRAME, dur))
            i = j + 1
        else:
            i += 1

    print(f"候选中缝 {len(gaps)} 处")
    for a, b, d in gaps:
        print(f"  {a:8.2f}s → {b:8.2f}s   静默 {d:5.2f}s   （约 {int(a//60)}:{a%60:05.2f}）")

    out = r"C:\Users\BlueGold\Desktop\星子的新家\开源\the-dark-side\data\gaps.json"
    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump([{"start": round(a, 2), "end": round(b, 2), "silence": round(d, 2)} for a, b, d in gaps],
                  f, indent=1)
    print(f"\n写入 {out}")


if __name__ == "__main__":
    main()
