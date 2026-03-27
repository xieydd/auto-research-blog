#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def load_results(results_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    iterations: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for raw_line in results_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("event"):
            events.append(row)
        else:
            iterations.append(row)
    return iterations, events


def scale_x(index: int, count: int, left: float, right: float) -> float:
    if count <= 1:
        return (left + right) / 2
    return left + (right - left) * (index / (count - 1))


def scale_y(
    score: float,
    chart_top: float,
    chart_bottom: float,
    axis_min: float,
    axis_max: float,
) -> float:
    clamped = max(axis_min, min(axis_max, score))
    if axis_max <= axis_min:
        return (chart_top + chart_bottom) / 2
    return chart_bottom - (((clamped - axis_min) / (axis_max - axis_min)) * (chart_bottom - chart_top))


def compute_axis_bounds(iterations: list[dict[str, Any]], target_score: float) -> tuple[float, float, float]:
    scores = [float(row["overall_score"]) for row in iterations]
    if not scores:
        return 0.0, 100.0, 10.0

    relevant = scores + [target_score]
    min_score = min(relevant)
    max_score = max(relevant)
    span = max_score - min_score

    # Keep the chart tight around the data, similar to autoresearch's progress plot.
    padding = max(span * 0.18, 1.0)
    axis_min = max(0.0, math.floor((min_score - padding) * 2) / 2)
    axis_max = min(100.0, math.ceil((max_score + padding) * 2) / 2)

    if axis_max - axis_min < 6.0:
        midpoint = (axis_max + axis_min) / 2
        axis_min = max(0.0, midpoint - 3.0)
        axis_max = min(100.0, midpoint + 3.0)

    desired_ticks = 6
    rough_step = (axis_max - axis_min) / desired_ticks
    candidate_steps = [0.5, 1.0, 2.0, 2.5, 5.0, 10.0]
    tick_step = min(candidate_steps, key=lambda step: abs(step - rough_step))
    axis_min = math.floor(axis_min / tick_step) * tick_step
    axis_max = math.ceil(axis_max / tick_step) * tick_step
    axis_min = max(0.0, axis_min)
    axis_max = min(100.0, axis_max)

    return axis_min, axis_max, tick_step


