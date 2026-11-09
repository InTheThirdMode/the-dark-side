# -*- coding: utf-8 -*-
"""第三步：把整轨画成一张图。只有数据，没有一句话。

上：每秒 RMS（dBFS），十段用交替底色分隔，段号标在顶上。
下：每段的 crest factor（峰值与 RMS 之差，dB），横条。
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
import soundfile as sf

SRC = r"C:\Users\BlueGold\Music\The Dark Side of the Moon.flac"
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "img", "album.png")

SR = 22050
BIN = 1.0  # 每秒一个点

sys.stdout.reconfigure(encoding="utf-8")


def envelope():
    data, sr = sf.read(SRC, dtype="float32", always_2d=True)
    if sr != SR:
        n = int(round(data.shape[0] * SR / sr))
        data = data[np.linspace(0, data.shape[0] - 1, n).astype(np.int64)]
        sr = SR
    mono = data.mean(axis=1)
    hop = int(SR * BIN)
    n = len(mono) // hop
    blocks = mono[: n * hop].reshape(n, hop).astype(np.float64)
    rms = np.sqrt((blocks ** 2).mean(axis=1))
    db = 20 * np.log10(np.maximum(rms, 1e-6))
    return db, sr


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    meta = json.load(open(os.path.join(DATA, "tracks.json"), encoding="utf-8"))
    tracks = meta["tracks"]
    total = meta["file"]["duration"]
    db, _ = envelope()
    t = np.arange(len(db)) * BIN

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(22, 9), gridspec_kw={"height_ratios": [3.2, 1]}, sharex=False
    )
    fig.patch.set_facecolor("#0d1117")
    for a in (ax, ax2):
        a.set_facecolor("#0d1117")
        for s in a.spines.values():
            s.set_color("#30363d")
        a.tick_params(colors="#8b949e", labelsize=11)

    # 交替底色
    for i, tr in enumerate(tracks):
        if i % 2 == 0:
            ax.axvspan(tr["start"], tr["end"], color="#161b22", zorder=0)

    ax.fill_between(t, db, -70, color="#1f6feb", alpha=0.35, linewidth=0)
    ax.plot(t, db, color="#58a6ff", linewidth=0.6)
    avg = float(db[db > -60].mean())
    ax.axhline(avg, color="#f0883e", linewidth=0.8, linestyle="--", alpha=0.8)
    ax.text(total - 6, avg + 1.2, f"mean {avg:.1f} dBFS", color="#f0883e",
            fontsize=11, ha="right", va="bottom")

    for tr in tracks:
        mid = (tr["start"] + tr["end"]) / 2
        ax.text(mid, -8, str(tr["n"]), color="#c9d1d9", fontsize=13, ha="center",
                va="top", weight="bold")
        ax.axvline(tr["start"], color="#30363d", linewidth=0.6, alpha=0.7)

    ax.set_ylim(-58, -2)
    ax.set_xlim(0, total)
    ax.set_ylabel("RMS per second (dBFS)", color="#8b949e", fontsize=12)
    ax.set_xlabel("time (min:sec)", color="#8b949e", fontsize=12)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x // 60)}:{int(x % 60):02d}"))
    ax.grid(axis="y", color="#21262d", linewidth=0.6)
    ax.set_title("Pink Floyd — The Dark Side of the Moon (1973) · whole-track envelope, 10 segments",
                 color="#e6edf3", fontsize=15, pad=14, loc="left")

    # 下：crest factor
    xs = np.arange(len(tracks))
    crest = [tr["crest"] for tr in tracks]
    colors = ["#3fb950" if c >= 16 else "#d29922" for c in crest]
    ax2.bar(xs, crest, color=colors, width=0.62, zorder=3)
    for x, tr in zip(xs, tracks):
        ax2.text(x, tr["crest"] + 0.15, f"{tr['crest']:.1f}", color="#c9d1d9",
                 fontsize=10, ha="center", va="bottom")
    ax2.set_xticks(xs)
    ax2.set_xticklabels([f"{tr['n']}" for tr in tracks], color="#c9d1d9")
    ax2.set_ylim(0, max(crest) + 2)
    ax2.set_ylabel("crest (dB)", color="#8b949e", fontsize=11)
    ax2.grid(axis="y", color="#21262d", linewidth=0.6)
    ax2.set_xlabel("track", color="#8b949e", fontsize=11)

    fig.tight_layout()
    fig.savefig(OUT, dpi=140, facecolor=fig.get_facecolor())
    print(f"写入 {OUT}")

    dr = max(crest) - min(crest)
    print(f"crest 区间 {min(crest):.1f}–{max(crest):.1f} dB（跨度 {dr:.1f}）")


if __name__ == "__main__":
    main()
