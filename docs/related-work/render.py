#!/usr/bin/env python3
"""Render the related-work survey records from their JSON into readable Markdown.

Each cluster has one JSON file under data/: the first reader's entries and the
skeptic's verdicts, retrieved on the date the file records. This script writes one
Markdown record per cluster beside it. Corrections the skeptic made are shown next
to the claim they correct, and both are kept, because a record shows change rather
than hiding it. Standard-library Python 3.11+.

    python3 docs/related-work/render.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

FIELDS = [
    ("organisation", "Organisation"),
    ("kind", "Kind"),
    ("self_description", "Self-description, as read"),
    ("subject_scope", "Subject scope"),
    ("primary_sources_used", "Sources it says it uses"),
    ("outputs", "Outputs"),
    ("derived_scoring_or_ranking", "Per-person derived score or rank, as observed"),
    ("identifiers_exposed", "Identifiers exposed"),
    ("signal_precedents", "Per-filing conditions it states or computes"),
    ("openness_code", "Code"),
    ("openness_data_license", "Data licence"),
    ("openness_api", "API"),
    ("funding_or_business_model", "Funding or business model, as stated"),
    ("disclaimer_or_frame", "How it frames what a listing means"),
    ("status_as_of_retrieval", "Status at retrieval"),
]


def bullets(value) -> str:
    if isinstance(value, list):
        return "\n".join(f"  - {v}" for v in value) if value else "  - none observed"
    return f"  {value}"


def render(cluster: dict) -> str:
    retrieved = cluster["retrieved"]
    out = [f"# Related-work record: {cluster['title']}", ""]
    out.append(
        f"*Read on {retrieved}. A first reader wrote each entry from the project's own pages; "
        "a second reader, briefed to refute, re-fetched every cited page. Corrections are shown "
        "beside the claims they correct and both are kept. Presence in this record is not a "
        "claim about a project's quality, and absence is not either. Presence in the register "
        "is not evidence of wrongdoing: where a record below describes what a neighbour "
        "published about an officeholder, it describes the role and not the person, names "
        "no one outside a citation URL, and is not a Finding. Rendered from "
        f"`data/{cluster['key']}.json` by `render.py`; edit the JSON, not this file.*"
    )
    out.append("")
    verdicts = {v["name"]: v for v in cluster["skeptic"].get("verdicts", [])}
    for e in cluster["sweep"]["entries"]:
        v = verdicts.get(e["name"], {})
        out.append(f"## {e['name']}")
        out.append("")
        out.append(f"<{e['url']}>")
        out.append("")
        for key, label in FIELDS:
            if key in e:
                out.append(f"- **{label}.**")
                out.append(bullets(e[key]))
        if v.get("refuted"):
            out.append("- **Corrected on second reading.**")
            for r in v["refuted"]:
                out.append(
                    f"  - *{r['field']}.* First read: {r['claim']} "
                    f"On re-reading: {r['correction']} (<{r['citation_url']}>)"
                )
        cnv = list(e.get("could_not_verify", [])) + [
            u for u in v.get("unverifiable", []) if u not in e.get("could_not_verify", [])
        ]
        if cnv:
            out.append("- **Not verified.**")
            out.append(bullets(cnv))
        if v.get("confirmed"):
            n = len(v["confirmed"])
            out.append(f"- **Confirmed by the second reader.** {n} claims, listed in the JSON.")
        out.append("- **Citations.**")
        for c in e.get("citations", []):
            out.append(f"  - <{c['url']}> (retrieved {c['retrieved']}): {c['supports']}")
        out.append("")
    unreached = cluster["sweep"].get("could_not_reach", [])
    if unreached:
        out.append("## Pages the first reader could not reach")
        out.append("")
        out.extend(f"- {u}" for u in unreached)
        out.append("")
    missing = cluster["skeptic"].get("missing_in_cluster", [])
    if missing:
        out.append("## Projects the second reader said were missing from this cluster")
        out.append("")
        out.extend(f"- **{m['name']}.** <{m['url']}> {m['why']}" for m in missing)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    for path in sorted(DATA.glob("*.json")):
        cluster = json.loads(path.read_text(encoding="utf-8"))
        target = HERE / f"{cluster['key']}.md"
        target.write_text(render(cluster), encoding="utf-8", newline="\n")
        print(f"rendered {cluster['key']}.md ({len(cluster['sweep']['entries'])} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
