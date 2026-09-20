import pytest

from deepfc.corner_distribution import (
    estimate_dispersion,
    negative_binomial_negative_log_loss,
    negative_binomial_over_probability,
    poisson_over_probability,
)


def test_poisson_over_and_under_are_complements() -> None:
    over_probability = poisson_over_probability(10.0, 9.5)

    assert 0.0 < over_probability < 1.0
    assert over_probability + (1.0 - over_probability) == pytest.approx(1.0)


def test_over_probability_decreases_as_line_increases() -> None:
    probabilities = [
        poisson_over_probability(10.0, line)
        for line in (8.5, 9.5, 10.5, 11.5)
    ]

    assert probabilities == sorted(probabilities, reverse=True)


def test_negative_binomial_matches_poisson_with_zero_dispersion() -> None:
    assert negative_binomial_over_probability(10.0, 9.5, 0.0) == pytest.approx(
        poisson_over_probability(10.0, 9.5)
    )


def test_negative_binomial_assigns_more_probability_to_high_total() -> None:
    poisson_probability = poisson_over_probability(10.0, 14.5)
    negative_binomial_probability = negative_binomial_over_probability(
        10.0,
        14.5,
        0.02,
    )

    assert negative_binomial_probability > poisson_probability


def test_negative_binomial_over_probability_decreases_as_line_increases() -> None:
    probabilities = [
        negative_binomial_over_probability(5.0, line, 0.1)
        for line in (3.5, 4.5, 5.5, 6.5)
    ]

    assert probabilities == sorted(probabilities, reverse=True)


def test_dispersion_estimate_uses_observed_variance() -> None:
    assert estimate_dispersion(2, 20, 400) == pytest.approx(1.9)
    assert estimate_dispersion(1, 10, 100) == 0.0
    assert estimate_dispersion(2, 0, 0) == 0.0


def test_negative_binomial_loss_is_finite() -> None:
    assert negative_binomial_negative_log_loss(10, 10.0, 1.9) > 0.0


@pytest.mark.parametrize("line", [-0.5, 9.0])
def test_probability_rejects_unsupported_lines(line: float) -> None:
    with pytest.raises(ValueError):
        poisson_over_probability(10.0, line)
