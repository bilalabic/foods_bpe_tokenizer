"""Turn raw registered food names into training data.

foods_raw.txt -> foods_clean.txt

Usage:
    python clean_foods.py
"""

from pathlib import Path
import argparse
import sys


# Python's lower() maps "I" -> "i"; Turkish needs "I" -> "ı" and "İ" -> "i".
# Circumflex vowels are folded because the registry spells the same province both
# ways ("Hakkari" and "Hakkâri"), which would otherwise split into two tokens.
TURKISH_LOWER_MAP = str.maketrans({
    "I": "ı",
    "İ": "i",
    "Â": "a", "â": "a",
    "Î": "i", "î": "i",
    "Û": "u", "û": "u",
})

PROVINCE_NAMES = """
Adana Adıyaman Afyonkarahisar Ağrı Amasya Ankara Antalya Artvin Aydın Balıkesir
Bilecik Bingöl Bitlis Bolu Burdur Bursa Çanakkale Çankırı Çorum Denizli
Diyarbakır Edirne Elazığ Erzincan Erzurum Eskişehir Gaziantep Giresun Gümüşhane
Hakkari Hatay Isparta Mersin İstanbul İzmir Kars Kastamonu Kayseri Kırklareli
Kırşehir Kocaeli Konya Kütahya Malatya Manisa Kahramanmaraş Mardin Muğla Muş
Nevşehir Niğde Ordu Rize Sakarya Samsun Siirt Sinop Sivas Tekirdağ Tokat
Trabzon Tunceli Şanlıurfa Uşak Van Yozgat Zonguldak Aksaray Bayburt Karaman
Kırıkkale Batman Şırnak Bartın Ardahan Iğdır Yalova Karabük Kilis Osmaniye Düzce
""".split()

# Registrations also use the everyday short forms: "Antep Baklavası", "Urfa Kebabı".
PROVINCE_ALIASES = ["Antep", "Urfa", "Maraş", "Afyon", "İçel", "Hakkâri"]

MIN_LENGTH = 3


def turkish_lower(text: str) -> str:
    return text.translate(TURKISH_LOWER_MAP).lower()


PROVINCES = {turkish_lower(p) for p in PROVINCE_NAMES + PROVINCE_ALIASES}


def strip_province(name: str) -> str:
    """Drop a leading province, but only when two or more words remain.

    In "Adana Kebabı" the possessive -ı binds to Adana, so dropping the province
    would leave the ungrammatical "kebabı". In "Patlıcanlı Kazan Kebabı" it binds
    to "kazan", so the province is free to go.
    """
    parts = name.split()
    if len(parts) > 2 and parts[0] in PROVINCES:
        return " ".join(parts[1:])
    return name


def clean_names(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for line in lines:
        name = strip_province(turkish_lower(line).strip())

        if len(name) < MIN_LENGTH or name in PROVINCES or name in seen:
            continue

        seen.add(name)
        result.append(name)

    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Lowercase food names, drop province prefixes and duplicates."
    )
    parser.add_argument("input", nargs="?", default="foods_raw.txt", help="Input file")
    parser.add_argument("output", nargs="?", default="foods_clean.txt", help="Output file")
    args = parser.parse_args()

    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    result = clean_names(lines)
    Path(args.output).write_text("\n".join(result) + "\n", encoding="utf-8")

    print(f"read {len(lines)} lines -> wrote {len(result)} clean names: {args.output}")


if __name__ == "__main__":
    main()
