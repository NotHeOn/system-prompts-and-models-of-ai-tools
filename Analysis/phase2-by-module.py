#!/usr/bin/env python3
"""
Phase 2 – By-Module Aggregation
---------------------------------
Reads the same 20 detected source files, re-extracts content,
then writes one .md per module showing all tools side by side.

Output: Analysis/phase2-content/by-module/
  01-identity.md
  02-behavior.md
  03-tools.md
  04-output-format.md
  05-constraints.md
  06-environment.md
  07-examples.md
  08-task-management.md
"""

import json
import re
from pathlib import Path

BASE     = Path(__file__).parent.parent
ANALYSIS = BASE / "Analysis"
CONFIG   = ANALYSIS / "module-detection-config.json"
OUT_DIR  = ANALYSIS / "phase2-content" / "by-module"
XML_SRC  = ANALYSIS / "format-classification" / "xml"  / "system-prompt"
MD_SRC   = ANALYSIS / "format-classification" / "markdown" / "system-prompt"

# Files confirmed in detected/ (skip CodeBuddy)
SKIP = {"CodeBuddy Prompts__Craft Prompt.txt"}


# ── extraction (same helpers as phase2-extract.py) ────────────────────────────

def extract_xml_tag(content: str, tag: str) -> list[str]:
    pat = rf'<{re.escape(tag)}[^>]*>([\s\S]*?)</{re.escape(tag)}>'
    return [m.strip() for m in re.findall(pat, content, re.IGNORECASE)]


def extract_markdown_section(content: str, keyword: str) -> list[str]:
    lines   = content.split('\n')
    results = []
    i = 0
    while i < len(lines):
        m = re.match(r'^(#{1,4})\s+(.+)', lines[i])
        if m and keyword.lower() in lines[i].lower():
            level   = len(m.group(1))
            section = [lines[i]]
            i += 1
            while i < len(lines):
                nm = re.match(r'^(#{1,4})\s+', lines[i])
                if nm and len(nm.group(1)) <= level:
                    break
                section.append(lines[i])
                i += 1
            text = '\n'.join(section).strip()
            if len(text) > len(section[0]):
                results.append(text)
        else:
            i += 1
    return results


def detect_module(content: str, mod: dict, fmt: str) -> dict | None:
    """Return {'matched': [...], 'excerpts': [...]} or None."""
    excerpts = []
    matched  = []

    if fmt == 'xml':
        for tag in mod['detection']['xml']['tags']:
            hits = extract_xml_tag(content, tag)
            if hits:
                matched.append(tag)
                excerpts += hits
    else:
        for kw in mod['detection']['markdown']['keywords']:
            hits = extract_markdown_section(content, kw)
            if hits:
                matched.append(kw)
                excerpts += hits

    if excerpts:
        return {'matched': matched, 'excerpts': excerpts, 'via': 'structured'}

    # fallback
    for pat in mod['detection']['fallback']['patterns']:
        flags = re.MULTILINE
        if re.search(pat, content, flags):
            return {'matched': [pat], 'excerpts': [], 'via': 'fallback'}

    return None


# ── collect all data ──────────────────────────────────────────────────────────

def collect(modules: list) -> dict:
    """
    Returns:
      { module_id: [ {tool, fmt, matched, excerpts, via}, ... ] }
    """
    data = {m['id']: [] for m in modules}

    pairs = (
        [(p, 'xml')      for p in sorted(XML_SRC.glob('*.txt')) if p.name not in SKIP] +
        [(p, 'markdown') for p in sorted(MD_SRC.glob('*.txt'))  if p.name not in SKIP]
    )

    for fpath, fmt in pairs:
        content = fpath.read_text(encoding='utf-8', errors='ignore')
        tool    = fpath.stem

        for mod in modules:
            mid    = mod['id']
            result = detect_module(content, mod, fmt)
            if result:
                data[mid].append({
                    'tool':     tool,
                    'fmt':      fmt,
                    'matched':  result['matched'],
                    'excerpts': result['excerpts'],
                    'via':      result['via'],
                })

    return data


# ── render one module file ────────────────────────────────────────────────────

MODULE_INDEX = {
    'identity':       '01',
    'behavior':       '02',
    'tools':          '03',
    'output_format':  '04',
    'constraints':    '05',
    'environment':    '06',
    'examples':       '07',
    'task_management':'08',
}

def render_module(mod: dict, entries: list, total_files: int) -> str:
    substantive = [e for e in entries if e['excerpts']]
    fallback    = [e for e in entries if not e['excerpts']]

    lines = [
        f"# {mod['name_zh']} / {mod['name_en']}",
        f"",
        f"> **层级**: `{mod['tier']}`  |  "
        f"**覆盖**: {len(substantive)}/{total_files} 文件有结构化内容，"
        f"{len(fallback)} 个仅 fallback 命中",
        f"",
        "---",
        "",
        "## 覆盖情况",
        "",
        "| 文件 | 格式 | 匹配方式 | 匹配到的标签/标题 |",
        "|---|---|---|---|",
    ]

    for e in entries:
        icon  = "✓" if e['excerpts'] else "~"
        via   = e['via']
        tags  = ", ".join(f"`{t}`" for t in e['matched'])
        lines.append(f"| {icon} {e['tool']} | {e['fmt']} | {via} | {tags} |")

    lines += ["", "---", "", "## 提取内容", ""]

    for e in substantive:
        lines.append(f"### {e['tool']}  `{e['fmt']}`")
        lines.append(f"")
        lines.append(f"匹配: `{'`, `'.join(e['matched'])}`")
        lines.append(f"")
        for i, excerpt in enumerate(e['excerpts'], 1):
            body = excerpt
            if len(body) > 3000:
                body = body[:3000] + '\n... [truncated]'
            if len(e['excerpts']) > 1:
                lines.append(f"**[{i}]**")
            lines += ["```", body, "```", ""]

    if fallback:
        lines += ["---", "", "## Fallback 命中（无结构化内容）", ""]
        for e in fallback:
            lines.append(f"- **{e['tool']}** `{e['fmt']}` → `{e['matched'][0]}`")
        lines.append("")

    return '\n'.join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    modules    = json.loads(CONFIG.read_text())['modules']
    total      = sum(1 for _ in XML_SRC.glob('*.txt') if _.name not in SKIP) + \
                 sum(1 for _ in MD_SRC.glob('*.txt')  if _.name not in SKIP)
    data       = collect(modules)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*52}")
    print(f"  Phase 2 – By-Module  ({total} source files)")
    print(f"{'='*52}\n")

    for mod in modules:
        mid      = mod['id']
        idx      = MODULE_INDEX[mid]
        entries  = data[mid]
        content  = render_module(mod, entries, total)
        fname    = f"{idx}-{mid}.md"
        (OUT_DIR / fname).write_text(content, encoding='utf-8')

        substantive = sum(1 for e in entries if e['excerpts'])
        print(f"  {fname:<30}  {substantive}/{total} files")

    print(f"\nOutput → {OUT_DIR}")


if __name__ == '__main__':
    main()
