from datetime import date, timedelta
import pytest
from deepfc.match_data import Match
from experiments.shot_reconstruction import Shot, pressure, load_shots, generate, key


def test_empty_and_neutral_history():
    assert pressure([], 'A','B','home',date(2020,1,2)) == 1
    history = [Shot(date(2020,1,1),'A','home',10,10,4,4), Shot(date(2020,1,1),'B','away',10,10,4,4)]
    assert pressure(history,'A','B','home',date(2020,1,2)) == pytest.approx(1)


@pytest.mark.parametrize('when',[date(2020,1,2),date(2020,1,3)])
def test_same_day_and_future_rejected(when):
    with pytest.raises(ValueError,match='strictly precede'):
        pressure([Shot(when,'A','home',10,10,4,4)],'A','B','home',date(2020,1,2))


def test_weighting_and_venue_roles():
    history = [Shot(date(2020,1,1),'A','home',30,10,12,4),
               Shot(date(2020,6,29),'C','home',10,10,4,4),
               Shot(date(2020,6,29),'B','away',10,20,4,8)]
    assert pressure(history,'A','B','home',date(2020,6,29)+timedelta(days=1)) == pytest.approx(
        # The extra day decays both weights and changes smoothing slightly.
        manual(history, date(2020,6,30)))
    altered = history+[Shot(date(2020,1,1),'A','away',1000,10,400,4)]
    assert pressure(altered,'A','B','home',date(2020,6,30)) == pressure(history,'A','B','home',date(2020,6,30))


def manual(history, when):
    w1=0.5**((when-history[0].when).days/180)
    w2=0.5**((when-history[1].when).days/180)
    league=(30*w1+10*w2)/(w1+w2)
    return ((30*w1+5*league)/(w1+5))*((20*w2+5*league)/(w2+5))/league**2


def test_quarantine_preserves_corner_cohort(tmp_path):
    p=tmp_path/'E1.csv'
    p.write_text('Div,Date,HomeTeam,AwayTeam,HC,AC,HS,AS,HST,AST\nE1,10/11/2024,Burnley,Swansea,4,3,2,10,7,3\nE1,11/11/2024,A,B,2,3,12,9,4,2\n')
    from deepfc.football_data_csv import load_football_data_csv
    loaded=load_football_data_csv([p])
    shots, excluded=load_shots([p],loaded.matches)
    assert loaded.rows_loaded == 2
    assert len(shots)==1 and len(excluded)==1
    assert 'quarantine' in excluded[0]['reason']
    assert excluded[0]['raw']['HS']=='2'


@pytest.mark.parametrize('stats',['-1,5,0,1','2,5,3,1',',5,0,1','1.5,5,0,1'])
def test_invalid_shots_do_not_drop_corners(tmp_path,stats):
    p=tmp_path/'E1.csv'
    p.write_text('Div,Date,HomeTeam,AwayTeam,HC,AC,HS,AS,HST,AST\nE1,01/01/2020,A,B,2,3,'+stats+'\n')
    m=Match(date(2020,1,1),'E1','A','B',2,3)
    shots, excluded=load_shots([p],[m])
    assert shots=={} and len(excluded)==1


def test_future_and_same_day_outcomes_cannot_change_predictions():
    matches=[Match(date(2018,1,1)+timedelta(days=i),'E1','A','B',3+i%4,2+i%3) for i in range(60)]
    target=Match(date(2018,7,1),'E1','A','B',4,3)
    matches += [target]
    shots={key(m):(Shot(m.match_date,'A','home',10,9,4,3),Shot(m.match_date,'B','away',9,10,3,4)) for m in matches}
    before,candidates=generate(matches,shots)
    altered=dict(shots)
    altered[key(target)]=(Shot(target.match_date,'A','home',1000,900,400,300),)
    future=Match(date(2018,7,2),'E1','A','B',99,99)
    after,changed=generate(matches+[future],altered)
    assert len(before)==2
    for strength in candidates:
        assert changed[strength][:2]==candidates[strength]
        assert [(p.match,p.venue,p.dispersion) for p in candidates[strength]] == [(p.match,p.venue,p.dispersion) for p in before]


def test_complete_report_on_synthetic_three_period_cohort(tmp_path):
    from experiments.shot_reconstruction import run
    rows=['Div,Date,HomeTeam,AwayTeam,HC,AC,HS,AS,HST,AST']
    days=[date(2018,1,1)+timedelta(days=i) for i in range(60)]
    days += [date(2018,7,1),date(2023,8,1),date(2024,8,1)]
    rows += [f'E1,{d:%d/%m/%Y},A,B,4,3,10,10,4,4' for d in days]
    path=tmp_path/'synthetic.csv'
    path.write_text('\n'.join(rows)+'\n')
    result=run([path])
    assert result['selected_strength']==0.25
    assert not result['selected_beats_baseline_in_selection']
    assert set(result['comparison']['periods'])=={'selection','validation','later_test'}
    assert all(value['candidate_minus_baseline']['mean_brier_score']==0 for value in result['comparison']['periods'].values())
