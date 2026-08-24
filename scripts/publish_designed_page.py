#!/usr/bin/env python3
"""Publish a custom-designed page into the static site.

publish_page.py reuses an exported page wholesale, which is right for blog
posts but leaves the body locked to the Elementor blog layout. Landing pages
need their own design, so this keeps only the chrome from an exported page (the
<head>, the site header and the footer, which carry the nav, fonts, tracking
and brand styling) and replaces everything between the header and footer with
hand-written markup and CSS.

That split is safe because the region between </header> and <footer> is
div-balanced in the export, so dropping it whole leaves valid HTML.

    python3 scripts/publish_designed_page.py --json page.json

    {
      "title": "...",
      "slug": "courses/mastermind-course",
      "meta_description": "...",
      "content_file": "content/mastermind.html",   # body markup + its <style>
      "shell": "courses/mastermind-course",        # page to borrow chrome from
      "date": "2026-08-11",
      "image_url": "/wp-content/..."
    }
"""
import argparse
import datetime
import html as htmllib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish_page as pp  # noqa: E402

DEFAULT_SHELL = "courses/mastermind-course"
CURRENT_MENU_CLASSES = {
    "current-menu-item",
    "current_page_item",
    "current-menu-ancestor",
    "current-menu-parent",
    "elementor-item-active",
}

GA4_EVENT_TRANSPORT = """<script async data-ga4-event-transport src="https://www.googletagmanager.com/gtag/js?id=G-PXT2VCVFLW&amp;l=ga4EventLayer"></script>
<script data-ga4-event-transport>
window.ga4EventLayer = window.ga4EventLayer || [];
window.ga4Event = window.ga4Event || function(){ window.ga4EventLayer.push(arguments); };
window.ga4Event('js', new Date());
window.ga4Event('config', 'G-PXT2VCVFLW', {send_page_view: false});
</script>"""


def replace_meta(head: str, attribute: str, key: str, value: str) -> str:
    """Replace one existing social meta tag without creating duplicates."""
    pattern = rf'<meta {attribute}="{re.escape(key)}" content=".*?" />'
    replacement = f'<meta {attribute}="{key}" content="{htmllib.escape(str(value), quote=True)}" />'
    return re.sub(pattern, replacement, head, count=1, flags=re.S)


def remove_meta(head: str, attribute: str, key_pattern: str) -> str:
    """Remove stale social tags copied from the shell page."""
    return re.sub(
        rf'\s*<meta {attribute}="{key_pattern}" content=".*?" />',
        "",
        head,
        flags=re.S,
    )


