# Numerical repair validation

Statistical objective, unit Gaussian regularization, unnormalized 180-day weights,
cohorts and performance gates were unchanged. Generic solver failures were due to
near-optimum progress/precision termination, not a detectable score/Hessian error.
Identifiability is enforced by orthonormal sum-to-zero contrasts. Curvature was
positive on every accepted fit. No objective rescaling was needed; the main repair
is accurate expm1/log1p objective differences instead of subtracting large sums.

All development checks were completed before later candidate evaluation. Independent
BFGS had precision-related unsuccessful flags but agreed closely in parameters and
objective; its flag was NOT overridden for production forecasts. Candidate success
is independently established by the stricter Newton residual/curvature certificate.
Different-start convergence checks and long-double alternative score calculations
provide additional evidence for the unique convex optimum.

Development maximum finite-difference gradient error: 6.122513296e-08.
Development maximum Hessian error: 4.265713738e-08.
Independent BFGS maximum parameter difference: 3.434103051e-07.
Different-start maximum parameter difference: 7.440770222e-11.
Development Hessian condition numbers: 98.58 to 1271.14.

Full run maximum gradient_max: 9.66102065014e-09.
Full run maximum independent_gradient_max: 9.6609738016e-09.
Full run maximum gradient_agreement: 5.57156968131e-13.
Full run maximum newton_step_max: 2.54438339482e-09.
Full run maximum newton_decrement_squared: 2.4721139471e-17.
Full run maximum linear_solve_residual: 2.64697796017e-23.
Full run maximum iterations: 5.

895 certified fits; no fallback or omitted forecast fixtures. 80 tests passed.
