from __future__ import annotations

import json

import click

import afterpython as ap
from afterpython._io.yaml import read_yaml

build_path = ap.paths.build_path


def build_faq_json():
    """Build faq.json from the user's afterpython/faq.yml.

    Output shape: a flat list of {question, answer, category}. `category` is
    always present — empty string when unset — so the frontend can rely on a
    uniform item shape. Order is preserved so the frontend can derive category
    order from first appearance.
    """
    faq_yml_path = ap.paths.afterpython_path / "faq.yml"

    if not faq_yml_path.exists():
        click.echo("No faq.yml found, skip building faq.json")
        return

    raw = read_yaml(faq_yml_path)
    if raw is None:
        click.echo("faq.yml is empty, skip building faq.json")
        return

    click.echo("Building faq.json...")

    items = [
        {
            "question": str(item["question"]),
            "answer": str(item["answer"]),
            "category": str(item["category"]) if item.get("category") else "",
        }
        for item in raw
    ]

    with open(build_path / "faq.json", "w") as f:
        json.dump(items, f, indent=2)
