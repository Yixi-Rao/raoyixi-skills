---
name: drawio
description: Create editable draw.io diagrams as .drawio files and optionally export them to PNG, SVG, PDF, or JPG. Use when the user asks for draw.io, diagrams.net, mxGraph, .drawio files, architecture diagrams, flowcharts, sequence-style diagrams, ER diagrams, process maps, or editable diagram exports.
---

# Draw.io

Create native editable draw.io diagrams. Prefer `.drawio` output unless the user asks for PNG, SVG, PDF, or JPG.

## Bundled Resources

Load these only when needed:

- `references/diagram-types.md`: Use when the request names ERD, UML class, sequence, architecture, ML/deep-learning, or flowchart diagrams; it contains shape, edge, and layout presets.
- `references/style-presets.md`: Use when the user asks to learn, save, list, set, delete, or apply a diagram style preset.
- `references/style-extraction.md`: Use only from the style preset learn flow.
- `references/troubleshooting.md`: Use when export, rendering, vision review, or draw.io CLI behavior fails.
- `scripts/repair_png.py`: Used by `drawio_tool.py` after embedded PNG export to repair draw.io CLI's truncated IEND issue.
- `scripts/encode_drawio_url.py`: Use when draw.io CLI is unavailable and the user needs a browser fallback URL for opening the editable diagram in diagrams.net.

## Workflow

1. Decide the diagram type and output format from the request.
2. If a specific diagram type is named, consult `references/diagram-types.md` for the structural preset.
3. If a named/default style preset is requested, consult `references/style-presets.md` before choosing colors, fonts, shapes, or edge styles.
4. Generate valid draw.io XML in `mxGraphModel` format.
5. Write the XML to a temporary `.xml` or `.drawio` file using `apply_patch`.
6. Run `scripts/drawio_tool.py` to validate XML, write the final `.drawio`, and optionally export.
7. If export succeeds, keep the `.drawio` source unless the user explicitly wants only the exported file.
8. Return the absolute output path and mention if export was skipped because draw.io CLI is unavailable.

Use descriptive lowercase hyphenated filenames, for example `login-flow.drawio` or `moe-rl-training-architecture.drawio.svg`.

## Script

Run the bundled helper from the skill directory:

```bash
python3 /Users/raoyixi/.codex/skills/drawio/scripts/drawio_tool.py \
  --input /absolute/path/source.xml \
  --output /absolute/path/name.drawio
```

Export examples:

```bash
python3 /Users/raoyixi/.codex/skills/drawio/scripts/drawio_tool.py \
  --input /absolute/path/source.xml \
  --output /absolute/path/name.drawio \
  --export svg
```

```bash
python3 /Users/raoyixi/.codex/skills/drawio/scripts/drawio_tool.py \
  --input /absolute/path/source.xml \
  --output /absolute/path/name.drawio \
  --export png --transparent --scale 2
```

The script:

- Validates XML well-formedness.
- Accepts either `<mxGraphModel>` or `<mxfile>` roots.
- Writes a final `.drawio` file. When the input root is `<mxGraphModel>`, it wraps it in a standard `<mxfile><diagram>...</diagram></mxfile>` container for better diagrams.net compatibility.
- Locates `drawio` on `PATH` or `/Applications/draw.io.app/Contents/MacOS/draw.io`.
- Exports with embedded XML for PNG, SVG, and PDF.
- Repairs embedded PNG exports automatically when `scripts/repair_png.py` is present.
- Keeps the `.drawio` source after export by default; pass `--delete-source` only when the user asks for an export-only deliverable.

If export is requested but draw.io CLI is unavailable, still create the `.drawio` file. To give the user a browser fallback, run:

```bash
python3 /Users/raoyixi/.codex/skills/drawio/scripts/encode_drawio_url.py \
  /absolute/path/name.drawio
```

The URL encodes the diagram in the fragment and opens in diagrams.net.

## Style Presets

Support these user operations using `references/style-presets.md`:

- "learn my style from `<path>` as `<name>`"
- "list my styles"
- "show my `<name>` style"
- "make `<name>` the default"
- "remove default"
- "delete `<name>`"
- "rename `<a>` to `<b>`"

Look up user presets in `~/.drawio-skill/styles/<name>.json`. Built-in presets are optional; do not invent one if no file exists. If a requested preset is missing, list available presets and stop instead of silently falling back.

## XML Basics

Every generated `mxGraphModel` must include:

```xml
<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
  </root>
</mxGraphModel>
```

Add all vertices and edges under `parent="1"`.

Common vertex:

```xml
<mxCell id="node-1" value="Label" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="80" y="80" width="180" height="70" as="geometry"/>
</mxCell>
```

Common edge:

```xml
<mxCell id="edge-1" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="node-1" target="node-2">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

Decision diamond:

```xml
<mxCell id="decision-1" value="Condition?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
  <mxGeometry x="320" y="80" width="150" height="90" as="geometry"/>
</mxCell>
```

Database:

```xml
<mxCell id="db-1" value="Database" style="shape=cylinder3;whiteSpace=wrap;boundedLbl=1;backgroundOutline=1;size=15;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;" vertex="1" parent="1">
  <mxGeometry x="560" y="80" width="160" height="80" as="geometry"/>
</mxCell>
```

## Rules

- Escape attribute text: `&amp;`, `&lt;`, `&gt;`, `&quot;`.
- Use `html=1;` whenever a label contains HTML tags such as `&lt;br&gt;` or `&lt;b&gt;`.
- Do not put `--` inside XML comments.
- Use stable unique IDs for every `mxCell`.
- Prefer orthogonal connectors for flowcharts and architecture diagrams.
- Keep labels short enough to fit; use `<br>` line breaks for dense labels.
- Use a restrained palette and consistent dimensions across related nodes.
- For exported PNG/SVG/PDF that should remain editable in draw.io, rely on the script export path; it passes embedded-diagram flags where supported.

## Output Format

- `.drawio`: default and always editable.
- `.drawio.png`: portable bitmap with embedded diagram XML.
- `.drawio.svg`: scalable export with embedded diagram XML.
- `.drawio.pdf`: printable export with embedded diagram XML.
- `.drawio.jpg`: lossy export; no embedded XML support.

If the draw.io CLI is missing, still deliver the `.drawio` file and explain that export requires installing the draw.io desktop app or putting `drawio` on `PATH`.
