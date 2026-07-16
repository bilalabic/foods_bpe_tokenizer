"""A byte-pair-encoding tokenizer for Turkish food names.

Merges never cross whitespace. Words are merged in isolation, so no token can
span "içli köftesi" and the model cannot memorise a whole dish as one symbol,
and "\n" stays a standalone token so it keeps working as the stop signal.

Drop-in replacement for CharTokenizer: same encode/decode/vocab_size/eos_id.

Usage:
    tok = BPETokenizer.from_file("../data/foods_clean.txt")
    tok.save("merges.json")
    ids = tok.encode("içli köftesi")
    tok.decode(ids)
"""

from collections import Counter
from pathlib import Path
import json
import re


CHUNKS = re.compile(r"\S+|\s")

Pair = tuple[str, str]


def _count_pairs(word_freqs: dict[str, int], splits: dict[str, tuple[str, ...]]) -> Counter:
    pairs: Counter = Counter()
    for word, freq in word_freqs.items():
        symbols = splits[word]
        for pair in zip(symbols, symbols[1:]):
            pairs[pair] += freq
    return pairs


def _merge_word(symbols: tuple[str, ...], pair: Pair) -> tuple[str, ...]:
    merged: list[str] = []
    i = 0
    while i < len(symbols):
        if i < len(symbols) - 1 and (symbols[i], symbols[i + 1]) == pair:
            merged.append(symbols[i] + symbols[i + 1])
            i += 2
        else:
            merged.append(symbols[i])
            i += 1
    return tuple(merged)


def train_merges(text: str, vocab_size: int, min_freq: int, base_size: int) -> list[Pair]:
    """Repeatedly merge the most frequent adjacent pair inside words."""
    word_freqs = Counter(text.split())
    splits = {word: tuple(word) for word in word_freqs}
    merges: list[Pair] = []

    while base_size + len(merges) < vocab_size:
        pairs = _count_pairs(word_freqs, splits)
        if not pairs:
            break
        pair, count = pairs.most_common(1)[0]
        # A pair seen once only teaches the model one name by heart.
        if count < min_freq:
            break
        merges.append(pair)
        splits = {word: _merge_word(symbols, pair) for word, symbols in splits.items()}

    return merges


class BPETokenizer:
    def __init__(self, chars: list[str], merges: list[Pair]):
        self.chars = list(chars)
        self.merges = [tuple(m) for m in merges]
        self.ranks = {pair: i for i, pair in enumerate(self.merges)}

        tokens = self.chars + ["".join(pair) for pair in self.merges]
        self.stoi = {t: i for i, t in enumerate(tokens)}
        self.itos = {i: t for i, t in enumerate(tokens)}
        self.vocab_size = len(tokens)
        self.newline_id = self.stoi["\n"]
        self.eos_id = self.newline_id

    # 200 is where this corpus stops starving: past ~300 most tokens are seen
    # fewer than 5 times and the model can only memorise their embeddings.
    @classmethod
    def from_file(cls, path: str, vocab_size: int = 200, min_freq: int = 2) -> "BPETokenizer":
        text = Path(path).read_text(encoding="utf-8")
        if "\n" not in text:
            text += "\n"
        chars = sorted(set(text))
        return cls(chars, train_merges(text, vocab_size, min_freq, len(chars)))

    def _encode_word(self, word: str) -> list[str]:
        symbols = list(word)
        while len(symbols) >= 2:
            candidates = [
                (self.ranks[pair], i)
                for i, pair in enumerate(zip(symbols, symbols[1:]))
                if pair in self.ranks
            ]
            if not candidates:
                break
            _, i = min(candidates)
            symbols[i:i + 2] = [symbols[i] + symbols[i + 1]]
        return symbols

    def encode(self, s: str) -> list[int]:
        ids: list[int] = []
        for chunk in CHUNKS.findall(s):
            if chunk.isspace():
                ids.append(self.stoi[chunk])
            else:
                ids.extend(self.stoi[t] for t in self._encode_word(chunk))
        return ids

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos[i] for i in ids)

    def save(self, path: str) -> None:
        payload = {"chars": self.chars, "merges": [list(p) for p in self.merges]}
        Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str) -> "BPETokenizer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data["chars"], data["merges"])
