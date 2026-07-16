# model

Two halves: the BPE tokenizer written for this project, and the transformer taken from
[malibayram/single_letter_transformers](https://github.com/malibayram/single_letter_transformers).

| File | Origin |
| --- | --- |
| `bpe_tokenizer.py`, `merges.json` | this project |
| `tokenizer.py` — character-level | upstream, kept for comparison |
| `config.py` … `model.py`, `train.py`, `generate.py` | upstream `qwen3/` |
| `tiny_food.pt` | trained checkpoint |

## Tokenizer

Plain BPE: start from single characters, repeatedly merge the most frequent adjacent pair.
Three rules shape ours.

**Merges never cross whitespace.** Words are merged in isolation, so no token can cover
`içli köftesi`. Without this the model memorises 484 strings instead of learning how a dish
name is built.

**`\n` stays standalone.** It marks the start and end of a name and is the EOS the model
stops on. A merge spanning it would leave the model unable to stop.

**`min_freq=2`** caps the vocabulary on its own: asking for 800 tokens yields 590, because
past that no pair repeats. A token seen once teaches one name by heart.

Drop-in compatible with upstream's `CharTokenizer` — same `encode` / `decode` /
`vocab_size` / `eos_id`, so only the import line changes.

```python
tok = BPETokenizer.from_file("../data/foods_clean.txt")   # vocab_size=200
tok.save("merges.json")
tok.encode("ekşili çorbası")        # -> ['ekşili', ' ', 'çorbası']
```

## Transformer

`TinyQwen`: 25k parameters, `hidden_size=32`, 2 layers, 4 query heads over 2 KV heads,
`max_seq_len=24`. `vocab_size` flows in from the tokenizer.

The notebook trains with `BLOCK_SIZE=20`, because the longest name is 18 tokens plus the
leading newline — a shorter window would never show the model a complete name.

### The one change from upstream

`self.apply(self._init_weights)` with `std=0.02`. `nn.Embedding` defaults to `N(0, 1)`, and
weight tying makes that matrix the output head too, so logits started with std ~`sqrt(32)`
and the first loss sat at 32 instead of the uniform baseline `ln 200 = 5.30`.

| step | `N(0, 1)` | `std=0.02` |
| --- | --- | --- |
| 1 | 31.89 | 5.30 |
| 1000 | 1.24 | 0.62 |
| 3000 | 0.47 | 0.38 |

It halves the steps needed and ends ~20% lower — but the model also fits the training set
harder, and novelty at T=0.9 falls from 59% to 33%. On a 484-name corpus, lower loss is not
automatically a better generator.
