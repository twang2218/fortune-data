import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

from common import Agent, CookieJar
from dotenv import load_dotenv
from extract import Crawler, Extractor
from load import CookieDB, Jsonl
from loguru import logger
from transform import (
    ChineseConverter,
    FilterByLength,
    FilterByRank,
    FilterByScore,
    Scorer,
)


def process_jar(jar, base_dir: str = "data"):
    try:
        # Extract
        cookies = Extractor.extract(jar)
        location = os.path.join(base_dir, "raw", "crawled", jar.lang)
        s = Jsonl(name=jar.name, location=location)
        s.save(cookies)

        stats_crawled = len(cookies)

        # Transform
        batch_size = 50
        # model_name = "tongyi:qwen-turbo-latest"
        transformers = [
            FilterByLength(min_length=5, max_length=500),
            Scorer(model_name=jar.model_name, batch_size=batch_size),
            FilterByScore(score=6.5),
            FilterByRank(top=jar.limit),
        ]
        if jar.lang.startswith("zh"):
            transformers.append(ChineseConverter(lang=jar.lang))

        for transformer in transformers:
            cookies = transformer.transform(cookies)
        location = os.path.join(base_dir, "raw", "processed", jar.lang)
        s = Jsonl(name=jar.name, location=location)
        s.save(cookies)

        # Load
        # tier2
        location = os.path.join(base_dir, "tier2", jar.lang)
        s = CookieDB(name=jar.name, location=location, dat_file=False)
        s.save(cookies)
        logger.info(
            f"Completed: [{jar.lang}] '{jar.name}': {stats_crawled} cookies retrieved => {len(cookies)} cookies saved."
        )
    except Exception as e:
        logger.error(f"Failed processing [{jar.lang}] '{jar.name}' failed: {e}")
        logger.exception(e)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "task_file",
        type=str,
        nargs="?",
        help="Path to the task file.",
        default="tasks.jsonl",
    )
    parser.add_argument(
        "output_path",
        type=str,
        nargs="?",
        default="cookies",
        help="Path to the output cookie file. default is the input_file",
    )
    args = parser.parse_args()

    # setup cache
    cache_dir = Path(".cache").resolve()
    Agent.init_cache(cache_dir)
    Crawler.init_cache(cache_dir)

    jars = []
    with open(args.task_file, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("//"):
                # ignore empty lines and comments
                continue
            jar = CookieJar.model_validate_json(line)
            if jar.name:
                jars.append(jar)

    process_jar_with_output_path = partial(process_jar, base_dir=args.output_path)
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_jar_with_output_path, jars)

    # tier1
    cookies = {}
    for jar in jars:
        if jar.lang not in cookies:
            cookies[jar.lang] = []
        location = os.path.join(args.output_path, "raw", "processed", jar.lang)
        s = Jsonl(name=jar.name, location=location)
        try:
            cookies[jar.lang].extend(s.load())
        except Exception as e:
            logger.error(f"Failed to load {jar.name} for {jar.lang}: {e}")

    # Transform
    transformers = [
        FilterByRank(top=500),
    ]
    logger.info("## tier1")
    for lang, lang_cookies in cookies.items():
        for transformer in transformers:
            lang_cookies = transformer.transform(lang_cookies)
        location = os.path.join(args.output_path, "tier1")
        s = CookieDB(name=lang, location=location, dat_file=False)
        s.save(lang_cookies)
        logger.info(f"  [tier1] '{lang}': {len(lang_cookies)} cookies.")
    logger.info("## tier2")
    for lang, lang_cookies in cookies.items():
        logger.info(f"  [tier2] '{lang}': {len(lang_cookies)} cookies.")

if __name__ == "__main__":
    main()
