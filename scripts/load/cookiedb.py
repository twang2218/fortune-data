import os
from typing import List

from model import Cookie

from .loader import Loader


class CookieDB(Loader[Cookie]):
    def load(self) -> List[Cookie]:
        results = []

        filename = self.get_filename()
        if not os.path.exists(filename):
            return results

        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        if not content:
            return results

        # normalize line endings
        content = content.replace("\r\n", "\n")
        for section in content.split("\n%\n"):
            section = section.strip()
            if not section:
                continue
            results.append(Cookie(content=section, source=self.name))
        return results

    def save(self, data: List[Cookie]):
        filename = self.get_filename()
        with open(filename, "w", encoding="utf-8") as f:
            for item in data:
                f.write(f"{item}\n%\n")
