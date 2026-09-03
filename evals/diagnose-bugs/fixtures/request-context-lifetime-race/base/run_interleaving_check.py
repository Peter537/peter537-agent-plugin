import argparse
import asyncio

from request_context import handle_request


async def exercise_interleaving() -> bool:
    first_started = asyncio.Event()
    second_started = asyncio.Event()
    release_first = asyncio.Event()
    release_second = asyncio.Event()
    tasks: list[asyncio.Task[str]] = []

    try:
        first = asyncio.create_task(
            handle_request("request-one", first_started, release_first)
        )
        tasks.append(first)
        await first_started.wait()

        second = asyncio.create_task(
            handle_request("request-two", second_started, release_second)
        )
        tasks.append(second)
        await second_started.wait()

        release_first.set()
        release_second.set()
        first_result, second_result = await asyncio.gather(first, second)
        return first_result == "request-one" and second_result == "request-two"
    finally:
        release_first.set()
        release_second.set()
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


def positive_integer(value: str) -> int:
    runs = int(value)
    if runs < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return runs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=positive_integer, required=True)
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    failures = 0
    for _ in range(args.runs):
        failures += not await exercise_interleaving()
    print(f"failures={failures}/{args.runs}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
