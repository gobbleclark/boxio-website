#!/usr/bin/env python3
"""
One-time generator for src/assets/us-states.json (state outlines for the site's maps).

Source data: us-atlas@3.0.1 states-albers-10m.json (public domain, U.S. Census Bureau),
already projected to Albers USA in a 975x610 frame.
    curl -L https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/states-albers-10m.json -o /tmp/states.json
    python3 tools/make_us_map.py /tmp/states.json
"""
import json
import sys
from pathlib import Path

ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}
MIN_STEP = 0.7  # px; drop points closer than this to the previous kept point


def main(src):
    topo = json.loads(Path(src).read_text())
    (sx, sy), (tx, ty) = topo["transform"]["scale"], topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idxs):
        pts = []
        for i in idxs:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a[1:] if pts else a)
        kept = [pts[0]]
        for p in pts[1:-1]:
            if abs(p[0] - kept[-1][0]) + abs(p[1] - kept[-1][1]) >= MIN_STEP:
                kept.append(p)
        if len(kept) < 3:
            return ""
        return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in kept) + "Z"

    out = []
    for g in topo["objects"]["states"]["geometries"]:
        name = g["properties"]["name"]
        if name not in ABBR:
            continue
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        d = "".join(ring(r) for poly in polys for r in poly)
        out.append({"id": ABBR[name], "name": name, "d": d})
    out.sort(key=lambda s: s["id"])
    dest = Path(__file__).resolve().parent.parent / "src" / "assets" / "us-states.json"
    dest.write_text(json.dumps({"viewBox": "0 0 975 610", "states": out}, separators=(",", ":")))
    print(f"Wrote {len(out)} states, {dest.stat().st_size / 1024:.0f} KB -> {dest}")


if __name__ == "__main__":
    main(sys.argv[1])
