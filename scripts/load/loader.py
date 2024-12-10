from typing import List

from pydantic import BaseModel, Field

from common import Cookie


class Loader(BaseModel):
    name: str = Field(default="", description="The name of the loader.")
    location: str = Field(default="", description="The location of the loader.")

    def get_filename(self) -> str:
        return f"{self.location}/{self.name}"

    def load(self) -> List[Cookie]:
        raise NotImplementedError

    def save(self, data: List[Cookie]):
        raise NotImplementedError
