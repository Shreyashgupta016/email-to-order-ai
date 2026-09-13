"""
catalog.py — the product list.

In a real client project this is pulled from their ERP (product master data)
once a day. Here it's a plain Python list so the demo runs with no setup.

Each product:
  code    -> the article/SKU number the ERP needs
  name    -> official product name
  aliases -> how customers actually write it in emails
  unit    -> how it's sold
  price   -> EUR per unit
"""

CATALOG = [
    {
        "code": "ART-90432",
        "name": "Hex bolt M8 x 40mm, zinc-plated (box of 100)",
        "aliases": ["m8 bolts", "m8 hex bolts", "8mm bolts", "m8x40"],
        "unit": "box",
        "price": 12.50,
    },
    {
        "code": "ART-90433",
        "name": "Hex bolt M10 x 50mm, zinc-plated (box of 100)",
        "aliases": ["m10 bolts", "m10 hex bolts", "10mm bolts", "m10x50"],
        "unit": "box",
        "price": 15.00,
    },
    {
        "code": "ART-90510",
        "name": "Hex nut M8, zinc-plated (box of 200)",
        "aliases": ["m8 nuts", "8mm nuts", "nuts m8"],
        "unit": "box",
        "price": 8.20,
    },
    {
        "code": "ART-55012",
        "name": "Industrial packing tape 50mm x 66m, brown",
        "aliases": ["packing tape", "packaging tape", "brown tape", "50mm tape"],
        "unit": "roll",
        "price": 3.20,
    },
    {
        "code": "ART-55020",
        "name": "Stretch wrap film 500mm x 300m, clear",
        "aliases": ["stretch wrap", "pallet wrap", "stretch film", "shrink wrap"],
        "unit": "roll",
        "price": 6.80,
    },
    {
        "code": "ART-77100",
        "name": "Cable tie 200mm x 4.8mm, black (bag of 100)",
        "aliases": ["cable ties", "zip ties", "200mm cable ties", "black ties"],
        "unit": "bag",
        "price": 4.50,
    },
    {
        "code": "ART-77105",
        "name": "Cable tie 300mm x 4.8mm, black (bag of 100)",
        "aliases": ["300mm cable ties", "long cable ties", "300 zip ties"],
        "unit": "bag",
        "price": 5.90,
    },
    {
        "code": "ART-31040",
        "name": "Safety gloves, nitrile-coated, size L (pair)",
        "aliases": ["safety gloves", "work gloves", "nitrile gloves", "gloves large"],
        "unit": "pair",
        "price": 2.10,
    },
]

PRICE_BY_CODE = {p["code"]: p["price"] for p in CATALOG}
NAME_BY_CODE = {p["code"]: p["name"] for p in CATALOG}
ALL_CODES = [p["code"] for p in CATALOG]


def catalog_as_text() -> str:
    """Render the catalog as compact text to put in the prompt."""
    lines = []
    for p in CATALOG:
        lines.append(
            f'{p["code"]} | {p["name"]} | per {p["unit"]} | EUR {p["price"]:.2f} '
            f'| also called: {", ".join(p["aliases"])}'
        )
    return "\n".join(lines)
