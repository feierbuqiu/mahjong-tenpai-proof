"""SHA-256 manifest of a Lean project's sources (no build output).

usage: python -I manifest.py <project dir> <out.json>

* `lean_files`: path -> sha256 for every `*.lean` file outside `.lake`;
* `lean_set_sha256`: sha256 of `json.dumps(lean_files, sort_keys=True, separators=(',', ':'))`,
  the same digest the 2026-10-20 static review used, so the two can be compared directly;
* `config_files`: lakefile.toml, lean-toolchain, lake-manifest.json;
* `all_sha256`: one digest over both maps.
"""
import sys, json, hashlib, pathlib

root = pathlib.Path(sys.argv[1])
lean = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob('*.lean')) if '.lake' not in p.parts}
cfg = {n: hashlib.sha256((root / n).read_bytes()).hexdigest()
       for n in ('lakefile.toml', 'lean-toolchain', 'lake-manifest.json')}
dig = lambda d: hashlib.sha256(json.dumps(d, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
out = {'lean_file_count': len(lean), 'lean_set_sha256': dig(lean), 'all_sha256': dig({'lean': lean, 'config': cfg}),
       'config_files': cfg, 'lean_files': lean}
pathlib.Path(sys.argv[2]).write_text(json.dumps(out, indent=1, sort_keys=True), encoding='utf-8')
print(f"{len(lean)} lean files  lean_set_sha256 {out['lean_set_sha256']}  all_sha256 {out['all_sha256']}")
