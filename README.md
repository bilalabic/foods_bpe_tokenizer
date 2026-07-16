# foods_bpe_tokenizer

A BPE tokenizer written from scratch on Turkish registered food names, and a miniature
transformer trained with it to generate new dish names.

The model and the character-level tokenizer it is compared against come from
**[malibayram/single_letter_transformers](https://github.com/malibayram/single_letter_transformers)**
(`qwen3/`: RMSNorm, QK-Norm, GQA, RoPE, SwiGLU). This project adds the data, the BPE
tokenizer and the notebook.

Run `demo.ipynb` top to bottom. Python 3.13 + torch, nothing else.

## Data

500 registered geographical indications from TÜRKPATENT, product groups *Yemekler ve
çorbalar* and *Fırıncılık ve pastacılık mamulleri*.

`data/clean_foods.py` → **484 names, 29-character alphabet**: Turkish lowercasing (`I→ı`,
`İ→i`), circumflex folding (the registry writes both *Hakkari* and *Hakkâri*), province
stripping, dedupe.

The province is dropped only when two or more words survive. In *"Adana Kebabı"* the
possessive `-ı` binds to *Adana*, so stripping it would leave the ungrammatical *"kebabı"*;
in *"Patlıcanlı Kazan Kebabı"* it binds to *kazan* and the province is free to go.

```bash
cd data && python clean_foods.py
```

## Tokenizer

`model/bpe_tokenizer.py`, stdlib only. Merges never cross whitespace, so no token can
swallow a whole dish name and let the model memorise it. `\n` stays standalone and is the
EOS the model uses to stop.

`vocab_size=200` — the corpus is 7.4k characters, so a larger vocabulary starves each token:

| vocab | tokens/name | tokens seen <5× |
| --- | --- | --- |
| 30 (char-level) | 15.3 | 0% |
| **200** | **7.4** | **14%** |
| 300 | 6.5 | 42% |
| 590 | 5.2 | 81% |

## Model

25k parameters, 3000 steps, CPU. Loss **5.30 → 0.33** (5.30 = `ln 200`, the uniform
baseline).

`model/model.py` has one change from upstream: weights are initialised at `std=0.02`.
`nn.Embedding` defaults to `N(0, 1)` and weight tying makes that the output head too, so at
vocab 200 the first loss was 32 instead of 5.30.

It is a trade-off, not a free win — fitting the data better means copying it more:

| init | loss | novel names (T=0.9) |
| --- | --- | --- |
| `N(0, 1)` (upstream) | 0.477 | 59% |
| `std=0.02` | **0.329** | 33% |

## Generating

Names are sampled from the newline token until the model emits newline again, then checked
against the training set — reproducing *adana kebabı* is memorisation, not generation.
Temperature is the dial:

| T | novel | sample |
| --- | --- | --- |
| 0.6 | 15% | `bolvadin mantısı` (copy) |
| 0.9 | 33% | `capaz yahnisi` |
| 1.2 | 50% | `kübbürt pilavı` |
