#!/usr/bin/env python3
"""Reproducible Quran counts over a pinned morphology file (Quranic Arabic Corpus v0.4 format).

Every number shown in a quran-data-essay video must come from this script (or another
script in scripts/quran/) run against a pinned data file, never typed by hand.

Data line format (tab-separated):  sura:ayah:word:segment  form  POS  TAG|TAG|LEM:x|ROOT:y
Unit of counting is the WORD (sura:ayah:word), not the segment: a word matches when any
of its segments matches all filters.

Usage:
  count.py --data FILE verses
  count.py --data FILE words
  count.py --data FILE match --lemma آخِر [--root أخر] [--pos N] [--feat F --feat FS ...]
           [--not-feat M ...] [--name akhirah] [--csv out.csv] [--json out.json]
  count.py --data FILE selftest

--feat X     the matching segment must carry feature X; repeat for AND (--feat IMPV --feat 2MS).
             X is either an exact tag (IMPV, PERF, PASS, ADJ) or a person/gender/number
             spec: F matches F, FS, FD, FP, 3FS…; 2MS matches 2MS; MP matches MP, 3MP…
             (F never matches FUT).
--not-feat X the matching segment must not carry feature X.
"""
import argparse, csv, hashlib, json, re, sys
from collections import OrderedDict


def load(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            loc, form, pos, feats = line.rstrip("\n").split("\t")
            s, a, w, g = (int(x) for x in loc.split(":"))
            tags = feats.split("|")
            kv = dict(t.split(":", 1) for t in tags if ":" in t)
            rows.append({"s": s, "a": a, "w": w, "g": g, "form": form, "pos": pos,
                         "tags": tags, "lem": kv.get("LEM"), "root": kv.get("ROOT")})
    return rows


def words(rows):
    out = OrderedDict()
    for r in rows:
        out.setdefault((r["s"], r["a"], r["w"]), []).append(r)
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def seg_ok(seg, a):
    if a.lemma and seg["lem"] != a.lemma:
        return False
    if a.root and seg["root"] != a.root:
        return False
    if a.pos and seg["pos"] != a.pos:
        return False
    return True


PGN = re.compile(r"([123]?)([MF]?)([SDP]?)")


def has_feat(tags, v):
    """Exact tag, or person/gender/number spec compared component by component."""
    if v in tags:
        return True
    want = PGN.fullmatch(v)
    if not v or not want:
        return False
    for t in tags:
        got = PGN.fullmatch(t) if t else None
        if got and all(w == "" or w == g for w, g in zip(want.groups(), got.groups())):
            return True
    return False


def word_matches(segs, a):
    for g in segs:
        if not seg_ok(g, a):
            continue
        if a.feat and not all(has_feat(g["tags"], f) for f in a.feat):
            continue
        if a.not_feat and any(has_feat(g["tags"], f) for f in a.not_feat):
            continue
        return True
    return False


def cmd_match(rows, a, data_path):
    found = [(k, segs) for k, segs in words(rows).items() if word_matches(segs, a)]
    result = {
        "name": a.name or a.lemma or a.root,
        "count": len(found),
        "unit": "word",
        "rule": {"lemma": a.lemma, "root": a.root, "pos": a.pos,
                 "feat": a.feat, "not_feat": a.not_feat},
        "data": {"file": data_path, "sha256": sha256(data_path)},
        "verses": len({(s, v) for (s, v, _), _ in found}),
    }
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["sura", "ayah", "word", "form", "tags"])
            for (s, v, w), segs in found:
                wr.writerow([s, v, w, "".join(g["form"] for g in segs),
                             " ".join("|".join(g["tags"]) for g in segs)])
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))
    return result


def selftest(rows, data_path):
    """Known values for the pinned file (sha256 742bfac5…). A mismatch means the data
    or the matcher changed — stop and investigate before trusting any count."""
    ns = argparse.Namespace
    base = dict(root=None, pos=None, feat=None, not_feat=None, name=None, csv=None, json=None)
    checks = [
        ("verses", len({(r["s"], r["a"]) for r in rows}), 6236),
        ("dunya (lemma دُنْيا)", None, 115, dict(lemma="دُنْيا")),
        ("akhirah (lemma آخِر, feminine)", None, 115, dict(lemma="آخِر", feat=["F"])),
        ("akhir all genders (lemma آخِر)", None, 155, dict(lemma="آخِر")),
        ("Isa (lemma عِيسَى)", None, 25, dict(lemma="عِيسَى")),
        ("Adam (lemma آدَم)", None, 25, dict(lemma="آدَم")),
        ("shahr singular (lemma شَهْر, not dual/plural)", None, 12,
         dict(lemma="شَهْر", not_feat=["MD", "MP"])),
        ("shahr all forms", None, 21, dict(lemma="شَهْر")),
        ("qul (lemma قالَ, imperative 2MS)", None, 332, dict(lemma="قالَ", feat=["IMPV", "2MS"])),
        ("qalu (lemma قالَ, perfect 3MP)", None, 332, dict(lemma="قالَ", feat=["PERF", "3MP"])),
    ]
    ok = True
    w = words(rows)
    for c in checks:
        label, got, want = c[0], c[1], c[2]
        if got is None:
            a = ns(**{**base, **c[3]})
            got = sum(1 for segs in w.values() if word_matches(segs, a))
        flag = "ok" if got == want else "MISMATCH"
        ok &= got == want
        print(f"{flag:8} {label}: {got} (expected {want})")
    print("data sha256:", sha256(data_path))
    sys.exit(0 if ok else 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verses")
    sub.add_parser("words")
    sub.add_parser("selftest")
    m = sub.add_parser("match")
    m.add_argument("--lemma"); m.add_argument("--root"); m.add_argument("--pos")
    m.add_argument("--feat", action="append"); m.add_argument("--not-feat", action="append")
    m.add_argument("--name"); m.add_argument("--csv"); m.add_argument("--json")
    a = p.parse_args()
    rows = load(a.data)
    if a.cmd == "verses":
        print(len({(r["s"], r["a"]) for r in rows}))
    elif a.cmd == "words":
        print(len(words(rows)))
    elif a.cmd == "selftest":
        selftest(rows, a.data)
    else:
        if not (a.lemma or a.root):
            p.error("match needs --lemma or --root")
        cmd_match(rows, a, a.data)


if __name__ == "__main__":
    main()
