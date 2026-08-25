#!/usr/bin/env python3
"""Keep the shared Develop Coaching navigation concise and current."""

import re
import sys
from pathlib import Path


REMOVED_MENU_IDS = ("menu-item-7952", "menu-item-9177", "menu-item-14446")
FREE_TRAININGS_MENU_ID = "menu-item-16753"
MY_STORY_MENU_ID = "menu-item-9176"
NAVIGATION_STYLE = """<style id="dc-simplified-navigation">
@media (min-width: 1025px) {
  .elementor-element-d083c1c {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-rows: auto auto;
    align-items: center;
  }
  .elementor-element-dcb2a0c {
    grid-column: 1 / -1;
    grid-row: 1;
    justify-self: end;
    width: auto !important;
  }
  .elementor-element-b81d386 {
    grid-column: 1;
    grid-row: 2;
    width: auto !important;
    max-width: none !important;
  }
  .elementor-element-7804adf {
    grid-column: 2;
    grid-row: 2;
    align-self: center;
    width: auto !important;
    margin-left: 18px !important;
  }
}
@media (max-width: 767px) {
  .elementor-element-bca47e7 > .e-con-inner {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 12px;
    padding: 12px 16px 8px !important;
  }
  .elementor-element-41f4756,
  .elementor-element-d083c1c,
  .elementor-element-b81d386 {
    width: auto !important;
    min-width: 0 !important;
  }
  .elementor-element-f54cf12 {
    width: 190px !important;
  }
  .elementor-element-f54cf12 img {
    width: 190px !important;
    height: auto !important;
  }
  .elementor-element-12f3659 > .e-con-inner {
    padding: 0 16px 8px !important;
  }
  .elementor-element-79870bb {
    justify-content: flex-end !important;
  }
}
</style>"""


def _menu_item_start(html: str, menu_id: str, offset: int = 0):
    return re.search(
        rf'<li\b[^>]*class="[^"]*\b{re.escape(menu_id)}\b[^"]*"[^>]*>',
        html[offset:],
        re.I,
    )


def _menu_item_end(html: str, start: int) -> int:
    """Return the end of an li element, including any nested submenu items."""
    depth = 0
    for token in re.finditer(r"<li\b|</li\s*>", html[start:], re.I):
        if token.group(0).lower().startswith("<li"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return start + token.end()
    raise ValueError("Unbalanced navigation list item")


def _remove_menu_items(html: str, menu_id: str) -> str:
    offset = 0
    while match := _menu_item_start(html, menu_id, offset):
        start = offset + match.start()
        end = _menu_item_end(html, start)
        html = html[:start] + html[end:]
        offset = start
    return html


def _rename_menu_item(html: str, menu_id: str, old_label: str, new_label: str) -> str:
    offset = 0
    while match := _menu_item_start(html, menu_id, offset):
        start = offset + match.start()
        end = _menu_item_end(html, start)
        item = html[start:end]
        updated, count = re.subn(
            rf">\s*{re.escape(old_label)}\s*</a>",
            f">{new_label}</a>",
            item,
            count=1,
            flags=re.I,
        )
        if count == 0 and re.search(
            rf">\s*{re.escape(new_label)}\s*</a>", item, re.I
        ):
            updated = item
        elif count != 1:
            raise ValueError(f"Could not rename the {old_label} menu item")
        html = html[:start] + updated + html[end:]
        offset = start + len(updated)
    return html


def simplify_main_navigation(html: str) -> str:
    """Remove outdated top-level items without deleting their destination pages."""
    for menu_id in REMOVED_MENU_IDS:
        html = _remove_menu_items(html, menu_id)
    html = _rename_menu_item(
        html, FREE_TRAININGS_MENU_ID, "Free Trainings", "Free Resources"
    )
    html = _rename_menu_item(html, MY_STORY_MENU_ID, "My Story", "About Greg")
    style_pattern = re.compile(
        r'<style id="dc-simplified-navigation">.*?</style>', re.S | re.I
    )
    if style_pattern.search(html):
        html = style_pattern.sub(NAVIGATION_STYLE, html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", f"{NAVIGATION_STYLE}\n</head>", 1)
    return html


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "www")
    changed = 0
    for path in sorted(root.rglob("*.html")):
        original = path.read_text(encoding="utf-8", errors="ignore")
        updated = simplify_main_navigation(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"Updated navigation in {changed} HTML files")


if __name__ == "__main__":
    main()
