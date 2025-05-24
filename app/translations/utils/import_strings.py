"""
Description: Imports all translations from the json file to the .po files
"""

import json
from io import StringIO
from babel.messages.pofile import read_po, write_po
from babel.messages.catalog import Catalog
from pathlib import Path
from app import create_app
from app.utils.localization import babel


def import_strings(filename=None, source="en", target=None):
    """Import translation strings from JSON format."""
    translations_dir = Path(__file__).parent / "app/translations"

    if filename:
        from_tron = json.loads(open(filename, "r", encoding="utf-8").read())
    else:
        from_tron = json.loads(
            open(
                translations_dir / "utils" / "strings.json", "r", encoding="utf-8"
            ).read()
        )

    template_path = translations_dir / "utils" / "messages.pot"
    template_str = StringIO(open(template_path, "r", encoding="utf-8").read())
    template = read_po(template_str)

    if not target:
        for locale in babel.list_translations():
            locale = locale.language
            new_catalog = Catalog()
            for id in from_tron:
                if locale in from_tron[id].keys():
                    new_catalog.add(id, from_tron[id][locale])
            new_catalog.update(template)
            write_po(
                open(
                    translations_dir / locale / "LC_MESSAGES/messages.po",
                    "wb",
                ),
                new_catalog,
            )
    else:
        new_catalog = Catalog()
        for id in from_tron:
            if target in from_tron[id].keys():
                new_catalog.add(id, from_tron[id][target])
        new_catalog.update(template)
        write_po(
            open(translations_dir / target / "LC_MESSAGES/messages.po", "wb"),
            new_catalog,
        )


if __name__ == "__main__":
    app, _ = create_app()

    with app.app_context():
        import_strings(target="en")
        print("Import succeeded!")
