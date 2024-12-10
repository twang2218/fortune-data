from typing import List

from pydantic import BaseModel, Field


class ScoreEntry(BaseModel):
    score: float = Field(default=0, description="The evaluation score for the entry.")
    explanation: str = Field(
        default="", description="The details of evaluation process for this score."
    )


class Score(BaseModel):
    explaination: str = Field(
        default="",
        description="Explain the meaning of the 'content' word by word, analyze the author's writing intent, and explore the implied meanings. (Please answer in the language used by the text）",
    )
    popularity: ScoreEntry = Field(
        default=ScoreEntry(),
        description="How popular this content might be used or referenced in daily life. (0 = hardly used, 10 = very popular)",
    )
    quality: ScoreEntry = Field(
        default=ScoreEntry(),
        description="The quality and historical importance of this content. (0 = none, 10 = very significant)",
    )
    sentiment: ScoreEntry = Field(
        default=ScoreEntry(),
        description="The potential positive impact on readers' mindset or behavior. (0 = very negative, 10 = very positive)",
    )
    clarity: ScoreEntry = Field(
        default=ScoreEntry(),
        description="How easy it is to understand. (0 = very difficult, 10 = very easy)",
    )

    overall: float = Field(
        default=0,
        description="The overall score of the content. (0 = very bad, 10 = very good)",
    )

    _weights = {
        "popularity": 0.4,
        "quality": 0.2,
        "sentiment": 0.2,
        "clarity": 0.2,
    }

    def weighted_score(self) -> float:
        return sum(
            getattr(self, dim).score * self._weights[dim]
            for dim in self._weights.keys()
        )

    def update_overall(self):
        self.overall = self.weighted_score()

    def __str__(self):
        return f"(meaning: {self.explaination}, pop: {self.popularity}, qual: {self.quality}, pos: {self.sentiment}, clr: {self.clarity}) => {self.overall:.2f}"


class Cookie(BaseModel):
    title: str = Field(default="", description="title of the content, e.g. poem title")
    author: str = Field(
        default="", description="author of the content, e.g. poem author"
    )
    content: str = Field(
        default="", description="content of the cookie (poem, quote, etc.)"
    )
    source: str = Field(
        default="",
        description="source of the content, e.g. poem title, book name, author, etc.",
    )
    # extras: Optional[Dict[str, str]] = Field(default=None, description="extra information")
    link: str = Field(default="", description="link to the content")
    score: Score = Field(default=None, description="scores of the content")

    def __str__(self):
        source = self.title if self.title else self.source
        source = f"{source}  {self.author}" if self.author else source
        source = source.strip()

        if self.author:
            return f"{source}\n{self.content}"
        else:
            if source:
                if "\n" in self.content or len(self.content) > 20:
                    return f"{self.content}\n\t\t-- {source}"
                else:
                    return f"{self.content}  -- {source}"
            else:
                return self.content


class CookieList(BaseModel):
    cookies: List[Cookie] = Field(
        default=[],
        description="A list of cookies.",
    )


class CookieJar(BaseModel):
    lang: str = Field(
        default="",
        description="The language of the task, e.g. zh, en, etc.",
    )
    name: str = Field(
        default="",
        description="The name of the task.",
    )
    link: str = Field(
        default="",
        description="The link of the task.",
    )
    extractor: str = Field(
        default="",
        description="The extractor of the task.",
    )
    model_name: str = Field(
        default="tongyi:qwen-turbo-latest",
        description="The language model name.",
    )
