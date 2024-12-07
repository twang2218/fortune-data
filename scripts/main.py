import os

from dotenv import load_dotenv
from extract import Extractor
from load import CookieDB, Jsonl
from model import Cookie, CookieJar
from transform import Scorer, FilterByLength, FilterByScore


def main():
    load_dotenv()
    # parser = argparse.ArgumentParser()
    # parser.add_argument("input_path", type=str, help="Path to the input JSON file.")
    # parser.add_argument(
    #     "output_path",
    #     type=str,
    #     nargs="?",
    #     help="Path to the output cookie file. default is the input_file",
    # )
    # args = parser.parse_args()

    jars = []
    with open("tasks.jsonl", "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            jar = CookieJar.model_validate_json(line)
            if jar.name:
                jars.append(jar)

    location_extract = "data/extract"
    location_transform = "data/transform"
    location_load = "data/load"

    os.makedirs(location_extract, exist_ok=True)
    os.makedirs(location_transform, exist_ok=True)
    os.makedirs(location_load, exist_ok=True)

    for jar in jars:
        # Extract
        cookies = Extractor.extract(jar)
        s = Jsonl[Cookie](name=jar.name, location=location_extract)
        s.save(cookies)

        # Transform
        transformers = [
            FilterByLength(min_length=5, max_length=300),
            Scorer(batch_size=1),
            FilterByScore(score=5.0),
            # FilterByRank(top=100),
        ]
        for transformer in transformers:
            cookies = transformer.transform(cookies)
        s = Jsonl[Cookie](name=jar.name, location=location_transform)
        s.save(cookies)

        # # Transform - Scoring
        # scorer = Scorer()
        # cookies = scorer.score(cookies)
        # s = Jsonl[Cookie](name=jar.name, location=location_transform)
        # s.save(cookies)

        # Transform - Filtering
        ## Sort cookies by overall score
        ## Select top xxx cookies
        ## Filter out cookie content that is too long

        # Load
        s = CookieDB(name=jar.name, location=location_load)
        s.save(cookies)


if __name__ == "__main__":
    main()
