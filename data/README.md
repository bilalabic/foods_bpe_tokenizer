# data

500 registered geographical indications from [TÜRKPATENT](https://ci.turkpatent.gov.tr),
product groups *Yemekler ve çorbalar* and *Fırıncılık ve pastacılık mamulleri*.

| File | |
| --- | --- |
| `scrape_foods.py` | collects the names from the registry |
| `foods_raw.txt` | 500 names, as scraped |
| `clean_foods.py` | the cleaning pass |
| `foods_clean.txt` | 484 names, one per line |

```bash
python scrape_foods.py       # registry -> foods_raw.txt
python clean_foods.py        # foods_raw.txt -> foods_clean.txt
```

The scraper queries both product groups across every province, pages through the results one
at a time with a delay between requests, and keeps the primary name of each entry — the
slash and parenthesised variants of *"Kahta Patlıcanlı Ayran Çorbası/Kahta Balcanı Dev
Çorbası"* are the same dish. It then shuffles with a fixed seed and takes 500, so the same
query returns the same sample.

Re-running it hits the live registry, so the result can differ from the committed
`foods_raw.txt` as new products are registered.

## What it does

**Turkish lowercasing.** Python's `lower()` maps `I → i`; Turkish needs `I → ı` and `İ → i`.

**Circumflex folding.** The registry spells the same province both ways — *Hakkari* (2×) and
*Hakkâri* (3×). Unfolded they become two unrelated tokens, and `â` enters the alphabet for
the sake of three names.

**Province stripping, only when two or more words survive.** 355 of the 500 names start with
a province, but removing the first word unconditionally wrecks the other 145 — their first
word is often not a place:

```
Tandırda Van Balığı      ->  Van Balığı        (tandırda = a cooking method)
Kazan Kavurması          ->  Kavurması         (kazan = a cauldron)
Yufkalı Konuralp Pilavı  ->  Konuralp Pilavı   (yufkalı = an ingredient)
```

Even on a genuine province it depends on what is left behind, because the Turkish possessive
`-ı` binds to the word in front of it:

```
Patlıcanlı Kazan Kebabı  ->  patlıcanlı kazan kebabı    (-ı binds to kazan -> strip)
Adana Kebabı             ->  adana kebabı               (-ı binds to Adana -> keep)
Adana Şırdan             ->  adana şırdan               (2 words -> keep)
```

The suffix alone cannot separate the two cases: `haydari` is a complete dish name and
`beyranı` is a dangling possessive, yet both end in a vowel plus `ı/i`. Telling them apart
needs Turkish morphology or a dish lexicon. The word-count rule needs neither and never
produces broken Turkish.

**Dedupe.** Stripping collapses *"Urfa Ciğer Kebabı"* and *"Diyarbakır Ciğer Kebabı"* into
one dish; 29 names merge this way. One entry is a bare *"Gaziantep"* — a registry artefact,
dropped.

## Result

484 unique names, 7427 characters. The alphabet is 29 symbols: a space plus 28 letters (`j`
never occurs). No digits, no punctuation — the scraper already discards the parenthesised
and slash-separated alternative names.