def rewrite_service_jsonld(
    head: str,
    *,
    title: str,
    description: str,
    url: str,
    date_published: str,
    date_modified: str,
    image: str,
    image_width: int,
    image_height: int,
    videos: list[dict],
) -> str:
    """Describe the coaching page and its verified testimonial videos."""
    pattern = re.compile(
        r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)', re.S
    )
    match = pattern.search(head)
    if not match:
        return head

    data = json.loads(match.group(2))
    graph = data.get("@graph", [])
    org_id = f"{pp.DOMAIN}/#organization"
    webpage_id = url
    service_id = f"{url}#service"
    cleaned = []

    for node in graph:
        node_type = node.get("@type")
        if node_type == "Place":
            continue
        if node.get("@id") == org_id:
            node["@type"] = "Organization"
            for key in ("address", "openingHours", "location"):
                node.pop(key, None)
        if node.get("@id") == webpage_id:
            node["datePublished"] = date_published
            node["dateModified"] = date_modified
            node["mainEntity"] = {"@id": service_id}
        if node_type == "Article":
            continue
        cleaned.append(node)

    cleaned.append(
        {
            "@type": "Service",
            "@id": service_id,
            "name": title,
            "description": description,
            "url": url,
            "serviceType": "Construction business coaching programme",
            "provider": {"@id": org_id},
            "areaServed": {"@type": "Country", "name": "United Kingdom"},
            "audience": {
                "@type": "Audience",
                "audienceType": (
                    "Established UK construction business owners turning over "
                    "£750k to £5m"
                ),
            },
            "image": {
                "@type": "ImageObject",
                "url": image,
                "width": image_width,
                "height": image_height,
            },
            "mainEntityOfPage": {"@id": webpage_id},
        }
    )

    required_video_fields = {
        "id",
        "name",
        "description",
        "thumbnail_url",
        "upload_date",
        "duration",
        "embed_url",
    }
    seen_video_ids = set()
    seen_video_names = set()
    seen_video_descriptions = set()
    for video in videos:
        if not isinstance(video, dict):
            raise SystemExit(
                "publish_designed_page: testimonial video must be an object"
            )
        missing = sorted(required_video_fields - video.keys())
        if missing:
            raise SystemExit(
                "publish_designed_page: testimonial video is missing fields: "
                + ", ".join(missing)
            )
        video_id = str(video["id"]).strip()
        if not video_id or video_id in seen_video_ids:
            raise SystemExit(
                f"publish_designed_page: testimonial video id is empty or repeated: {video_id!r}"
            )
        video_name = str(video["name"]).strip()
        if not video_name or video_name in seen_video_names:
            raise SystemExit(
                "publish_designed_page: testimonial video name is empty or repeated: "
                f"{video_name!r}"
            )
        video_description = str(video["description"]).strip()
        if not video_description or video_description in seen_video_descriptions:
            raise SystemExit(
                "publish_designed_page: testimonial video description is empty or repeated: "
                f"{video_description!r}"
            )
        thumbnail_url = str(video["thumbnail_url"]).strip()
        upload_date = str(video["upload_date"]).strip()
        duration = str(video["duration"]).strip()
        embed_url = str(video["embed_url"]).strip()
        if not thumbnail_url.startswith("https://") or re.search(r"\s", thumbnail_url):
            raise SystemExit(
                f"publish_designed_page: invalid testimonial thumbnail URL: {thumbnail_url!r}"
            )
        try:
            datetime.date.fromisoformat(upload_date)
        except ValueError:
            raise SystemExit(
                f"publish_designed_page: invalid testimonial upload date: {upload_date!r}"
            ) from None
        if not re.fullmatch(r"PT\d+M\d+S", duration):
            raise SystemExit(
                f"publish_designed_page: invalid testimonial duration: {duration!r}"
            )
        if not embed_url.startswith("https://") or re.search(r"\s", embed_url):
            raise SystemExit(
                f"publish_designed_page: invalid testimonial embed URL: {embed_url!r}"
            )
        seen_video_ids.add(video_id)
        seen_video_names.add(video_name)
        seen_video_descriptions.add(video_description)
        cleaned.append(
            {
                "@type": "VideoObject",
                "@id": f"{url}#video-{video_id}",
                "name": video_name,
                "description": video_description,
                "thumbnailUrl": thumbnail_url,
                "uploadDate": upload_date,
                "duration": duration,
                "embedUrl": embed_url,
                "publisher": {"@id": org_id},
                "isPartOf": {"@id": webpage_id},
                "inLanguage": "en-GB",
            }
        )
    data["@graph"] = cleaned
    replacement = match.group(1) + json.dumps(data, separators=(",", ":")) + match.group(3)
    return head[: match.start()] + replacement + head[match.end() :]


