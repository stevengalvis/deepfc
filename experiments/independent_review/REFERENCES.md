# Reviewed source references

The independent audit reviewed the published joint code and results at [7e8ad0a](https://github.com/stevengalvis/deepfc/tree/7e8ad0acdcea13f5778e107882c36e5d6922fbd3). Its companion historical records are retained unchanged in this branch.

The home-slope design additionally inspected these earlier rejected approaches, without rerunning them.

- [Line-wise logistic calibration code](https://github.com/stevengalvis/deepfc/blob/10dba72593b3c79fa143ec1d7580d856b4eea6be/experiments/probability_calibration.py) and [reported result](https://github.com/stevengalvis/deepfc/blob/10dba72593b3c79fa143ec1d7580d856b4eea6be/experiments/results/championship_probability_calibration.md). Its reported NLL is binary log loss. Count NLL remained unchanged.
- [Dispersion experiment](https://github.com/stevengalvis/deepfc/blob/8ab1074e17651f620e166573d2812883c2fae04e/experiments/results/championship_dispersion.md).
- [Team-prior shrinkage experiment](https://github.com/stevengalvis/deepfc/blob/f63666c1450072bf99654713da7e579d87d98d36/experiments/results/championship_shrinkage.md).
- [Attack and concession exponent experiment](../results/championship_signal_strength.md).
- [Current joint specification](../joint_market_calibration_spec.md), [implementation](../joint_market_calibration.py), and [saved report](../results/joint_market_calibration/REPORT.md).
- [Acceptance-criteria audit](../results/acceptance_criteria_audit/AUDIT.md) and [prospective probability protocol](../protocols/team_corner_probability_confirmation.md).

The source paths above are immutable commit links where branches differ. Supporting diagnostic and execution evidence is contained in this directory; no access to an earlier private worker filesystem is assumed.
