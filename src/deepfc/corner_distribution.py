"""Probability calculations shared by DeepFC corner-count models."""

import math


def poisson_over_probability(expected_total: float, line: float) -> float:
    """Return P(corners > line) under a Poisson distribution."""

    _validate_probability_inputs(expected_total, line)

    largest_under_total = math.floor(line)
    current_total_probability = math.exp(-expected_total)
    probability_at_or_below_line = current_total_probability
    for corner_total in range(1, largest_under_total + 1):
        current_total_probability *= expected_total / corner_total
        probability_at_or_below_line += current_total_probability
    return _bounded_probability(1.0 - probability_at_or_below_line)


def negative_binomial_over_probability(
    expected_total: float,
    line: float,
    negative_binomial_dispersion: float,
) -> float:
    """Return P(corners > line) under a Negative Binomial distribution."""

    _validate_probability_inputs(expected_total, line)
    if negative_binomial_dispersion < 0:
        raise ValueError("negative_binomial_dispersion must not be negative")
    if math.isclose(negative_binomial_dispersion, 0.0, abs_tol=1e-12):
        return poisson_over_probability(expected_total, line)

    shape, success_probability = _negative_binomial_parameters(
        expected_total,
        negative_binomial_dispersion,
    )
    current_total_probability = success_probability**shape
    probability_at_or_below_line = current_total_probability
    for corner_total in range(1, math.floor(line) + 1):
        current_total_probability *= (
            (corner_total - 1 + shape) / corner_total
        ) * (1.0 - success_probability)
        probability_at_or_below_line += current_total_probability
    return _bounded_probability(1.0 - probability_at_or_below_line)


def negative_binomial_negative_log_loss(
    actual_total: int,
    expected_total: float,
    negative_binomial_dispersion: float,
) -> float:
    """Return Negative Binomial negative log likelihood for one observation."""

    if isinstance(actual_total, bool) or not isinstance(actual_total, int):
        raise ValueError("actual_total must be a non-negative integer")
    if actual_total < 0:
        raise ValueError("actual_total must be a non-negative integer")
    if expected_total <= 0:
        raise ValueError("expected_total must be greater than zero")
    if negative_binomial_dispersion < 0:
        raise ValueError("negative_binomial_dispersion must not be negative")
    if math.isclose(negative_binomial_dispersion, 0.0, abs_tol=1e-12):
        return (
            expected_total
            - actual_total * math.log(expected_total)
            + math.lgamma(actual_total + 1)
        )

    shape, success_probability = _negative_binomial_parameters(
        expected_total,
        negative_binomial_dispersion,
    )
    log_probability = (
        math.lgamma(actual_total + shape)
        - math.lgamma(shape)
        - math.lgamma(actual_total + 1)
        + shape * math.log(success_probability)
        + actual_total * math.log1p(-success_probability)
    )
    return -log_probability


def estimate_dispersion(
    observation_count: int,
    corner_sum: int,
    squared_corner_sum: int,
) -> float:
    """Estimate Negative Binomial dispersion from earlier observations."""

    if observation_count < 2:
        return 0.0
    expected_corners = corner_sum / observation_count
    if expected_corners <= 0:
        return 0.0
    sample_variance = (
        squared_corner_sum - corner_sum**2 / observation_count
    ) / (observation_count - 1)
    return max(
        0.0,
        (sample_variance - expected_corners) / expected_corners**2,
    )


def _negative_binomial_parameters(
    expected_corners: float,
    dispersion: float,
) -> tuple[float, float]:
    shape = 1.0 / dispersion
    success_probability = shape / (shape + expected_corners)
    return shape, success_probability


def _validate_probability_inputs(expected_corners: float, line: float) -> None:
    if expected_corners <= 0:
        raise ValueError("expected_corners must be greater than zero")
    if line < 0 or not math.isclose(line % 1, 0.5):
        raise ValueError("line must be a non-negative half line")


def _bounded_probability(probability: float) -> float:
    return max(0.0, min(1.0, probability))