def rewrite_header_current_page(head: str, slug: str) -> str:
    """Move the shell header's current-page state to the generated page."""
    header_start = head.find("<header")
    header_end = head.find("</header>")
    if header_start == -1 or header_end == -1:
        return head
    header_end += len("</header>")
    header = head[header_start:header_end]

    def clean_classes(match: re.Match) -> str:
        classes = [
            value
            for value in match.group(1).split()
            if value not in CURRENT_MENU_CLASSES
        ]
        return f'class="{" ".join(classes)}"'

    header = re.sub(r'class="([^"]*)"', clean_classes, header)
    header = re.sub(r'\s+aria-current="page"', "", header)

    target_href = f'/{slug.strip("/")}/'
    target_pattern = re.compile(
        rf'(<li class=")([^"]*)(">\s*<a\s+)([^>]*\bhref="{re.escape(target_href)}"[^>]*)>'
    )

    def mark_current(match: re.Match) -> str:
        li_classes = match.group(2).split() + ["current-menu-item", "current_page_item"]
        attrs = match.group(4)
        class_match = re.search(r'class="([^"]*)"', attrs)
        if class_match:
            anchor_classes = class_match.group(1).split()
            if "elementor-item-active" not in anchor_classes:
                anchor_classes.append("elementor-item-active")
            attrs = (
                attrs[: class_match.start()]
                + f'class="{" ".join(anchor_classes)}"'
                + attrs[class_match.end() :]
            )
        else:
            attrs += ' class="elementor-item-active"'
        if 'aria-current="page"' not in attrs:
            attrs += ' aria-current="page"'
        return match.group(1) + " ".join(li_classes) + match.group(3) + attrs + ">"

    header = target_pattern.sub(mark_current, header)
    return head[:header_start] + header + head[header_end:]


def safe_repo_file(value: str, label: str) -> str:
    """Resolve a payload file inside the repository and refuse escapes."""
    raw = (value or "").strip()
    if not raw:
        raise SystemExit(f"publish_designed_page: missing {label}")
    root = os.path.realpath(pp.ROOT)
    target = os.path.realpath(raw if os.path.isabs(raw) else os.path.join(root, raw))
    try:
        contained = target != root and os.path.commonpath([root, target]) == root
    except ValueError:
        contained = False
    if not contained:
        raise SystemExit(f"publish_designed_page: {label} escapes the repository: {value!r}")
    if not os.path.isfile(target):
        raise SystemExit(f"publish_designed_page: {label} not found: {value!r}")
    return target


def split_chrome(html: str) -> tuple[str, str]:
    """Return (everything up to and including </header>, everything from <footer>)."""
    marker = html.find("</header>")
    footer = html.find("<footer")
    if marker == -1 or footer == -1 or footer < marker:
        raise SystemExit("publish_designed_page: could not find header/footer in the shell page")
    return html[: marker + len("</header>")], html[footer:]


