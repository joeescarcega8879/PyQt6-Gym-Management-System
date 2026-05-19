"""
Generates dark theme CSS variants from the base styles.css.
Each theme replaces only the accent color tokens.

Usage:
    python scripts/generate_themes.py
"""
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
BASE_CSS = (ROOT / "src" / "assets" / "styles.css").read_text(encoding="utf-8")
THEMES_DIR = ROOT / "src" / "assets" / "themes"
THEMES_DIR.mkdir(exist_ok=True)

# Blue accent shades (source — the default theme)
BLUE_ACCENT  = "#2196F3"
BLUE_HOVER   = "#1E88E5"
BLUE_DARK    = "#1976D2"
BLUE_DARKER  = "#1565C0"

# Each entry: (key, display_name, accent, hover, dark, darker)
THEMES = [
    ("dark_blue",   "Dark Blue",   "#2196F3", "#1E88E5", "#1976D2", "#1565C0"),
    ("dark_green",  "Dark Green",  "#4CAF50", "#43A047", "#388E3C", "#2E7D32"),
    ("dark_purple", "Dark Purple", "#9C27B0", "#8E24AA", "#7B1FA2", "#6A1B9A"),
    ("dark_orange", "Dark Orange", "#FF9800", "#FB8C00", "#F57C00", "#E65100"),
    ("dark_cyan",   "Dark Cyan",   "#00BCD4", "#00ACC1", "#0097A7", "#00838F"),
]

for key, name, accent, hover, dark, darker in THEMES:
    css = BASE_CSS

    # Replace accent shades — most specific first to avoid partial replacements
    css = css.replace(BLUE_DARKER, darker)
    css = css.replace(BLUE_DARK,   dark)
    css = css.replace(BLUE_HOVER,  hover)
    css = css.replace(BLUE_ACCENT, accent)

    # badge-info is semantically cyan (#00BCD4) in all themes — restore it
    # only if the accent itself isn't cyan (dark_cyan keeps it as-is)
    if key != "dark_cyan":
        css = css.replace(
            "background-color: " + accent + ";\n}\n\nQLabel[class=\"badge-success\"]",
            "background-color: #00BCD4;\n}\n\nQLabel[class=\"badge-success\"]",
        )

    # Update header comment to reflect the current accent
    short_name = name.replace("Dark ", "")
    css = css.replace(
        " * - Primary:   #2196F3 (Blue)",
        f" * - Primary:   {accent} ({short_name})",
    )

    out = THEMES_DIR / f"{key}.css"
    out.write_text(css, encoding="utf-8")
    print(f"  Generated {key}.css  accent={accent}")

print(f"\n{len(THEMES)} theme files written to {THEMES_DIR}")
