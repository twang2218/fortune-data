from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class Loader(BaseModel, Generic[T]):
    name: str = Field(default="", description="The name of the loader.")
    location: str = Field(default="", description="The location of the loader.")

    def get_filename(self) -> str:
        return f"{self.location}/{self.name}"

    def load(self) -> List[T]:
        raise NotImplementedError

    def save(self, data: List[T]):
        raise NotImplementedError
