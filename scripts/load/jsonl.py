from typing import Generic, List, TypeVar

from pydantic import BaseModel

from .loader import Loader

T = TypeVar("T", bound=BaseModel)


class Jsonl(Loader[T], Generic[T]):
    def load(self) -> List[T]:
        results = []
        filename = self.get_filename() + ".jsonl"
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                # ignore empty lines and comments
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                results.append(T.model_validate_json(line))
        return results

    def save(self, data: List[T]):
        filename = self.get_filename() + ".jsonl"
        with open(filename, "w", encoding="utf-8") as f:
            for item in data:
                f.write(item.model_dump_json() + "\n")
