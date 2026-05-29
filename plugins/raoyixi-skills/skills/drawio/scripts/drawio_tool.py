#!/usr/bin/env python3
"""Validate/write draw.io files and optionally export with the draw.io CLI."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from xml.etree import ElementTree as ET


DRAWIO_MAC = Path("/Applications/draw.io.app/Contents/MacOS/draw.io")


SAMPLE = """<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1000" pageHeight="600" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="start" value="Start" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="80" y="80" width="140" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="step" value="Build diagram" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="300" y="80" width="160" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="end" value="Done" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="540" y="80" width="140" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="edge-1" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="start" target="step">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="edge-2" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="step" target="end">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Input XML/.drawio file")
    source.add_argument("--sample-flowchart", action="store_true", help="Create a small sample flowchart")
    parser.add_argument("--output", type=Path, required=True, help="Output .drawio path")
    parser.add_argument("--export", choices=["png", "svg", "pdf", "jpg"], help="Optional export format")
    parser.add_argument("--transparent", action="store_true", help="Transparent PNG background")
    parser.add_argument("--scale", type=float, help="Export scale")
    parser.add_argument("--border", type=int, default=10, help="Export border width")
    parser.add_argument("--keep-source", action="store_true", help="Deprecated compatibility flag; source is kept by default")
    parser.add_argument("--delete-source", action="store_true", help="Delete .drawio after a successful export")
    parser.add_argument("--raw-mxgraphmodel", action="store_true", help="Write raw mxGraphModel instead of wrapping it in mxfile")
    parser.add_argument("--open", action="store_true", help="Open final output on macOS")
    return parser.parse_args()


def load_xml(args: argparse.Namespace) -> str:
    if args.sample_flowchart:
        return SAMPLE
    return args.input.read_text(encoding="utf-8")


def validate_xml(text: str) -> ET.Element:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise SystemExit(f"XML parse error: {exc}") from exc
    if root.tag not in {"mxGraphModel", "mxfile"}:
        raise SystemExit(f"Unsupported root <{root.tag}>. Expected <mxGraphModel> or <mxfile>.")
    if root.tag == "mxGraphModel":
        cells = root.findall("./root/mxCell")
        ids = [cell.attrib.get("id") for cell in cells]
        if "0" not in ids or "1" not in ids:
            raise SystemExit("mxGraphModel must contain mxCell id=\"0\" and id=\"1\".")
        duplicates = sorted({cell_id for cell_id in ids if cell_id and ids.count(cell_id) > 1})
        if duplicates:
            raise SystemExit(f"Duplicate mxCell ids: {', '.join(duplicates)}")
    return root


def as_drawio_file(text: str, root: ET.Element, raw: bool = False) -> str:
    if root.tag == "mxfile" or raw:
        return text
    diagram_id = uuid.uuid4().hex[:20]
    return (
        '<mxfile host="app.diagrams.net" modified="2026-05-18T00:00:00.000Z" '
        'agent="Codex drawio skill" version="24.7.17" type="device">\n'
        f'  <diagram id="{diagram_id}" name="Page-1">\n'
        f'{text}\n'
        "  </diagram>\n"
        "</mxfile>\n"
    )


def find_drawio() -> str | None:
    found = shutil.which("drawio")
    if found:
        return found
    if DRAWIO_MAC.exists():
        return str(DRAWIO_MAC)
    return None


def export_file(drawio: Path, fmt: str, args: argparse.Namespace) -> Path:
    cli = find_drawio()
    if not cli:
        raise SystemExit("draw.io CLI not found. Install draw.io desktop or put drawio on PATH.")
    out = drawio.with_suffix(drawio.suffix + f".{fmt}")
    cmd = [cli, "-x", "-f", fmt, "-b", str(args.border), "-o", str(out), str(drawio)]
    if fmt in {"png", "svg", "pdf"}:
        cmd.insert(3, "-e")
    if fmt == "png" and args.transparent:
        cmd.insert(3, "-t")
    if args.scale:
        cmd[3:3] = ["-s", str(args.scale)]
    subprocess.run(cmd, check=True)
    if fmt == "png":
        repair_script = Path(__file__).with_name("repair_png.py")
        if repair_script.exists():
            subprocess.run([sys.executable, str(repair_script), str(out)], check=True)
    return out


def open_path(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)


def main() -> int:
    args = parse_args()
    xml_text = load_xml(args)
    root = validate_xml(xml_text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(as_drawio_file(xml_text, root, args.raw_mxgraphmodel), encoding="utf-8")
    print(f"wrote {args.output}")

    final = args.output
    if args.export:
        final = export_file(args.output, args.export, args)
        print(f"exported {final}")
        if args.delete_source and not args.keep_source:
            args.output.unlink()
            print(f"removed {args.output}")

    if args.open:
        open_path(final)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
