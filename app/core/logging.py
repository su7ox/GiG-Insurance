"""Structured logging configuration shared across the app."""
import logging


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO)
