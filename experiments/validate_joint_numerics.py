"""Development-only numeric validation; never computes forecast performance."""
import json
from datetime import date
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.optimize._numdiff import approx_derivative
import experiments.joint_strength as joint
from deepfc.football_data_csv import load_football_data_csv
from deepfc.corner_distribution import estimate_dispersion

matches=load_football_data_csv(sorted(Path('data').glob('E1_*.csv'))).matches
records=[]
original=joint.solve_newton
for day in [date(2018,8,31),date(2018,10,24),date(2021,4,25),date(2022,8,1)]:
    history=[m for m in matches if m.match_date<day]
    values=[c for m in history for c in [m.home_corners,m.away_corners]]
    alpha=estimate_dispersion(len(values),sum(values),sum(c*c for c in values))
    record={'date':str(day)}
    def check(fun,hess,difference,initial):
        numeric=approx_derivative(lambda x:fun(x)[0],initial).ravel()
        analytic=fun(initial)[1]
        record['finite_difference_gradient_max_error']=float(np.max(np.abs(numeric-analytic)))
        numeric_hessian=approx_derivative(lambda x:fun(x)[1],initial)
        record['finite_difference_hessian_max_error']=float(np.max(np.abs(numeric_hessian-hess(initial))))
        x,cert=original(fun,hess,difference,initial)
        perturbed=initial+np.random.default_rng(7).normal(0,.2,len(initial))
        other,_=original(fun,hess,difference,perturbed)
        record['different_start_parameter_max_difference']=float(np.max(np.abs(x-other)))
        independent=minimize(fun,initial,jac=True,method='BFGS',options={'gtol':1e-7,'maxiter':1000})
        record['bfgs_success']=bool(independent.success)
        record['bfgs_gradient_max']=float(np.max(np.abs(fun(independent.x)[1])))
        record['bfgs_parameter_max_difference']=float(np.max(np.abs(independent.x-x)))
        record['bfgs_objective_difference']=difference(x,independent.x-x)
        eigen=np.linalg.eigvalsh(hess(x));record['minimum_eigenvalue']=float(eigen[0]);record['condition_number']=float(eigen[-1]/eigen[0])
        assert record['finite_difference_gradient_max_error']<1e-5
        assert record['finite_difference_hessian_max_error']<1e-5
        assert record['different_start_parameter_max_difference']<1e-7
        assert record['bfgs_parameter_max_difference']<1e-5
        assert abs(record['bfgs_objective_difference'])<1e-8
        return x,cert
    joint.solve_newton=check
    model=joint.fit(history,day,alpha);record['certificate']=model.diagnostics
    records.append(record)
    print('Validated '+str(day),flush=True)
joint.solve_newton=original
Path('experiments/results/joint_strength/numerical_repair/development_checks.json').write_text(json.dumps(records,indent=2)+'\n')
