from collections.abc import Iterable


class TotalCalculationStrategy:
    def calculate(self, values: Iterable[int]) -> int:
        result = 0
        for value in values:
            if value < 0:
                raise ValueError("line values must be non-negative")
            result += value
        return result


class TotalCalculationFactory:
    @staticmethod
    def create() -> TotalCalculationStrategy:
        return TotalCalculationStrategy()


def calculate_total(values: Iterable[int]) -> int:
    strategy = TotalCalculationFactory.create()
    return strategy.calculate(values)
