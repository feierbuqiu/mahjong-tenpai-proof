"""Convert the other party's plan JSON ({"plan":[{"W":[names],"codes":[[i,j,k,l],...]},...]})
into the plain-text plan format read by census.exe:
    <W hex mask> <ncodes> <k> t1 .. tk t1 .. tk ...
Only the data layout of their file is used; no code of theirs is imported.
"""
import json
import sys

NAMES = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
         "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p",
         "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s",
         "E", "S", "W", "N", "P", "F", "C"]
ALIAS = {n: i for i, n in enumerate(NAMES)}
ALIAS.update({"Haku": 31, "Hatsu": 32, "Chun": 33,
              "1z": 27, "2z": 28, "3z": 29, "4z": 30, "5z": 31, "6z": 32, "7z": 33})


def tile(x):
    if isinstance(x, int):
        if not 0 <= x < 34:
            raise ValueError(f"tile index out of range: {x}")
        return x
    return ALIAS[x]


def main(src, dst):
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["plan"]
    k = data.get("k")
    out = []
    ncodes = 0
    for row in rows:
        mask = 0
        for name in row["W"]:
            mask |= 1 << tile(name)
        codes = row["codes"]
        for c in codes:
            if k is None:
                k = len(c)
            if len(c) != k:
                raise ValueError("mixed code lengths")
        flat = " ".join(" ".join(str(tile(t)) for t in c) for c in codes)
        out.append(f"{mask:x} {len(codes)} {k} {flat}\n")
        ncodes += len(codes)
    with open(dst, "w", encoding="ascii", newline="\n") as f:
        f.writelines(out)
    print(f"classes={len(rows)} codes={ncodes} k={k} -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