def build_page(payload: dict) -> str:
    shell_slug = pp.safe_site_path(payload.get("shell") or DEFAULT_SHELL, "shell")
    shell_path = os.path.join(pp.WWW, shell_slug, "index.html")
    if not os.path.exists(shell_path):
        raise SystemExit(f"publish_designed_page: shell page not found: {shell_path}")

    content_path = safe_repo_file(payload["content_file"], "content file")

    html = open(shell_path, encoding="utf-8").read()
    content = open(content_path, encoding="utf-8").read()

    title = payload["title"].strip()
    slug = pp.safe_site_path(payload["slug"], "slug")
    description = (payload.get("meta_description") or "").strip()
    date = payload.get("date") or datetime.date.today().isoformat()
    date_published = payload.get("date_published") or date
    image = payload.get("image_url") or ""
    if image.startswith("/"):
        image = pp.DOMAIN + image
    url = f"{pp.DOMAIN}/{slug}/"
    esc = lambda s: htmllib.escape(s, quote=True)

    head, footer = split_chrome(html)
    head = rewrite_header_current_page(head, slug)

    # Same SEO slots as the blog publisher, applied to the chrome's <head>.
    head = pp.slot(head, r"<title>.*?</title>", f"<title>{esc(title)}</title>", "<title>", 1)
    head = re.sub(
        r'<meta name="description" content=".*?"/>',
        lambda _: f'<meta name="description" content="{esc(description)}"/>',
        head,
        count=1,
        flags=re.S,
    )
    head = re.sub(
        r'<link rel="canonical" href=".*?" />',
        lambda _: f'<link rel="canonical" href="{url}" />',
        head,
        count=1,
        flags=re.S,
    )
    for prop, value in [
        ("og:type", "website"),
        ("og:title", title),
        ("og:description", description),
        ("og:url", url),
        ("og:image", image or pp.LOGO),
        ("og:image:secure_url", image or pp.LOGO),
        ("og:image:width", payload.get("image_width", 1200)),
        ("og:image:height", payload.get("image_height", 630)),
        ("og:image:alt", payload.get("image_alt") or title),
        ("og:image:type", "image/jpeg"),
    ]:
        head = replace_meta(head, "property", prop, value)
    for name, value in [
        ("twitter:title", title),
        ("twitter:description", description),
        ("twitter:image", image or pp.LOGO),
    ]:
        head = replace_meta(head, "name", name, value)

    for prop in (
        "article:publisher",
        "article:published_time",
        "article:modified_time",
        "og:updated_time",
        "og:video",
        r'ya:ovs:[^\"]+',
    ):
        head = remove_meta(head, "property", prop)
    for name in ("twitter:label1", "twitter:data1"):
        head = remove_meta(head, "name", name)

    head = pp.rewrite_jsonld(
        head, title=title, description=description, url=url, date=date, image=image
    )
    head = rewrite_service_jsonld(
        head,
        title=title,
        description=description,
        url=url,
        date_published=date_published,
        date_modified=date,
        image=image or pp.LOGO,
        image_width=int(payload.get("image_width", 1200)),
        image_height=int(payload.get("image_height", 630)),
        videos=payload.get("videos", []),
    )
    if payload.get("ga4_event_transport"):
        head = head.replace("</head>", GA4_EVENT_TRANSPORT + "\n</head>", 1)
    for pattern in pp.STALE_TAGS:
        head = pattern.sub("", head)
    footer = re.sub(r"\s*<!-- Page cached by LiteSpeed Cache[^>]*-->\s*$", "\n", footer)

    # Shared CSS is inlined rather than linked so a page is one self-contained
    # file, matching how the rest of the export works.
    css_parts = []
    for css_file in payload.get("css_files", ["content/_design-system.css"]):
        css_path = safe_repo_file(css_file, "CSS file")
        css_parts.append(open(css_path, encoding="utf-8").read())

    fonts = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Source+Sans+Pro:ital,wght@0,400;0,700;1,400;1,700&display=swap">'
    )
    style = "<style>\n" + "\n".join(css_parts) + "\n</style>"

    return (
        f"{head}\n{fonts}\n{style}\n"
        f'<div class="dc-page">\n{content.strip()}\n</div>\n{footer}'
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing page (refused by default)",
    )
    args = ap.parse_args()

    payload = json.load(open(args.json, encoding="utf-8"))
    for field in ("title", "slug", "content_file"):
        if not payload.get(field):
            raise SystemExit(f"publish_designed_page: missing required field: {field}")

    slug = pp.safe_site_path(payload["slug"], "slug")
    date = payload.get("date") or datetime.date.today().isoformat()
    html = build_page(payload)

    out_file = os.path.join(pp.WWW, slug, "index.html")
    existed = os.path.exists(out_file)
    overwrite = bool(args.overwrite or payload.get("overwrite"))
    if existed and not overwrite and not args.dry_run:
        raise SystemExit(
            f"publish_designed_page: page already exists: {out_file}. "
            'Pass --overwrite (or "overwrite": true in the payload) to replace it.'
        )
    if not args.dry_run:
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        open(out_file, "w", encoding="utf-8").write(html)
        pp.update_sitemap(slug, date)
        search_kind = payload.get("search_kind") or (
            "courses" if slug.startswith("courses/") else "pages"
        )
        pp.update_search_index(
            payload["title"],
            slug,
            payload.get("meta_description") or "",
            kind=search_kind,
        )

    print(
        json.dumps(
            {
                "path": os.path.relpath(out_file, pp.ROOT),
                "url": f"{pp.DOMAIN}/{slug}/",
                "created": not existed,
                "bytes": len(html),
                "dry_run": bool(args.dry_run),
            }
        )
    )


if __name__ == "__main__":
    main()
