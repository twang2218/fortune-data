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

stats = {}


def process_jar(jar, base_dir: str = "data"):
    global stats
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

        if jar.lang not in stats:
            stats[jar.lang] = {
                "lang": jar.lang,
                "crawled": 0,
                "tier1": 0,
                "tier2": 0,
                "jars": [],
            }

        stats[jar.lang]["crawled"] += stats_crawled
        stats[jar.lang]["tier2"] += len(cookies)
        stats[jar.lang]["jars"].append(
            {
                "name": jar.name,
                "crawled": stats_crawled,
                "tier2": len(cookies),
            }
        )

    except Exception as e:
        logger.error(f"Failed processing [{jar.lang}] '{jar.name}' failed: {e}")
        logger.exception(e)


def load_jars(task_file: str):
    jars = []
    with open(task_file, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("//"):
                # ignore empty lines and comments
                continue
            jar = CookieJar.model_validate_json(line)
            if jar.name:
                jars.append(jar)
    return jars


def process_tier2(jars: list, base_dir: str):
    process_jar_with_output_path = partial(process_jar, base_dir=base_dir)
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_jar_with_output_path, jars)


def process_tier1(jars: list, base_dir: str):
    global stats
    cookies = {}

    # Extract
    for jar in jars:
        if jar.lang not in cookies:
            cookies[jar.lang] = []
        location = Path(base_dir) / "raw" / "processed" / jar.lang
        s = Jsonl(name=jar.name, location=str(location))
        try:
            cookies[jar.lang].extend(s.load())
        except Exception as e:
            logger.error(f"Failed to load {jar.name} for {jar.lang}: {e}")

    # Transform
    transformers = [
        FilterByRank(top=500),
    ]
    # Load
    for lang, lang_cookies in cookies.items():
        for transformer in transformers:
            lang_cookies = transformer.transform(lang_cookies)
        location = Path(base_dir) / "tier1"
        s = CookieDB(name=lang, location=str(location), dat_file=False)
        s.save(lang_cookies)
        stats[lang]["tier1"] = len(lang_cookies)


def load_stats(jars: list, base_dir: str) -> dict:
    statistics = {}
    for jar in jars:
        if jar.lang not in statistics:
            statistics[jar.lang] = {
                "lang": jar.lang,
                "crawled": 0,
                "tier1": 500,
                "tier2": 0,
                "jars": [],
            }
        # crawled
        location = Path(base_dir) / "raw" / "crawled" / jar.lang
        s = Jsonl(name=jar.name, location=str(location))
        statistics[jar.lang]["crawled"] += len(s.load())
        # tier2
        location = Path(base_dir) / "raw" / "processed" / jar.lang
        s = Jsonl(name=jar.name, location=str(location))
        statistics[jar.lang]["tier2"] += len(s.load())
        # tier1
        statistics[jar.lang]["jars"].append(
            {
                "name": jar.name,
                "crawled": statistics[jar.lang]["crawled"],
                "tier2": statistics[jar.lang]["tier2"],
            }
        )
    return statistics


def show_stats():
    global stats
    print()
    print("## Statistics")
    print()
    num_jars = 0
    num_crawled = 0
    num_tier1 = 0
    num_tier2 = 0

    print("### Details")
    print()
    print("| lang | jars | crawled |  tier2  | tier1 |")
    print("|------|------|---------|---------|-------|")
    for lang, lang_stats in stats.items():
        num_jars += len(lang_stats["jars"])
        num_crawled += lang_stats["crawled"]
        num_tier1 += lang_stats["tier1"]
        num_tier2 += lang_stats["tier2"]
        # print(f"lang: [{lang}],\t jars: {len(lang_stats['jars'])},\t crawled: {lang_stats['crawled']:5},\t tier2: {lang_stats['tier2']:5} [{lang_stats['tier2']/lang_stats['crawled']*100:.1f}%],\t tier1: {lang_stats['tier1']:4}")
        print(
            f"| {lang:4} | {len(lang_stats['jars']):4} | {lang_stats['crawled']:6}  | {lang_stats['tier2']:6}  | {lang_stats['tier1']:5} |"
        )

    print()
    print("### Summary")
    print()
    # print(f"Total langs:\t {len(stats):5}\t[{', '.join(stats.keys())}]")
    # print(f"Total jars:\t {num_jars:5}")
    # print(f"Total crawled:\t {num_crawled:5}")
    # print(f"Total tier2:\t {num_tier2:5}\t[{num_tier2/num_crawled*100:.1f}%]")
    # print(f"Total tier1:\t {num_tier1:5}")
    print(f"|    title      |  value  |           notes          |")
    print("|---------------|---------|--------------------------|")
    print(f"| Total langs   | {len(stats):6}  | [{', '.join(stats.keys())}] |")
    print(f"| Total jars    | {num_jars:6}  |                          |")
    print(f"| Total crawled | {num_crawled:6}  |                          |")
    print(
        f"| Total tier2   | {num_tier2:6}  |          {num_tier2/num_crawled*100:.1f}%           |"
    )
    print(f"| Total tier1   | {num_tier1:6}  |                          |")
    print()


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
    parser.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Show stats",
    )
    args = parser.parse_args()

    if args.stats:
        global stats
        jars = load_jars(args.task_file)
        stats = load_stats(jars, args.output_path)
        show_stats()
        return

    # setup cache
    cache_dir = Path(".cache").resolve()
    Agent.init_cache(cache_dir)
    Crawler.init_cache(cache_dir)

    jars = load_jars(args.task_file)
    process_tier2(jars, args.output_path)
    process_tier1(jars, args.output_path)
    show_stats()


if __name__ == "__main__":
    main()
