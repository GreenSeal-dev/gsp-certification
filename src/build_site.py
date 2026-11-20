"""Build the public GSP website from the tagged versions of gsp_requirements.yml.

Scoring (weights, scores, completion rules) is still in beta, so the pages don't
display it. The download is the repository's gsp_requirements.yml, unchanged.

Every release tag (vX.Y.Z) is rendered as a frozen copy under /vX.Y.Z/, and the
latest release is rendered again at the site root. Run from the repository root:

    python src/build_site.py                       # production build into _site/
    python src/build_site.py --base-url http://localhost:8000 --include-working-tree
    python -m http.server -d _site 8000
"""
import hashlib
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, urlparse

import click
import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.path.insert(0, str(Path(__file__).parent))
from gsp_data import parse_requirements  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE_SRC = ROOT / "site"
REPO_URL = "https://github.com/GreenSeal-dev/gsp-certification"
CERT_URL = "https://www.greenseal.dev/gsp/"
LEVELS = {
    1: {"name": "Level 1", "short": "L1", "label": "Self-assessed",
        "summary": "The organisation assesses its own practices against the Level 1 practices."},
    2: {"name": "Level 2", "short": "L2", "label": "Verified",
        "summary": "Evidence for every Level 2 practice is independently reviewed."},
}
ID_RE = re.compile(r"^GSP-(?:L\d-)?([A-Z]+)-(\d+)$")
ISO_PREFIX = re.compile(r"^ISO/IEC TS 20125-1:2026\s*[–-]\s*")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def semver(tag):
    return tuple(int(x) for x in tag.lstrip("v").split("."))


