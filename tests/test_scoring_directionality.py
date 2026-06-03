from ai_economics_cockpit.scoring.normalize import metric_stress_score


def test_higher_validates_scores_upward():
    assert metric_stress_score(1, "higher_validates_thesis", 1, 2, 3) == 0
    assert metric_stress_score(3, "higher_validates_thesis", 1, 2, 3) == 100
    assert metric_stress_score(2, "higher_validates_thesis", 1, 2, 3) == 50


def test_lower_validates_scores_downward():
    assert metric_stress_score(3, "lower_validates_thesis", 3, 2, 1) == 0
    assert metric_stress_score(1, "lower_validates_thesis", 3, 2, 1) == 100
    assert metric_stress_score(2, "lower_validates_thesis", 3, 2, 1) == 50

