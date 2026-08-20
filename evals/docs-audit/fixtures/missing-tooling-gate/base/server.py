"""Local server command contract."""

import argparse


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--bind", default="127.0.0.1")
    return value


if __name__ == "__main__":
    print(parser().parse_args().bind)
