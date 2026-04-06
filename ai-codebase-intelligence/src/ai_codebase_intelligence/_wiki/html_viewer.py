"""HTML wiki viewer generation."""
from __future__ import annotations

import html
import re

from .generator import WikiDocument, WikiSection


def _section_id(title: str) -> str:
    """Convert a section title to a URL-safe identifier.

    Args:
        title: Human-readable section title.

    Returns:
        Lowercased, hyphen-separated identifier.
    """
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _render_section(section: WikiSection, level: int = 2) -> str:
    """Render a single section and its children to HTML.

    Args:
        section: The wiki section to render.
        level: Heading level (2-6).

    Returns:
        HTML fragment for the section.
    """
    sid = _section_id(section.title)
    tag = f"h{min(level, 6)}"
    escaped_title = html.escape(section.title)
    escaped_content = html.escape(section.content)

    parts = [
        f'<section id="{sid}">',
        f"<{tag}>{escaped_title}</{tag}>",
        f"<p>{escaped_content}</p>",
    ]
    for child in section.children:
        parts.append(_render_section(child, level + 1))
    parts.append("</section>")
    return "\n".join(parts)


def generate_html(doc: WikiDocument) -> str:
    """Generate a full HTML page from a WikiDocument.

    Args:
        doc: The wiki document to render.

    Returns:
        Complete HTML string with DOCTYPE, styles, and scripts.
    """
    escaped_title = html.escape(doc.title)

    sections_html = "\n".join(
        _render_section(s) for s in doc.sections
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escaped_title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; max-width: 960px; margin: 0 auto; padding: 24px; }}
section {{ margin-bottom: 24px; }}
.controls {{ margin-bottom: 16px; }}
.controls button {{ margin-right: 8px; padding: 6px 12px; cursor: pointer; }}
</style>
</head>
<body>
<h1>{escaped_title}</h1>
<div class="controls">
<button id="expand-all">Expand All</button>
<button id="collapse-all">Collapse All</button>
</div>
{sections_html}
<script>
document.getElementById('expand-all').addEventListener('click', function() {{
  document.querySelectorAll('details').forEach(function(d) {{ d.open = true; }});
}});
document.getElementById('collapse-all').addEventListener('click', function() {{
  document.querySelectorAll('details').forEach(function(d) {{ d.open = false; }});
}});
</script>
</body>
</html>"""
