# -*- coding: utf-8 -*-
"""第四步：每段的拍与调。

拍：对每段取中段 90 秒，librosa 做 onset envelope → 节拍跟踪，报两个候选
（tempo 与 tempo×2），并给出网格自相关在候选周期上的强度，便于判断是不是半速/倍速。

调：chroma_cqt 取均值，跟 Krumhansl-Schmuckler 的 24 个调性模板相关，报第一名。

这两样都是估计值，不当作定论——尤其是拍，7/8 这种非偶数拍会被算成 8 分音符脉冲的两倍。
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
SLICE = 90

sys.stdout.reconfigure(encoding="utf-8")

K_S_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
K_S_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def key_of(chroma):
    scores = []
    for i in range(12):
        rotated = np.roll(chroma, -i)
        scores.append((float(np.corrcoef(rotated, K_S_MAJOR)[0, 1]), NAMES[i] + " major"))
        scores.append((float(np.corrcoef(rotated, K_S_MINOR)[0, 1]), NAMES[i] + " minor"))
    scores.sort(reverse=True)
    return scores[0][1], round(scores[0][0], 3)


def main():
    meta = json.load(open(os.path.join(DATA, "tracks.json"), encoding="utf-8"))
    data, sr = sf.read(SRC, dtype="float32", always_2d=True)
    if sr != SR:
        n = int(round(data.shape[0] * SR / sr))
        data = data[np.linspace(0, data.shape[0] - 1, n).astype(np.int64)]
        sr = SR
    mono = data.mean(axis=1)

    out = []
    for tr in meta["tracks"]:
        a = tr["start"] + max(0, (tr["dur"] - SLICE) / 2)
        seg = mono[int(a * sr): int((a + min(SLICE, tr["dur"])) * sr)]
        if len(seg) < sr * 5:
            continue
        onset = librosa.onset.onset_strength(y=seg, sr=sr)
        tempo = librosa.feature.tempo(onset_envelope=onset, sr=sr, aggregate=np.median)
        bpm = float(np.atleast_1d(tempo)[0])

        # 网格自相关：在候选周期上取强度，判断半速/倍速
        def acf_at(b):
            lag = 60.0 / b * (len(onset) / (len(seg) / sr))  # frames per beat
            lag = int(round(lag))
            if lag < 2 or lag >= len(onset):
                return 0.0
            x = onset - onset.mean()
            return float((x[:-lag] * x[lag:]).mean() / (x.var() + 1e-9))

        cand = [bpm / 2, bpm, bpm * 2]
        strengths = [acf_at(b) for b in cand]
        pick = cand[int(np.argmax(strengths))]

        chroma = librosa.feature.chroma_cqt(y=seg, sr=sr).mean(axis=1)
        key, corr = key_of(chroma)

        row = {
            "n": tr["n"], "title": tr["title"],
            "bpm_raw": round(bpm, 1),
            "bpm_candidates": [round(c, 1) for c in cand],
            "acf": [round(s, 3) for s in strengths],
            "bpm_pick": round(pick, 1),
            "key": key, "key_corr": corr,
        }
        out.append(row)
        print(f"{tr['n']:2d} {tr['title'][:24]:26s} raw {bpm:6.1f}  cand {cand[0]:5.1f}/{cand[1]:5.1f}/{cand[2]:5.1f}  "
              f"acf {strengths[0]:.2f}/{strengths[1]:.2f}/{strengths[2]:.2f}  pick {pick:5.1f}  {key} ({corr:.2f})")

    with open(os.path.join(DATA, "music.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n写入 {os.path.join(DATA, 'music.json')}")


if __name__ == "__main__":
    main()
