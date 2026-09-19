from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def test_all_templates_parse():
    root = Path(__file__).resolve().parents[1] / "app" / "templates"
    env = Environment(loader=FileSystemLoader(root))
    for path in root.rglob("*.html"):
        env.get_template(str(path.relative_to(root)))
