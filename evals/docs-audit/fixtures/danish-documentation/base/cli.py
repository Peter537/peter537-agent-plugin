"""Kommandolinjegrænseflade til den lokale eksportør."""

import argparse


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--input", required=True)
    return value


if __name__ == "__main__":
    print(parser().parse_args().input)
