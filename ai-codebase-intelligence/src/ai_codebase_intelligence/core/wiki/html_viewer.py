"""HTML viewer — 1:1 port of gitnexus core/wiki/html-viewer.js."""
from __future__ import annotations

import json
import os
from typing import Any


def generate_html_viewer(wiki_dir: str, project_name: str) -> str:
    module_tree: list[dict[str, Any]] = []
    try:
        with open(os.path.join(wiki_dir, "module_tree.json"), encoding="utf-8") as f:
            module_tree = json.load(f)
    except (OSError, json.JSONDecodeError):
        pass

    meta: dict[str, Any] | None = None
    try:
        with open(os.path.join(wiki_dir, "meta.json"), encoding="utf-8") as f:
            meta = json.load(f)
    except (OSError, json.JSONDecodeError):
        pass

    pages: dict[str, str] = {}
    try:
        for fname in os.listdir(wiki_dir):
            if fname.endswith(".md"):
                with open(os.path.join(wiki_dir, fname), encoding="utf-8") as f:
                    pages[fname[:-3]] = f.read()
    except OSError:
        pass

    html = _build_html(project_name, module_tree, pages, meta)
    output = os.path.join(wiki_dir, "index.html")
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    return output


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _build_html(
    project_name: str,
    module_tree: list[dict[str, Any]],
    pages: dict[str, str],
    meta: dict[str, Any] | None,
) -> str:
    pages_json = json.dumps(pages)
    tree_json = json.dumps(module_tree)
    meta_json = json.dumps(meta)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(project_name)} — Wiki</title>
<script src="https://cdn.jsdelivr.net/npm/marked@11.0.0/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;line-height:1.65}}
.layout{{display:flex;min-height:100vh}}
.sidebar{{width:280px;background:#f8f9fb;border-right:1px solid #e5e7eb;position:fixed;top:0;left:0;bottom:0;overflow-y:auto;padding:24px 16px}}
.content{{margin-left:280px;flex:1;padding:48px 64px;max-width:960px}}
.nav-item{{display:block;padding:7px 12px;border-radius:8px;cursor:pointer;font-size:13px}}
.nav-item:hover{{background:#f1f5f9}}
.nav-item.active{{background:#eff6ff;color:#2563eb;font-weight:600}}
</style>
</head>
<body>
<div class="layout">
<nav class="sidebar"><div id="nav-tree"></div></nav>
<main class="content" id="content"><h2>Loading...</h2></main>
</div>
<script>
var PAGES = {pages_json};
var TREE = {tree_json};
var META = {meta_json};
document.addEventListener('DOMContentLoaded', function() {{
  mermaid.initialize({{ startOnLoad: false, theme: 'neutral' }});
  var nav = document.getElementById('nav-tree');
  nav.innerHTML = '<a class="nav-item active" data-page="overview" href="#overview">Overview</a>';
  function render(tree, container) {{
    for (var i = 0; i < tree.length; i++) {{
      var a = document.createElement('a');
      a.className = 'nav-item';
      a.dataset.page = tree[i].slug;
      a.href = '#' + tree[i].slug;
      a.textContent = tree[i].name;
      container.appendChild(a);
      if (tree[i].children) render(tree[i].children, container);
    }}
  }}
  render(TREE, nav);
  nav.addEventListener('click', function(e) {{
    var t = e.target;
    while (t && !t.dataset.page) t = t.parentElement;
    if (t) {{ e.preventDefault(); navigate(t.dataset.page); }}
  }});
  navigate('overview');
}});
function navigate(page) {{
  var items = document.querySelectorAll('.nav-item');
  for (var i = 0; i < items.length; i++) items[i].classList.remove('active');
  var el = document.querySelector('[data-page="' + page + '"]');
  if (el) el.classList.add('active');
  var md = PAGES[page];
  var content = document.getElementById('content');
  content.innerHTML = md ? marked.parse(md) : '<h2>Page not found</h2>';
  try {{ mermaid.run({{ querySelector: '.mermaid' }}); }} catch(e) {{}}
  window.scrollTo(0, 0);
}}
</script>
</body>
</html>"""