def color_for_verdict(verdict: str) -> str:
    if verdict == "keep":
        return "#0f766e"
    if verdict == "discard":
        return "#b91c1c"
    if verdict == "baseline":
        return "#475569"
    return "#334155"


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_svg(
    experiment_id: str,
    iterations: list[dict[str, Any]],
    events: list[dict[str, Any]],
    target_score: float,
) -> str:
    width = 1600
    height = 900
    left = 110
    right = width - 60
    top = 110
    bottom = height - 110
    chart_width = right - left
    chart_height = bottom - top

    keep_rows = [row for row in iterations if row["verdict"] == "keep"]
    discard_rows = [row for row in iterations if row["verdict"] == "discard"]
    baseline_rows = [row for row in iterations if row["verdict"] == "baseline"]
    iteration_rows = [row for row in iterations if row["verdict"] != "baseline"]
    best_score = max((float(row["overall_score"]) for row in keep_rows), default=0.0)
    latest_score = float(iterations[-1]["overall_score"]) if iterations else 0.0
    axis_min, axis_max, tick_step = compute_axis_bounds(iterations, target_score)
    title_prefix = f"Autoresearch-Blog Progress: {len(iteration_rows)} Iterations"
    if baseline_rows:
        title_prefix += " + Baseline"

    header = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc" />',
        f'<text x="{width / 2:.0f}" y="42" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="700" fill="#0f172a">{title_prefix}, {len(keep_rows)} Kept Improvements</text>',
        f'<text x="{width / 2:.0f}" y="72" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="15" fill="#475569">Experiment {escape_xml(experiment_id)} · target {target_score:.1f}/100 · best {best_score:.1f}</text>',
        f'<text x="{width / 2:.0f}" y="96" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#64748b">latest {latest_score:.1f} · keeps {len(keep_rows)} · discards {len(discard_rows)}</text>',
    ]

    parts = header

    # Grid and score labels
    tick = axis_min
    tick_values: list[float] = []
    while tick <= axis_max + 1e-9:
        tick_values.append(round(tick, 3))
        tick += tick_step
    for score in tick_values:
        y = scale_y(score, top, bottom, axis_min, axis_max)
        midpoint = (axis_min + axis_max) / 2
        stroke = "#dbe3ea" if score in (axis_min, midpoint, axis_max) else "#edf2f7"
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" stroke="{stroke}" stroke-width="1" />'
        )
        parts.append(
            f'<text x="{left - 18}" y="{y + 5:.2f}" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#64748b">{score:.1f}</text>'
        )

    # Vertical grid / x ticks
    points: list[tuple[float, float, dict[str, Any]]] = []
    for idx, row in enumerate(iterations):
        iteration_no = int(row["iteration"])
        x = scale_x(idx, len(iterations), left, right)
        y = scale_y(float(row["overall_score"]), top, bottom, axis_min, axis_max)
        points.append((x, y, row))
        parts.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{bottom}" stroke="#edf2f7" stroke-width="1" />'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{bottom + 24}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#64748b">{iteration_no}</text>'
        )

    # Target line
    target_y = scale_y(target_score, top, bottom, axis_min, axis_max)
    parts.append(
        f'<line x1="{left}" y1="{target_y:.2f}" x2="{right}" y2="{target_y:.2f}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="8 8" />'
    )
    parts.append(
        f'<text x="{right}" y="{target_y - 10:.2f}" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="600" fill="#b45309">target {target_score:.1f}</text>'
    )

    # Target change events
    event_rows = [row for row in events if row.get("event") == "target-change"]
    event_offset = {}
    for idx, row in enumerate(iterations):
        event_offset[int(row["iteration"])] = idx
    for event in event_rows:
        target_change_index = len(points) - 0.5
        for idx, (_, _, row) in enumerate(points):
            if float(row["target_score_percent"]) == float(event["to_target_score_percent"]):
                target_change_index = idx - 0.5
                break
        x = left if not points else left + (chart_width * max(0.0, target_change_index) / max(1, len(points) - 1))
        parts.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{bottom}" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 6" />'
        )
        parts.append(
            f'<text x="{x + 6:.2f}" y="{top + 18}" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#64748b">target → {float(event["to_target_score_percent"]):.0f}</text>'
        )

    # Running best step line
    step_points: list[tuple[float, float]] = []
    running_best = None
    last_x = None
    for x, y, row in points:
        score = float(row["overall_score"])
        if running_best is None:
            running_best = score
            step_points.append((x, scale_y(running_best, top, bottom, axis_min, axis_max)))
        else:
            if last_x is not None:
                step_points.append((x, scale_y(running_best, top, bottom, axis_min, axis_max)))
            if score >= running_best and row["verdict"] != "discard":
                running_best = score
                step_points.append((x, scale_y(running_best, top, bottom, axis_min, axis_max)))
        last_x = x
    if step_points:
        path_parts: list[str] = []
        for idx, (x, y) in enumerate(step_points):
            path_parts.append(("M" if idx == 0 else "L") + f" {x:.2f} {y:.2f}")
        parts.append(
            f'<path d="{" ".join(path_parts)}" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />'
        )

    # Discard points first
    for x, y, row in points:
        verdict = row["verdict"]
        if verdict == "discard":
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#94a3b8" opacity="0.45" />')

    # Baseline / keep points and annotations
    for x, y, row in points:
        verdict = row["verdict"]
        if verdict not in {"baseline", "keep"}:
            continue
        color = color_for_verdict(verdict)
        radius = 7 if verdict == "keep" else 6
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="{color}" stroke="#ffffff" stroke-width="1" />')
        label = "Baseline" if verdict == "baseline" else None
        if verdict == "keep":
            diff_summary = row.get("diff_summary") or []
            if diff_summary:
                label = str(diff_summary[0])
        if label:
            truncated = escape_xml(label[:46] + ("..." if len(label) > 46 else ""))
            parts.append(
                f'<text x="{x + 6:.2f}" y="{y - 8:.2f}" transform="rotate(-28 {x + 6:.2f} {y - 8:.2f})" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#16a34a">{truncated}</text>'
            )

    # Legend
    legend_y = height - 38
    legend_items = [
        ("Discarded", "#94a3b8"),
        ("Kept", "#16a34a"),
        ("Running best", "#22c55e"),
        ("Target", "#f59e0b"),
    ]
    legend_x = left
    for label, color in legend_items:
        if label == "Target":
            parts.append(
                f'<line x1="{legend_x}" y1="{legend_y - 5}" x2="{legend_x + 24}" y2="{legend_y - 5}" stroke="{color}" stroke-width="2" stroke-dasharray="8 8" />'
            )
        elif label == "Running best":
            parts.append(
                f'<line x1="{legend_x}" y1="{legend_y - 5}" x2="{legend_x + 24}" y2="{legend_y - 5}" stroke="{color}" stroke-width="2.5" />'
            )
        else:
            opacity = "0.45" if label == "Discarded" else "1"
            parts.append(f'<circle cx="{legend_x + 10}" cy="{legend_y - 5}" r="5" fill="{color}" opacity="{opacity}" />')
        parts.append(
            f'<text x="{legend_x + 34}" y="{legend_y}" font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#334155">{label}</text>'
        )
        legend_x += 150

    # Axis labels
    parts.append(
        f'<text x="{left - 72}" y="{(top + bottom) / 2:.0f}" transform="rotate(-90 {left - 72} {(top + bottom) / 2:.0f})" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="15" fill="#334155">Judge Score (higher is better)</text>'
    )
    parts.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 18}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="15" fill="#334155">Iteration #</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def infer_target(iterations: list[dict[str, Any]], events: list[dict[str, Any]]) -> float:
    if iterations:
        return float(iterations[-1]["target_score_percent"])
    for event in reversed(events):
        if event.get("event") == "target-change":
            return float(event["to_target_score_percent"])
    return 100.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Render autoresearch-blog progress chart as SVG.")
    parser.add_argument("experiment_dir", help="Path to the experiment directory")
    parser.add_argument(
        "--output",
        help="Output SVG path. Defaults to <experiment_dir>/progress.svg",
    )
    args = parser.parse_args()

    experiment_dir = Path(args.experiment_dir).resolve()
    results_path = experiment_dir / "results.jsonl"
    if not results_path.exists():
        raise SystemExit(f"results.jsonl not found: {results_path}")

    iterations, events = load_results(results_path)
    target_score = infer_target(iterations, events)
    svg = build_svg(experiment_dir.name, iterations, events, target_score)

    output_path = Path(args.output).resolve() if args.output else experiment_dir / "progress.svg"
    output_path.write_text(svg, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
