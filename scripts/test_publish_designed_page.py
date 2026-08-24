#!/usr/bin/env python3
"""Focused safety and output checks for publish_designed_page.py."""
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish_designed_page as designed  # noqa: E402

with open(
    os.path.join(designed.pp.ROOT, "content", "mastermind-page.json"),
    encoding="utf-8",
) as handle:
    VERIFIED_VIDEOS = json.load(handle)["videos"]


PAYLOAD = {
    "title": "The Develop Mastermind: Coaching for Builders Doing £750k to £5m",
    "slug": "courses/mastermind-course",
    "meta_description": "A coaching programme for established construction business owners.",
    "content_file": "content/mastermind.html",
    "shell": "about-greg-wilkes",
    "date": "2026-08-24",
    "date_published": "2026-08-11",
    "image_url": "/wp-content/uploads/2026/08/mastermind-poster.jpg",
    "image_width": 1280,
    "image_height": 720,
    "image_alt": "The Develop Mastermind coaching programme for UK construction business owners",
    "ga4_event_transport": True,
    "videos": VERIFIED_VIDEOS,
}

failures = []


def check(name: str, ok: bool) -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(name)


def refused(fn) -> bool:
    try:
        fn()
    except SystemExit:
        return True
    return False


def run_main(payload: dict, *flags: str) -> None:
    fd, payload_path = tempfile.mkstemp(prefix="designed-page-", suffix=".json")
    os.close(fd)
    real_argv = sys.argv
    try:
        with open(payload_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        sys.argv = ["publish_designed_page.py", "--json", payload_path, *flags]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            designed.main()
    finally:
        sys.argv = real_argv
        os.unlink(payload_path)


def main() -> None:
    html = designed.build_page(PAYLOAD)
    with open("content/_design-system.css", encoding="utf-8") as handle:
        css = handle.read()
    check(
        "designed body present",
        'class="dc2-page"' in html and "Five pillars. One plan." in html,
    )
    check(
        "main site navigation present",
        'class="elementor elementor-4222 elementor-location-header"' in html
        and 'class="dc2-nav__links"' not in html
        and "Free Trainings" in html
        and "Client Wins" in html
        and "My Story" in html
        and "Podcast" in html,
    )
    check(
        "main site header is visible and only the shell footer is hidden",
        ".elementor-location-header,\n.elementor-location-footer" not in html
        and ".elementor-location-footer {\n  display: none !important;" in html,
    )
    header_html = html[html.find("<header") : html.find("</header>") + len("</header>")]
    mastermind_anchors = re.findall(
        r'<a\b[^>]*href="/courses/mastermind-course/"[^>]*>', header_html
    )
    my_story_anchors = re.findall(
        r'<a\b[^>]*href="/about-greg-wilkes/"[^>]*>', header_html
    )
    check(
        "Mastermind is the current shared navigation item",
        len(mastermind_anchors) == 2
        and all('aria-current="page"' in anchor for anchor in mastermind_anchors)
        and all("elementor-item-active" in anchor for anchor in mastermind_anchors)
        and header_html.count("current-menu-item current_page_item") == 2,
    )
    check(
        "shell page is not marked current in shared navigation",
        len(my_story_anchors) == 2
        and all('aria-current="page"' not in anchor for anchor in my_story_anchors)
        and all("elementor-item-active" not in anchor for anchor in my_story_anchors),
    )
    check("five pillar icons present", html.count('class="dc2-pillar-icon"') == 5)
    check("four software cards present", html.count("<article><span>0") == 4)
    check("nine testimonial videos present", html.count('class="dc2-youtube"') == 9)
    check("nine poster-first testimonials present", html.count('class="dc2-youtube__poster"') == 9)
    check("testimonial player receives keyboard focus", "iframe.tabIndex = 0" in html and "iframe.focus()" in html)
    check("nine high-resolution testimonial images present", html.count("maxresdefault.jpg") >= 9)
    check("testimonial videos load on click", "link.replaceWith(iframe)" in html and "?autoplay=1" in html)
    check(
        "five Mastermind CTA positions are labelled for analytics",
        html.count("data-analytics-location=") == 5
        and all(
            f'data-analytics-location="{location}"' in html
            for location in ("hero", "programme", "investment", "final", "sticky")
        ),
    )
    check(
        "Mastermind CTA and testimonial start events are present",
        "mastermind_cta_click" in html
        and "mastermind_testimonial_video_start" in html
        and 'window.ga4Event("event", name, parameters)' in html
        and "const fallback = window.setTimeout(navigate, 900)" in html
        and "window.clearTimeout(fallback)" in html
        and "if (regularNavigation && !sent) navigate()" in html
        and "parameters.event_timeout = 800" in html
        and "cta_location" in html
        and "testimonial_name" in html,
    )
    check(
        "page-specific GA4 event transport suppresses duplicate page views",
        html.count("data-ga4-event-transport") == 1
        and "G-PXT2VCVFLW" in html
        and "ga4EventLayer" in html
        and "send_page_view:false" in html
        and "if(previewHost&&!tagAssistant) return" in html,
    )
    schedule_path = os.path.join(designed.pp.WWW, "schedule-a-call", "index.html")
    with open(schedule_path, encoding="utf-8") as handle:
        schedule_html = handle.read()
    check(
        "FlowBuild scheduler start uses iframe focus evidence",
        "scale_session_scheduler_start" in schedule_html
        and "d.activeElement" in schedule_html
        and "w.ga4Event('event','scale_session_scheduler_start'" in schedule_html
        and "if(typeof w.ga4Event!=='function') return" in schedule_html
        and "https://link.flow-build.com/widget/booking/" in schedule_html,
    )
    check(
        "schedule page GA4 event transport suppresses duplicate page views",
        schedule_html.count("data-ga4-event-transport") == 1
        and "ga4EventLayer" in schedule_html
        and "send_page_view:false" in schedule_html
        and "if(previewHost&&!tagAssistant) return" in schedule_html,
    )
    check(
        "nine visible transcript summaries present",
        html.count('class="dc2-transcript-summary"') == 9
        and html.count("<h4>Transcript summary</h4>") == 9,
    )
    check("pillar headings use aligned rows", "grid-template-rows: auto 64px 1fr" in html)
    check(
        "official Develop Coaching palette present",
        all(colour in html.lower() for colour in ("#fdce36", "#fbaa35", "#0069b1", "#414042", "#d2d2d2")),
    )
    approved_hex = {
        "#ffffff", "#fdce36", "#fbaa35", "#0069b1", "#414042", "#d2d2d2",
        "#3e745b", "#a64c3d",
    }
    found_hex = {value.lower() for value in re.findall(r"#[0-9a-fA-F]{6}", css)}
    rgba_bases = {
        tuple(map(int, match))
        for match in re.findall(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css)
    }
    check(
        "custom CSS rejects off-brand colour literals",
        found_hex <= approved_hex and rgba_bases <= {(65, 64, 66), (255, 255, 255)},
    )
    check(
        "Source Sans Pro is the only custom page font",
        "family=Source+Sans+Pro" in html
        and "family=Archivo" not in html
        and "IBM+Plex+Mono" not in html
        and "Georgia" not in html,
    )
    check(
        "James result accurately qualified",
        "£1.5m <span>towards £4m</span>" in html
        and "Scaling from £1.5m towards £4m" in html,
    )
    check("Bradley result verified", "From £5k jobs to a £730k project" in html)
    check("Dale result qualified", "Turnover roughly doubled" in html)
    check("testimonial footer removed", 'class="dc2-proof__cta"' not in html)
    check(
        "testimonial qualifiers removed",
        "projected" not in html.lower() and "forecast" not in html.lower(),
    )
    check("site chrome present", "<header" in html and "<footer" in html)
    check(
        "custom footer uses the live privacy route",
        'href="https://develop-coaching.com/privacy/"' in html
        and 'href="https://develop-coaching.com/privacy-policy/"' not in html,
    )
    check("title replaced", f"<title>{PAYLOAD['title']}</title>" in html)
    schema_match = re.search(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
    )
    schema = json.loads(schema_match.group(1)) if schema_match else {}
    authors = [
        node for node in schema.get("@graph", [])
        if node.get("@id") == designed.pp.AUTHOR_ID
    ]
    check("JSON-LD has one canonical author", len(authors) == 1)
    schema_text = json.dumps(schema, separators=(",", ":"))
    check(
        "JSON-LD drops shell page identity",
        "/about-greg-wilkes/#webpage" not in schema_text
        and '"@type":"AboutPage"' not in schema_text
    )
    graph = schema.get("@graph", [])
    services = [node for node in graph if node.get("@type") == "Service"]
    videos = [node for node in graph if node.get("@type") == "VideoObject"]
    organizations = [
        node for node in graph if node.get("@id") == f"{designed.pp.DOMAIN}/#organization"
    ]
    webpages = [node for node in graph if node.get("@id") == f"{designed.pp.DOMAIN}/{PAYLOAD['slug']}/"]
    check(
        "JSON-LD describes the coaching offer as a Service",
        len(services) == 1
        and services[0].get("serviceType") == "Construction business coaching programme"
        and services[0].get("provider", {}).get("@id") == f"{designed.pp.DOMAIN}/#organization"
        and services[0].get("areaServed", {}).get("name") == "United Kingdom",
    )
    check(
        "JSON-LD removes inaccurate local business details",
        len(organizations) == 1
        and organizations[0].get("@type") == "Organization"
        and not any(node.get("@type") == "Place" for node in graph)
        and all(key not in organizations[0] for key in ("address", "openingHours", "location")),
    )
    check(
        "WebPage dates and main entity are current",
        len(webpages) == 1
        and webpages[0].get("datePublished") == "2026-08-11"
        and webpages[0].get("dateModified") == "2026-08-24"
        and webpages[0].get("mainEntity", {}).get("@id") == f"{designed.pp.DOMAIN}/{PAYLOAD['slug']}/#service",
    )
    check("JSON-LD has no Article node", not any(node.get("@type") == "Article" for node in graph))
    check(
        "JSON-LD has nine complete testimonial videos",
        len(videos) == 9
        and len({node.get("@id") for node in videos}) == 9
        and len({node.get("name") for node in videos}) == 9
        and len({node.get("description") for node in videos}) == 9
        and all(
            node.get("name")
            and node.get("description")
            and node.get("thumbnailUrl", "").startswith("https://i.ytimg.com/vi/")
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}", node.get("uploadDate", ""))
            and re.fullmatch(r"PT\d+M\d+S", node.get("duration", ""))
            and node.get("embedUrl", "").startswith("https://www.youtube.com/embed/")
            and node.get("publisher", {}).get("@id") == f"{designed.pp.DOMAIN}/#organization"
            and node.get("isPartOf", {}).get("@id") == f"{designed.pp.DOMAIN}/{PAYLOAD['slug']}/"
            and "contentUrl" not in node
            for node in videos
        ),
    )
    check(
        "schema descriptions match visible summaries",
        all(node["description"] in html for node in videos),
    )
    check(
        "social image metadata is consistent",
        html.count('content="https://develop-coaching.com/wp-content/uploads/2026/08/mastermind-poster.jpg"') >= 3
        and '<meta property="og:image:width" content="1280" />' in html
        and '<meta property="og:image:height" content="720" />' in html
        and '<meta property="og:type" content="website" />' in html,
    )
    check(
        "stale article and video social tags removed",
        "article:published_time" not in html
        and "article:modified_time" not in html
        and "article:publisher" not in html
        and "og:updated_time" not in html
        and "og:video" not in html
        and "ya:ovs:" not in html
        and "Time to read" not in html,
    )
    check(
        "traversal slug refused",
        refused(lambda: designed.build_page({**PAYLOAD, "slug": "../../tmp/escape"})),
    )
    check(
        "absolute shell refused",
        refused(lambda: designed.build_page({**PAYLOAD, "shell": "/tmp/escape"})),
    )
    check(
        "content escape refused",
        refused(lambda: designed.build_page({**PAYLOAD, "content_file": "/etc/passwd"})),
    )
    check(
        "incomplete testimonial metadata refused",
        refused(
            lambda: designed.build_page(
                {**PAYLOAD, "videos": [{"id": "missing-fields"}]}
            )
        ),
    )
    check(
        "non-object testimonial metadata refused",
        refused(lambda: designed.build_page({**PAYLOAD, "videos": ["invalid"]})),
    )
    for field, invalid_value in (
        ("thumbnail_url", "not-a-url"),
        ("upload_date", "2026-02-30"),
        ("duration", "PT2M5"),
        ("embed_url", "not-a-url"),
    ):
        check(
            f"invalid testimonial {field} refused",
            refused(
                lambda field=field, invalid_value=invalid_value: designed.build_page(
                    {
                        **PAYLOAD,
                        "videos": [{**VERIFIED_VIDEOS[0], field: invalid_value}],
                    }
                )
            ),
        )
    check(
        "duplicate testimonial name refused",
        refused(
            lambda: designed.build_page(
                {
                    **PAYLOAD,
                    "videos": [
                        VERIFIED_VIDEOS[0],
                        {**VERIFIED_VIDEOS[1], "name": VERIFIED_VIDEOS[0]["name"]},
                    ],
                }
            )
        ),
    )
    check(
        "duplicate testimonial description refused",
        refused(
            lambda: designed.build_page(
                {
                    **PAYLOAD,
                    "videos": [
                        VERIFIED_VIDEOS[0],
                        {
                            **VERIFIED_VIDEOS[1],
                            "description": VERIFIED_VIDEOS[0]["description"],
                        },
                    ],
                }
            )
        ),
    )
    check(
        "CSS escape refused",
        refused(lambda: designed.build_page({**PAYLOAD, "css_files": ["/etc/passwd"]})),
    )

    out_file = os.path.join(designed.pp.WWW, PAYLOAD["slug"], "index.html")
    before = hashlib.sha256(open(out_file, "rb").read()).hexdigest()
    check("existing page refused", refused(lambda: run_main(PAYLOAD)))
    run_main(PAYLOAD, "--dry-run")
    after = hashlib.sha256(open(out_file, "rb").read()).hexdigest()
    check("dry run leaves existing page unchanged", before == after)

    if failures:
        raise SystemExit(f"{len(failures)} check(s) failed: {', '.join(failures)}")
    print("all checks passed")


if __name__ == "__main__":
    main()
