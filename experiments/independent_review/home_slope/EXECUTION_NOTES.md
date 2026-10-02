# Approved home slope execution

The saved plan was approved for local execution with its pre-scoring stopping rules intact. The original plan is retained unchanged as APPROVED_PLAN.md. This publication preserves the completed result and does not authorize additional model execution.

The implementation is a separate local artifact importing the published research modules read-only. It uses exactly the prescribed pivot, bounds, regularizer and date folds. The published fit objective and certified Newton solver are reused with an explicit earlier cutoff. There is no global-cutoff mutation and no final-coefficient refit.

The first command invoked tests from outside the repository root and encountered one existing test's relative-specification-path requirement. It passed 109 tests and failed only that path lookup. Running from the repository directory resolved it without changing published code. The published artifact retains the final successful clean-install evidence. A further synthetic test checks positive and negative interior scalar fits, without changing experiment code or rerunning the historical fit.

The support object within each fold includes a convenience passes field computed by the same helper as pooled support. It compares that individual fold with the POOL-level support floors and is not an individual-fold execution gate. The approved individual-fold requirement is at least 200 earlier training fixtures. That requirement passes for all three folds. The actual pooled OOF support requirement also passes, as shown in the top-level support object. No support threshold was relaxed.

Numerical precision and bounds are fixed in home_slope.py. The scalar objective is full NB count likelihood plus its prescribed penalty. Analytic derivatives are tested against SciPy likelihood differences and independently checked using long-double accumulation at the actual optimum.

The run stopped at its nonpositive-delta rule. No later candidate forecasts, later Brier or NLL scores, transfer metrics, later bootstrap intervals or plots were produced. The conditional later evaluation stage was not entered, and no alternative correction was substituted. No threshold interpretation is needed because the earlier stop precedes those research criteria.
