import os
import subprocess
from pathlib import Path
from typing import List

from common import Cookie
from loguru import logger
from pydantic import Field

from .loader import Loader


class CookieDB(Loader):
    dat_file: bool = Field(default=False, description="Whether to generate .dat file")

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

    def save_dat(self):
        cookie_file = Path(self.get_filename())
        cookie_dat_file = cookie_file.with_suffix(".dat")

        if cookie_file.exists() and cookie_file.is_file():
            logger.debug(f"strfile {cookie_file}")
            if cookie_dat_file.exists() and cookie_dat_file.is_file():
                cookie_dat_file.unlink()
            subprocess.run(["strfile", cookie_file])
            if not cookie_dat_file.exists() or not cookie_dat_file.is_file():
                raise FileNotFoundError(f"strfile failed to create {cookie_dat_file}")
        else:
            raise FileNotFoundError(f"Cookie file {cookie_file} not found")

    def save(self, data: List[Cookie]):
        filename = self.get_filename()
        Path.mkdir(Path(filename).parent, parents=True, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            for item in data:
                f.write(f"{item}\n%\n")
        if self.dat_file:
            self.save_dat()
