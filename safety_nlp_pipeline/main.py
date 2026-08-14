"""Safety NLP Pipeline - single entry point.

Runs the full pipeline end-to-end with zero user intervention:

    python main.py

Stages: fetch (idempotent + fault tolerant) -> NLTK preprocess -> GridSearchCV
training -> evaluation & plots -> batch RAG explainability -> HTML report.

Optional flags:
    --force-refresh   re-download data even if a cached CSV exists
    --no-fetch        skip the fetch step entirely (cached CSV required)
    --no-rag          skip the batch RAG explainability step
    --samples N       number of test reports to explain with RAG (default 100)
"""
import argparse
import logging
import sys
import time

import pandas as pd

import config
from src import data_fetcher, evaluator, preprocessor, rag_explainer, report_generator, trainer

logger = logging.getLogger("safety_nlp_pipeline")


def setup_logging() -> None:
    """Log to both the console and ``pipeline.log``."""
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        handlers=handlers,
    )


def run_pipeline(args: argparse.Namespace) -> int:
    start = time.perf_counter()
    logger.info("=" * 62)
    logger.info("  SAFETY NLP PIPELINE  -  start")
    logger.info("=" * 62)

    # ---- Step 1: fetch ----------------------------------------------------
    logger.info("[1/6] FETCH DATA")
    if args.no_fetch:
        if not config.DATASET_PATH.exists():
            logger.error("--no-fetch given but no cached dataset exists at %s",
                         config.DATASET_PATH)
            return 1
        df = data_fetcher._load_cached()  # noqa: SLF001 - reuse normaliser
        logger.info("Loaded cached dataset (%d rows).", len(df))
    else:
        df = data_fetcher.fetch_all(force_refresh=args.force_refresh)

    # ---- Step 2: preprocess ------------------------------------------------
    logger.info("[2/6] PREPROCESS (NLTK)")
    t0 = time.perf_counter()
    processed = preprocessor.preprocess_dataset(df[config.NARRATIVE_COL])
    df[config.PROCESSED_COL] = pd.Series(processed, index=df.index)
    logger.info("Preprocessed %d narratives in %.1fs.",
                len(df), time.perf_counter() - t0)

    # ---- Step 3: train & cross-validate ------------------------------------
    logger.info("[3/6] TRAIN + GRIDSEARCHCV")
    model, vectorizer, X_train, y_train, X_test, y_test = \
        trainer.train_and_save(df)

    # ---- Step 4: evaluate & plot -------------------------------------------
    logger.info("[4/6] EVALUATE + PLOTS")
    eval_results = evaluator.evaluate_and_plot(
        model, vectorizer, X_test, y_test, df=df)

    # ---- Step 5: batch RAG explainability ----------------------------------
    rag_examples = pd.DataFrame()
    if not args.no_rag:
        logger.info("[5/6] BATCH RAG EXPLAINABILITY")
        rag_examples = rag_explainer.batch_rag(
            model, vectorizer, df, X_train, X_test, y_test,
            n_samples=args.samples)

    # ---- Step 6: HTML report -----------------------------------------------
    logger.info("[6/6] HTML REPORT")
    report_path = report_generator.generate_report(
        df, eval_results, rag_examples)
    logger.info("Report: %s", report_path)

    elapsed = time.perf_counter() - start
    logger.info("=" * 62)
    logger.info("  PIPELINE COMPLETED in %.1fs - open the report in a browser.",
                elapsed)
    logger.info("  %s", report_path)
    logger.info("=" * 62)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Safety NLP Pipeline end-to-end.")
    parser.add_argument("--force-refresh", action="store_true",
                        help="re-download data even if a cached CSV exists")
    parser.add_argument("--no-fetch", action="store_true",
                        help="skip fetching; requires a cached CSV")
    parser.add_argument("--no-rag", action="store_true",
                        help="skip batch RAG explainability")
    parser.add_argument("--samples", type=int, default=config.RAG_N_SAMPLES,
                        help=f"RAG test samples (default {config.RAG_N_SAMPLES})")
    return parser.parse_args()


def main() -> int:
    setup_logging()
    args = parse_args()
    if args.samples <= 0:
        logger.error("--samples must be a positive integer.")
        return 1
    return run_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
