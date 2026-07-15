#!/usr/bin/env python3
"""Fetch NYC district boundary GeoJSON layers, normalize a single label
property per feature, and write minimal GeoJSON for map-side simplification.

Source: NYC Open Data (data.cityofnewyork.us) geospatial GeoJSON exports,
all originally published by the NYC Dept. of City Planning and partner
agencies. No API token needed for the geospatial export endpoint.
"""
import json, os, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
LABELED = os.path.join(ROOT, "data", "labeled")
OUT = os.path.join(ROOT, "docs", "data")
for d in (RAW, LABELED, OUT):
    os.makedirs(d, exist_ok=True)

with open(os.path.join(ROOT, "scripts", "layers.json")) as f:
    LAYERS = json.load(f)

BORO = {1: "Manhattan", 2: "Bronx", 3: "Brooklyn", 4: "Queens", 5: "Staten Island"}

# geometry-simplification percentage by rough feature count
def simplify_pct(n):
    if n > 1500: return "5%"
    if n > 300:  return "9%"
    if n > 120:  return "14%"
    return "20%"

def fetch(layer):
    url = f"https://data.cityofnewyork.us/api/geospatial/{layer['id']}?method=export&format=GeoJSON"
    dst = os.path.join(RAW, layer["key"] + ".geojson")
    if os.path.exists(dst) and os.path.getsize(dst) > 2000:
        return dst
    print(f"  fetching {layer['key']} ({layer['id']}) ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "nyc-district-boundaries/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    with open(dst, "wb") as f:
        f.write(data)
    return dst

def make_label(layer, props):
    kind = layer["label_kind"]
    fld = layer["label_field"]
    v = props.get(fld)
    if kind == "community_board":
        # boro_cd like 101 -> Manhattan CB 1; codes >18 are park/airport
        # "joint interest areas," not real community boards.
        try:
            code = int(float(v)); b = code // 100; cb = code % 100
            if cb > 18:
                return f"{BORO.get(b, '?')} — joint interest area"
            return f"{BORO.get(b, '?')} CB {cb}"
        except Exception:
            return str(v)
    if kind == "census_tract":
        # boroct2020 like 1000100 -> Manhattan tract 1
        try:
            b = int(str(v)[0]); return f"{BORO.get(b,'?')} tract {str(v)[1:].lstrip('0') or '0'}"
        except Exception:
            return str(v)
    if kind == "fire_company":
        t = {"E": "Engine", "L": "Ladder", "Q": "Squad"}.get(props.get("fire_co_type"), props.get("fire_co_type") or "")
        n = props.get("fire_co_num") or ""
        try: n = str(int(float(n)))
        except Exception: pass
        return f"{t} {n}".strip()
    if kind == "election":
        # elect_dist like 23001 = Assembly District 23, Election District 1
        try:
            s = str(int(float(v))).zfill(5)
            return f"AD {int(s[:2])} · ED {int(s[2:])}"
        except Exception:
            return str(v)
    if kind == "prefix":
        try: v = str(int(float(v)))
        except Exception: v = str(v)
        return layer.get("label_prefix", "") + v
    # raw
    return "" if v is None else str(v)

def process(layer, raw_path):
    with open(raw_path) as f:
        gj = json.load(f)
    feats_in = gj.get("features", [])
    out = []
    for ft in feats_in:
        geom = ft.get("geometry")
        if not geom or not geom.get("coordinates"):
            continue
        props = ft.get("properties", {}) or {}
        # historic districts: keep only current designated boundaries
        if layer["key"] == "historic":
            if str(props.get("current_", "")).strip().lower() not in ("yes", "y", "true", "1"):
                continue
        # hurricane evac: keep only the six official zones (drop "X"=none and stray codes)
        if layer["key"] == "hurricane_evac":
            if str(props.get("hurricane_", "")).strip() not in ("1", "2", "3", "4", "5", "6"):
                continue
        nm = make_label(layer, props)
        out.append({"type": "Feature", "properties": {"nm": nm}, "geometry": geom})
    if not out:
        keys = list((feats_in[0].get("properties") or {}).keys()) if feats_in else []
        raise SystemExit(f"!! {layer['key']}: 0 usable features. property keys seen: {keys}")
    labeled = os.path.join(LABELED, layer["key"] + ".geojson")
    with open(labeled, "w") as f:
        json.dump({"type": "FeatureCollection", "features": out}, f)
    return labeled, len(out)

def simplify(layer, labeled_path, n):
    out = os.path.join(OUT, layer["key"] + ".json")
    # a few layers are few-but-very-detailed coastline polygons; thin them harder
    pct = "7%" if layer["key"] in ("hurricane_evac",) else simplify_pct(n)
    cmd = ["npx", "--yes", "mapshaper", labeled_path,
           "-simplify", pct, "keep-shapes",
           "-clean",
           "-o", "format=geojson", "precision=0.00001", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out, os.path.getsize(out)

def main():
    manifest = []
    for layer in LAYERS:
        raw = fetch(layer)
        labeled, n = process(layer, raw)
        out, size = simplify(layer, labeled, n)
        kb = size / 1024
        print(f"  {layer['key']:16s} {n:5d} feats  ->  {kb:8.1f} KB", flush=True)
        m = dict(layer); m["actual_count"] = n; m["file"] = "data/" + layer["key"] + ".json"
        m["size_kb"] = round(kb, 1)
        manifest.append(m)
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    total = sum(m["size_kb"] for m in manifest)
    print(f"\nDONE. {len(manifest)} layers, {total/1024:.2f} MB total (lazy-loaded).")

if __name__ == "__main__":
    main()
