from ai_economics_cockpit.scoring.confidence import confidence_weight


def test_confidence_weights():
    assert confidence_weight("A") == 1.0
    assert confidence_weight("B") == 0.85
    assert confidence_weight("C") == 0.65
    assert confidence_weight("D") == 0.35

