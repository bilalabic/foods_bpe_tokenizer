# foods_bpe_tokenizer

A BPE tokenizer written from scratch on Turkish registered food names, and a miniature
transformer trained with it to generate new dish names.

The model and the character-level tokenizer it is compared against come from
**[malibayram/single_letter_transformers](https://github.com/malibayram/single_letter_transformers)**
(`qwen3/`: RMSNorm, QK-Norm, GQA, RoPE, SwiGLU). This project adds the data, the BPE
tokenizer and the notebook.

```
data/         500 scraped names -> 484 clean     ->  data/README.md
model/        BPE tokenizer + TinyQwen           ->  model/README.md
demo.ipynb    the whole pipeline, end to end
```

Run `demo.ipynb` top to bottom.

## Results

| | |
| --- | --- |
| Corpus | 484 names, 7.4k characters, 29-symbol alphabet |
| Tokenizer | 200 tokens (30 chars + 170 merges), 7.4 tokens/name |
| vs character-level | 15.3 → 7.4 tokens/name, **2.1× shorter** |
| Model | 25k parameters, 3000 steps, CPU |
| Loss | 5.30 (`ln 200` baseline) → **0.33** |
| Novel names | 33% at T=0.9, 50% at T=1.2 |

BPE picks up exactly the morphology this data repeats — `kebabı` (51×), `çorbası` (41×),
`köftesi` (33×), `ciğer`, `patlıcan`:

```
ekşili çorbası           -> ['ekşili', ' ', 'çorbası']
patlıcanlı kazan kebabı  -> ['patlıcan', 'lı', ' ', 'ka', 'z', 'an', ' ', 'kebabı']
```

Samples: `etli ekşili kızılcık sarması`, `capaz yahnisi`, `günegör köftesi`,
`miflin çorbası`, `pöçüklü lahana köfte`.

## Decisions

**Strip the province only when two or more words survive.** In *"Adana Kebabı"* the
possessive `-ı` binds to *Adana*, so dropping it leaves the ungrammatical *"kebabı"*; in
*"Patlıcanlı Kazan Kebabı"* it binds to *kazan* and the province is free to go. Blind
first-word removal also mangles *"Tandırda Van Balığı"* and *"Kazan Kavurması"*, where the
first word is not a place at all. → [`data/README.md`](data/README.md)

**Merges never cross whitespace.** Otherwise one token could swallow a whole dish name and
the model would memorise 484 strings instead of learning how they are built. `\n` stays
standalone, because it is the EOS the model needs in order to stop. →
[`model/README.md`](model/README.md)

**`vocab_size=200`.** The corpus is 7.4k characters, so a larger vocabulary starves each
token of examples — and an embedding seen three times is memorised, not learned.

| vocab | tokens/name | tokens seen <5× |
| --- | --- | --- |
| 30 (char-level) | 15.3 | 0% |
| **200** | **7.4** | **14%** |
| 300 | 6.5 | 42% |
| 590 | 5.2 | 81% |

**`std=0.02` init** — the one change from upstream. `nn.Embedding` defaults to `N(0, 1)` and
weight tying makes that the output head too, so at vocab 200 the first loss was 32 instead
of 5.30. It is a trade-off, not a free win:

| init | loss | novel names (T=0.9) |
| --- | --- | --- |
| `N(0, 1)` (upstream) | 0.477 | 59% |
| `std=0.02` | **0.329** | 33% |

Fitting the data better means copying it more. With 484 names, low loss and invention pull
against each other; temperature is the dial between them.
