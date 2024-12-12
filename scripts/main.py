import argparse
import os
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from loguru import logger

from common import CookieJar
from extract import Extractor
from load import CookieDB, Jsonl
from transform import (
    ChineseConverter,
    FilterByLength,
    FilterByRank,
    FilterByScore,
    Scorer,
)


def process_jar(jar):
    try:
        # Extract
        cookies = Extractor.extract(jar)
        location = os.path.join("data", "extract", jar.lang)
        s = Jsonl(name=jar.name, location=location)
        s.save(cookies)

        # Transform
        batch_size = 50
        # model_name = "tongyi:qwen-turbo-latest"
        transformers = [
            FilterByLength(min_length=5, max_length=300),
            Scorer(model_name=jar.model_name, batch_size=batch_size),
            FilterByScore(score=6.5),
            FilterByRank(top=jar.limit),
        ]
        if jar.lang.startswith("zh"):
            transformers.append(ChineseConverter(lang=jar.lang))

        for transformer in transformers:
            cookies = transformer.transform(cookies)
        location = os.path.join("data", "transform", jar.lang)
        s = Jsonl(name=jar.name, location=location)
        s.save(cookies)

        # Load
        location = os.path.join("data", "load", "packaged", jar.lang)
        s = CookieDB(name=jar.name, location=location, dat_file=False)
        s.save(cookies)
        logger.info(f"Processing '{jar.name}' completed. {len(cookies)} cookies saved.")
    except Exception as e:
        logger.error(f"Processing '{jar.name}' failed: {e}")
        logger.exception(e)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_path",
        type=str,
        nargs="?",
        default="tasks.jsonl",
        help="Path to the input JSON file.",
    )
    # parser.add_argument(
    #     "output_path",
    #     type=str,
    #     nargs="?",
    #     help="Path to the output cookie file. default is the input_file",
    # )
    args = parser.parse_args()

    jars = []
    with open(args.input_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("//"):
                # ignore empty lines and comments
                continue
            jar = CookieJar.model_validate_json(line)
            if jar.name:
                jars.append(jar)

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_jar, jars)

    # embedded
    logger.info("Processing embedded cookies")
    cookies = {}
    for jar in jars:
        if jar.lang not in cookies:
            cookies[jar.lang] = []
        location = os.path.join("data", "transform", jar.lang)
        s = Jsonl(name=jar.name, location=location)
        try:
            cookies[jar.lang].extend(s.load())
        except Exception as e:
            logger.error(f"Failed to load {jar.name} for {jar.lang}: {e}")
    # Transform
    transformers = [
        FilterByRank(top=500),
    ]
    for lang, lang_cookies in cookies.items():
        for transformer in transformers:
            lang_cookies = transformer.transform(lang_cookies)
        location = os.path.join("data", "load", "embedded", lang)
        s = CookieDB(name=lang, location=location, dat_file=True)
        s.save(lang_cookies)


if __name__ == "__main__":
    main()