def collect_sources(include_working_tree):
    """Return version sources, oldest first: dicts with version, ref, date, yaml, changelog."""
    tags = [t for t in git("tag", "-l", "v*").split() if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    sources = []
    for tag in sorted(tags, key=semver):
        changelog = git("show", f"{tag}:CHANGELOG.md")
        # The release date is the one in the changelog entry; fall back to the commit date.
        m = re.search(rf"^## \[{re.escape(tag[1:])}\] - (\d{{4}}-\d{{2}}-\d{{2}})", changelog, re.M)
        sources.append({
            "version": tag[1:], "ref": tag, "released": True,
            "date": m.group(1) if m else git("log", "-1", "--format=%cs", tag).strip(),
            "yaml": git("show", f"{tag}:gsp_requirements.yml"),
            "changelog": changelog,
        })
    if include_working_tree:
        text = (ROOT / "gsp_requirements.yml").read_text(encoding="utf-8")
        version = str(yaml.safe_load(text)["version"])
        if not sources or sources[-1]["yaml"] != text:
            if any(s["version"] == version for s in sources):
                version += "-dev"
            sources.append({
                "version": version, "ref": "main", "released": False,
                "date": date.today().isoformat(), "yaml": text,
                "changelog": (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
            })
    if not sources:
        raise click.ClickException("No vX.Y.Z tags found (is this a full clone with tags?).")
    return sources


def clean(text):
    return " ".join(str(text).split()) if text is not None else ""


def build_model(src, root):
    """Turn one version's YAML into the structure the templates use."""
    data = parse_requirements(src["yaml"])
    lines = src["yaml"].splitlines()
    prefix = f"{root}/v{src['version']}"
    categories, reqs = [], []
    for cat in data["categories"]:
        items = []
        for req in cat["requirements"]:
            m = ID_RE.match(req["id"])
            if not m:
                raise click.ClickException(f"Unexpected requirement id {req['id']!r}")
            line = next((i + 1 for i, ln in enumerate(lines)
                         if re.match(rf"\s*- id: {re.escape(req['id'])}\s*$", ln)), None)
            guidance = req.get("assessment_guidance") or {}
            items.append({
                "id": req["id"], "code": m.group(1), "title": clean(req["title"]),
                "requirement": clean(req.get("requirement")),
                "rationale": clean(req.get("rationale")),
                "evidence": [clean(e) for e in req.get("evidence_examples", [])],
                "scale": [{"option": o, "guidance": clean(guidance.get(o))}
                          for o in req.get("assessment_scale", [])],
                "priority": req.get("priority", ""),
                "levels": sorted(req["levels"]),
                "iso_phase": ISO_PREFIX.sub("", req["ts_alignment"]) if req.get("ts_alignment") else "",
                "line": line,
            })
        code = items[0]["code"] if items else re.sub(r"\W+", "-", cat["category"]).lower()
        category = {"name": cat["category"], "code": code, "slug": code.lower(),
                    "requirements": items}
        for i, item in enumerate(items):
            item["category"] = category
            item["prev"] = items[i - 1] if i > 0 else None
            item["next"] = items[i + 1] if i + 1 < len(items) else None
        categories.append(category)
        reqs.extend(items)
    levels = sorted({lv for r in reqs for lv in r["levels"]})
    return {
        **src, "frozen_prefix": prefix, "categories": categories, "requirements": reqs,
        "levels": [{"n": lv, **LEVELS.get(lv, {"name": f"Level {lv}", "short": f"L{lv}",
                                               "label": "", "summary": ""}),
                    "count": sum(lv in r["levels"] for r in reqs)}
                   for lv in levels],
        "year": src["date"][:4],
    }


def check_links(out, root):
    """Fail if any internal link points to a file that was not generated."""
    missing = set()
    for page in out.rglob("*.html"):
        for href in re.findall(r'(?:href|src)="([^"]+)"', page.read_text(encoding="utf-8")):
            if not href.startswith(f"{root}/") or href.startswith("//"):
                continue
            path = href[len(root):].split("#")[0].split("?")[0]
            target = out / path.lstrip("/")
            if path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                missing.add(f"{href}  (in {page.relative_to(out)})")
    if missing:
        raise click.ClickException("Broken internal links:\n  " + "\n  ".join(sorted(missing)))


@click.command()
@click.option("--out", default="_site", type=click.Path(file_okay=False), show_default=True)
@click.option("--base-url", default="https://gsp.greenseal.dev", show_default=True,
              help="Public URL of the site, used for canonical links and citations.")
@click.option("--include-working-tree", is_flag=True,
              help="Also build the uncommitted gsp_requirements.yml as an unreleased version.")
def main(out, base_url, include_working_tree):
    base_url = base_url.rstrip("/")
    root = urlparse(base_url).path.rstrip("/")
    out = Path(out)
    if not out.is_absolute():
        out = ROOT / out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(SITE_SRC / "static", out / "static")

    versions = [build_model(s, root) for s in collect_sources(include_working_tree)]
    released = [v for v in versions if v["released"]]
    latest = versions[-1]
    for v in versions:
        v["is_latest"] = v is latest
    by_id = {}
    for v in versions:
        for r in v["requirements"]:
            by_id.setdefault(r["id"], []).append(v)
    latest_ids = {r["id"] for r in latest["requirements"]}
    blurbs = yaml.safe_load((SITE_SRC / "categories.yml").read_text(encoding="utf-8"))

    env = Environment(loader=FileSystemLoader(SITE_SRC / "templates"),
                      autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
    # Content hashes in asset URLs, so browsers fetch new CSS/JS after a change.
    asset_v = {name: hashlib.sha1((SITE_SRC / "static" / name).read_bytes()).hexdigest()[:8]
               for name in ("style.css", "filter.js")}
    env.globals.update(asset_v=asset_v, root=root, base_url=base_url, repo_url=REPO_URL, cert_url=CERT_URL,
                       latest=latest, versions=versions, released=released,
                       blurbs=blurbs, level_info=LEVELS)

    def write(path, template, **ctx):
        target = out / path.lstrip("/")
        if not path.endswith(".html"):
            target = target / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(env.get_template(template).render(**ctx), encoding="utf-8")

    for v in versions:
        # Each version is frozen under /vX.Y.Z/; the latest is also served at the root.
        targets = [(f"/v{v['version']}", v["frozen_prefix"])]
        if v is latest:
            targets.append(("", root))
        dl_dir = out / f"v{v['version']}" / "downloads"
        dl_dir.mkdir(parents=True)
        # The download is the repository's YAML for this version, byte for byte.
        (dl_dir / "gsp_requirements.yml").write_text(v["yaml"], encoding="utf-8")
        v["downloads"] = [{"name": "gsp_requirements.yml", "label": "Requirements", "kind": "YAML"}]
        for path_prefix, prefix in targets:
            ctx = {"v": v, "prefix": prefix, "at_root": path_prefix == ""}
            canonical = lambda p: f"{base_url}{p}"  # noqa: E731
            write(f"{path_prefix}/", "home.html", **ctx, canonical=canonical("/"),
                  page_title=None, nav="home")
            write(f"{path_prefix}/practices/", "practices.html", **ctx,
                  canonical=canonical("/practices/"), page_title="Practices", nav="practices")
            for r in v["requirements"]:
                issue = REPO_URL + "/issues/new?" + urlencode({
                    "title": f"[{r['id']}] ",
                    "body": f"Practice: {r['id']} ({r['title']})\nVersion: {v['version']}\n\n"
                            "What should change, and why?\n",
                })
                key = re.sub(r"\W", "_", f"{r['id']}_v{v['version']}").lower()
                bibtex = (f"@misc{{{key},\n"
                          f"  author       = {{{{GreenSeal.dev}}}},\n"
                          f"  title        = {{{{{r['id']}}}: {r['title']}}},\n"
                          f"  howpublished = {{Green Software Practices (GSP), version {v['version']}}},\n"
                          f"  year         = {{{v['year']}}},\n"
                          f"  url          = {{{base_url}/v{v['version']}/practices/{r['id']}/}}\n}}")
                write(f"{path_prefix}/practices/{r['id']}/", "practice.html", **ctx, r=r, bibtex=bibtex,
                      canonical=canonical(f"/practices/{r['id']}/" if r["id"] in latest_ids
                                          else f"/v{v['version']}/practices/{r['id']}/"),
                      page_title=f"{r['id']}: {r['title']}", nav="practices",
                      other_versions=by_id[r["id"]], issue_url=issue)

    ctx = {"v": latest, "prefix": root, "at_root": True}
    write("/versions/", "versions.html", **ctx, canonical=f"{base_url}/versions/",
          page_title="Versions", nav="versions",
          changelog=markdown.markdown(latest["changelog"].split("\n", 1)[1]
                                      if latest["changelog"].startswith("# ") else latest["changelog"]))
    write("/about/", "about.html", **ctx, canonical=f"{base_url}/about/",
          page_title="Licence and certification", nav="about")
    write("/404.html", "404.html", **ctx, canonical=None, page_title="Page not found", nav=None)

    pages = ["/", "/practices/", "/versions/", "/about/"] + \
        [f"/practices/{r['id']}/" for r in latest["requirements"]]
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{base_url}{p}</loc></url>\n" for p in pages)
        + "</urlset>\n", encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n",
                                    encoding="utf-8")

    check_links(out, root)
    n_pages = sum(1 for _ in out.rglob("*.html"))
    click.echo(f"✓ Built {n_pages} pages for {', '.join('v' + v['version'] for v in versions)} "
               f"(latest v{latest['version']}) into {out}")


if __name__ == "__main__":
    main()
