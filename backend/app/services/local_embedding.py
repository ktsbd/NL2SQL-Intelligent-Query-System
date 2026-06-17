import hashlib
import math
import re


class LocalHashEmbedding:
    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in self._tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _tokenize(self, text: str) -> list[str]:
        normalized = text.lower()
        ascii_tokens = re.findall(r"[a-z0-9_]+", normalized)
        cjk_tokens: list[str] = []
        for phrase in re.findall(r"[\u4e00-\u9fff]+", normalized):
            cjk_tokens.append(phrase)
            for size in (2, 3, 4):
                cjk_tokens.extend(phrase[index : index + size] for index in range(max(len(phrase) - size + 1, 0)))
        return ascii_tokens + cjk_tokens
