import os
from typing import List

from common import Cookie

from .loader import Loader


class Jsonl(Loader):
    def load(self) -> List[Cookie]:
        results = []
        filename = self.get_filename() + ".jsonl"

        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                # ignore empty lines and comments
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                results.append(Cookie.model_validate_json(line))
        return results

    def save(self, data: List[Cookie]):
        # make sure the directory exists
        filename = self.get_filename() + ".jsonl"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            for item in data:
                f.write(item.model_dump_json() + "\n")
