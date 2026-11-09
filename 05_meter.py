# -*- coding: utf-8 -*-
"""第五步：小节长度。

Money 是非偶数拍。它到底是 7 个八分音符一小节，还是 8 个，可以算：
取它最稳的一段（鼓机进满、没有转场），做 onset envelope 的自相关，
比较 7 拍、8 拍两个周期上的强度。差得多就是 7/8。

同时对 Time 做一次半速/倍速检验，因为它的节拍跟踪给了 136，
而这首歌的实际脉冲可能只有一半。
"""
import json
import os
import sys

import librosa
import numpy as np
import soundfile as sf

SRC = r"C:\Users\BlueGold\Music\The Dark Side of the Moon.flac"
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
SR = 22050

sys.stdout.reconfigure(encoding="utf-8")


def load_seg(mono, sr, t0, t1):
    return mono[int(t0 * sr): int(t1 * sr)]


def main():
    data, sr = sf.read(SRC, dtype="float32", always_2d=True)
    if sr != SR:
        n = int(round(data.shape[0] * SR / sr))
        data = data[np.linspace(0, data.shape[0] - 1, n).astype(np.int64)]
        sr = SR
    mono = data.mean(axis=1)
    meta = json.load(open(os.path.join(DATA, "tracks.json"), encoding="utf-8"))
    tracks = {t["n"]: t for t in meta["tracks"]}

    out = {}

    for name, n, window in [("Money", 6, 60.0), ("Time", 4, 40.0)]:
        tr = tracks[n]
        # 跳过前 40 秒（前奏/转场），取中间一段
        t0 = tr["start"] + 40
        t1 = min(t0 + window, tr["end"])
        seg = load_seg(mono, sr, t0, t1)
        onset = librosa.onset.onset_strength(y=seg, sr=sr)
        fps = len(onset) / (len(seg) / sr)
        tempo = float(np.atleast_1d(librosa.feature.tempo(onset_envelope=onset, sr=sr, aggregate=np.median))[0])
        beat_frames = fps * 60.0 / tempo
        x = onset - onset.mean()
        var = x.var() + 1e-9

        def acf(beats):
            lag = int(round(beat_frames * beats))
            if lag < 2 or lag >= len(x):
                return 0.0
            return float((x[:-lag] * x[lag:]).mean() / var)

        table = {f"{b} 拍": round(acf(b), 3) for b in (1, 2, 3, 4, 6, 7, 8, 12, 14, 16)}
        print(f"\n{name}  取样 {t0:.0f}–{t1:.0f}s  估计 tempo {tempo:.1f}  每拍 {beat_frames:.2f} 帧")
        for k, v in table.items():
            print(f"    {k:6s} {v:+.3f}")

        best_small = max([2, 3, 4], key=lambda b: acf(b))
        bar7, bar8 = acf(7), acf(8)
        # 只有 7 拍上的周期性确实是正的、并且明显强过 8 拍，才判 7/8。
        # 两个都是负数（整段没有小节级重复）时什么都不能判——第一版这里判错了一次。
        if bar7 > 0.05 and bar7 > bar8 * 1.3:
            verdict = "7-beat bars (7/8)"
        elif max(acf(4), acf(8), acf(16)) > 0.15 and bar7 <= bar8:
            verdict = "8-beat bars (4/4)"
        else:
            verdict = "inconclusive"
        print(f"  两小节候选：7拍 {bar7:+.3f} / 8拍 {bar8:+.3f} / 14拍 {acf(14):+.3f} / 16拍 {acf(16):+.3f}")

        out[name] = {
            "window": [round(t0, 1), round(t1, 1)],
            "tempo": round(tempo, 1),
            "beats_per_frame_ratio": round(beat_frames, 3),
            "acf_by_beats": table,
            "beat_periodicity_best": best_small,
            "bar7": round(bar7, 3),
            "bar8": round(bar8, 3),
            "verdict": verdict,
        }
        print(f"   判定：{out[name]['verdict']}")

    with open(os.path.join(DATA, "meter.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n写入 {os.path.join(DATA, 'meter.json')}")


if __name__ == "__main__":
    main()
