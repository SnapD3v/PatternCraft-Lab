"""
Description: Exports all translations into one json file
"""

import json
from io import StringIO
from babel.messages.pofile import read_po
from pathlib import Path
from app import create_app
from app.utils.localization import babel


def export_strings(source="en", target=None):
    """Export translation strings to JSON format."""
    # Get the absolute path to translations directory
    translations_dir = Path(__file__).parent / "app/translations"

    source_str = StringIO(
        open(
            translations_dir / source / "LC_MESSAGES/messages.po",
            "r",
            encoding="utf-8",
        ).read()
    )
    source_catalog = read_po(source_str)
    for_tron = {
        message.id: {source: message.string} for message in source_catalog if message.id
    }

    if not target:
        for locale in babel.list_translations():
            locale = locale.language
            if locale != source:
                target_str = StringIO(
                    open(
                        translations_dir / locale / "LC_MESSAGES/messages.po",
                        "r",
                        encoding="utf-8",
                    ).read()
                )
                target_catalog = read_po(target_str)

                for message in target_catalog:
                    if message.id and message.id in for_tron.keys():
                        for_tron[message.id][locale] = message.string
    else:
        target_str = StringIO(
            open(
                translations_dir / target / "LC_MESSAGES/messages.po",
                "r",
                encoding="utf-8",
            ).read()
        )
        target_catalog = read_po(target_str)

        for message in target_catalog:
            if message.id and message.id in for_tron.keys():
                for_tron[message.id][target] = message.string

    # Save JSON in translations directory
    output_path = translations_dir / "utils" / "strings.json"
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(for_tron, outfile, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    app, _ = create_app()

    with app.app_context():
        export_strings(source="ru")
        print("Extraction succeeded!")
