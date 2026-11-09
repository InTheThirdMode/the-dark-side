# -*- coding: utf-8 -*-
"""第二次自检：把整条流水线从零跑一遍，跟仓库里提交的结果比。

验证的是"可复现"——同样的输入跑两次，数字应该一模一样。
这一步第一次自检没做，因为第一次只查了"README 抄得对不对"，查不出算法是否稳定。
"""
import json
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
BAK = os.path.join(BASE, "_data_bak")
PY = sys.executable

sys.stdout.reconfigure(encoding="utf-8")

STEPS = ["01_gaps.py", "02_analyze.py", "04_tempo.py", "05_meter.py"]


def run(script):
    r = subprocess.run([PY, os.path.join(BASE, script)], capture_output=True, text=True,
                       errors="ignore", cwd=BASE)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-3:]


def flat(obj, pre=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from flat(v, f"{pre}.{k}" if pre else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from flat(v, f"{pre}[{i}]")
    else:
        yield pre, obj


def compare(a, b, name):
    fa, fb = dict(flat(a)), dict(flat(b))
    keys = set(fa) & set(fb)
    diffs = []
    for k in keys:
        x, y = fa[k], fb[k]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            if abs(float(x) - float(y)) > 1e-6:
                diffs.append((k, x, y))
        elif x != y:
            diffs.append((k, x, y))
    print(f"  {name}: 比了 {len(keys)} 个字段，不同 {len(diffs)} 处")
    for k, x, y in diffs[:12]:
        print(f"      {k}: 提交 {x} → 重跑 {y}")
    return diffs


def main():
    if os.path.exists(BAK):
        shutil.rmtree(BAK)
    shutil.copytree(DATA, BAK)
    for f in os.listdir(DATA):
        os.remove(os.path.join(DATA, f))

    for s in STEPS:
        code, tail = run(s)
        print(f"  {s} → exit {code}")
        if code != 0:
            for line in tail:
                print("      ", line)
            return 1

    total = 0
    for name in ("gaps.json", "tracks.json", "music.json", "meter.json"):
        old = json.load(open(os.path.join(BAK, name), encoding="utf-8"))
        new = json.load(open(os.path.join(DATA, name), encoding="utf-8"))
        total += len(compare(old, new, name))

    print(f"\n总计不可复现的字段：{total}")
    shutil.rmtree(BAK)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
