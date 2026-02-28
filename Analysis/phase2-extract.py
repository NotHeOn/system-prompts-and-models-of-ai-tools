#!/usr/bin/env python3
"""
Phase 2 Extraction Script
-------------------------
Input  : 21 structured files (xml/system-prompt × 10, markdown/system-prompt × 11)
Config : module-detection-config.json  (8 modules, tags / heading keywords / fallback regex)
Output :
  phase2-content/detected/  — files with >= THRESHOLD modules substantively extracted
  phase2-content/others/    — files that fell below the threshold
"""

import json
import re
from pathlib import Path

BASE      = Path(__file__).parent.parent
ANALYSIS  = BASE / "Analysis"
CONFIG    = ANALYSIS / "module-detection-config.json"
OUT_BASE  = ANALYSIS / "phase2-content"
DETECTED  = OUT_BASE / "detected"
OTHERS    = OUT_BASE / "others"
XML_SRC   = ANALYSIS / "format-classification" / "xml"  / "system-prompt"
MD_SRC    = ANALYSIS / "format-classification" / "markdown" / "system-prompt"

# A file goes to detected/ only if at least this many modules have real extracted text
THRESHOLD = 2


# ── helpers ──────────────────────────────────────────────────────────────────

def extract_xml_tag(content: str, tag: str) -> list[str]:
    pat = rf'<{re.escape(tag)}[^>]*>([\s\S]*?)</{re.escape(tag)}>'
    return [m.strip() for m in re.findall(pat, content, re.IGNORECASE)]


def extract_markdown_section(content: str, keyword: str) -> list[str]:
    """Return full text of any heading section whose title contains `keyword`."""
    lines   = content.split('\n')
    results = []
    i = 0
    while i < len(lines):
        m = re.match(r'^(#{1,4})\s+(.+)', lines[i])
        if m and keyword.lower() in lines[i].lower():
            level        = len(m.group(1))
            section      = [lines[i]]
            i += 1
            while i < len(lines):
                nm = re.match(r'^(#{1,4})\s+', lines[i])
                if nm and len(nm.group(1)) <= level:
                    break
                section.append(lines[i])
                i += 1
            text = '\n'.join(section).strip()
            if len(text) > len(section[0]):   # more than just the heading line
                results.append(text)
        else:
            i += 1
    return results


# ── per-format processing ─────────────────────────────────────────────────────

def process_xml(filepath: Path, modules: list) -> dict:
    content = filepath.read_text(encoding='utf-8', errors='ignore')
    result  = {}

    for mod in modules:
        mid      = mod['id']
        excerpts = []
        matched  = []

        for tag in mod['detection']['xml']['tags']:
            hits = extract_xml_tag(content, tag)
            if hits:
                matched.append(tag)
                excerpts += [{'tag': tag, 'content': h} for h in hits]

        if excerpts:
            result[mid] = {'match_type': 'tag', 'matched': matched, 'excerpts': excerpts}
            continue

        # fallback regex
        for pat in mod['detection']['fallback']['patterns']:
            if re.search(pat, content):
                result[mid] = {'match_type': 'fallback', 'matched': [pat], 'excerpts': []}
                break

    return result


def process_markdown(filepath: Path, modules: list) -> dict:
    content = filepath.read_text(encoding='utf-8', errors='ignore')
    result  = {}

    for mod in modules:
        mid      = mod['id']
        excerpts = []
        matched  = []

        for kw in mod['detection']['markdown']['keywords']:
            hits = extract_markdown_section(content, kw)
            if hits:
                matched.append(kw)
                excerpts += [{'heading': kw, 'content': h} for h in hits]

        if excerpts:
            result[mid] = {'match_type': 'heading', 'matched': matched, 'excerpts': excerpts}
            continue

        # fallback regex
        for pat in mod['detection']['fallback']['patterns']:
            if re.search(pat, content, re.MULTILINE):
                result[mid] = {'match_type': 'fallback', 'matched': [pat], 'excerpts': []}
                break

    return result


# ── render ────────────────────────────────────────────────────────────────────

def render(filepath: Path, fmt: str, detection: dict, modules: list) -> str:
    substantive = sum(1 for v in detection.values() if v.get('excerpts'))
    lines = [
        f"# {filepath.name}",
        f"",
        f"- **Format**: {fmt.upper()}",
        f"- **Modules with extracted content**: {substantive}/{len(modules)}",
        f"",
        "---",
        "",
    ]

    for mod in modules:
        mid     = mod['id']
        label   = f"{mod['name_zh']} / {mod['name_en']}  `{mod['tier']}`"
        info    = detection.get(mid)

        lines.append(f"## {label}")
        lines.append("")

        if not info:
            lines.append("_未检测到_")
        elif not info['excerpts']:
            lines.append(f"**匹配方式**: fallback regex")
            lines.append(f"**pattern**: `{info['matched'][0]}`")
            lines.append(f"_(fallback 命中，但无结构化内容可提取)_")
        else:
            lines.append(f"**匹配方式**: {info['match_type']} → `{'`, `'.join(info['matched'])}`")
            lines.append("")
            for exc in info['excerpts']:
                key  = exc.get('tag') or exc.get('heading', '')
                body = exc['content']
                if len(body) > 3000:
                    body = body[:3000] + '\n... [truncated]'
                lines += [f"<!-- {key} -->", "```", body, "```", ""]

        lines.append("")

    return '\n'.join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    modules = json.loads(CONFIG.read_text())['modules']
    DETECTED.mkdir(parents=True, exist_ok=True)
    OTHERS.mkdir(parents=True, exist_ok=True)

    stats = {'detected': [], 'others': []}

    pairs = (
        [(p, 'xml')      for p in sorted(XML_SRC.glob('*.txt'))] +
        [(p, 'markdown') for p in sorted(MD_SRC.glob('*.txt'))]
    )

    for fpath, fmt in pairs:
        detection   = process_xml(fpath, modules) if fmt == 'xml' else process_markdown(fpath, modules)
        substantive = sum(1 for v in detection.values() if v.get('excerpts'))
        output      = render(fpath, fmt, detection, modules)
        out_name    = fpath.stem + '.md'

        if substantive >= THRESHOLD:
            (DETECTED / out_name).write_text(output, encoding='utf-8')
            stats['detected'].append((fpath.name, substantive))
        else:
            (OTHERS / out_name).write_text(output, encoding='utf-8')
            stats['others'].append((fpath.name, substantive))

    print(f"\n{'='*50}")
    print(f"  Phase 2 Extraction  (threshold = {THRESHOLD} modules)")
    print(f"{'='*50}")
    print(f"\ndetected/  ({len(stats['detected'])} files)")
    for name, n in stats['detected']:
        print(f"  ✓  [{n}/8]  {name}")
    print(f"\nothers/  ({len(stats['others'])} files)")
    for name, n in stats['others']:
        print(f"  ✗  [{n}/8]  {name}")


if __name__ == '__main__':
    main()
