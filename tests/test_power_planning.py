from datetime import date,timedelta
import numpy as np
import pytest
from experiments.power_planning import cluster_stats,needed,power

def test_independent_fixture_blocks_recover_mean_standard_error():
    values=[-.03,.01,.02,-.01,.04]
    days=[date(2020,1,1)+timedelta(days=i) for i in range(len(values))]
    result=cluster_stats(values,days,1)
    assert result['se']==pytest.approx(np.std(values,ddof=1)/np.sqrt(len(values)))

def test_margin_boundary_and_sample_size_scaling():
    assert power(.01,1000,0)==pytest.approx(.025)
    assert needed(.01,0,.9) is None
    assert needed(.02,.001,.9)==pytest.approx(4*needed(.01,.001,.9),abs=4)
    n=needed(.01,.001,.9)
    assert power(.01,n,.001)>=.9
