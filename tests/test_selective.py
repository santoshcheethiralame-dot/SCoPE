from dragnet.selective import bh_select, conformal_pvalues, risk_coverage, select_and_evaluate


def test_risk_coverage_answers_confident_first():
    # confidence 0.9 covers, 0.5 fails, 0.1 covers -> answering by confidence hits the failure second
    curve = risk_coverage([(0.9, True), (0.1, True), (0.5, False)])
    assert curve[0] == (1 / 3, 0.0)          # top pick covers -> zero risk
    assert curve[1][1] == 0.5                # second pick (0.5) fails -> 1/2 risk
    assert curve[-1] == (1.0, 1 / 3)         # one failure of three


def test_conformal_pvalue_direction_and_validity():
    calibration = [(s / 10, False) for s in range(10)]   # ten failing cases, scores 0.0..0.9
    # a high-scoring test point is unlikely under 'fails' -> small p; a low one -> large p
    p_high, p_low = conformal_pvalues(calibration, [(0.95, True), (0.05, True)])
    assert p_high < p_low
    assert 0 < p_high <= 1 and 0 < p_low <= 1


def test_bh_selects_a_prefix_at_level():
    # p-values well below alpha get selected; a large one does not
    selected = bh_select([0.001, 0.002, 0.9], alpha=0.1)
    assert selected == {0, 1}


def test_selection_controls_the_false_answer_rate():
    # failing cases score low (0.0-0.38), covering cases score high (0.6-0.98) -> a high-scoring
    # test point has few failing calibration cases above it, so a small p, and is safely selected.
    calibration = [(0.02 * i, False) for i in range(20)] + [(0.6 + 0.02 * i, True) for i in range(20)]
    test = [(0.9, True), (0.85, True), (0.8, True), (0.82, True), (0.25, False), (0.3, False)]
    report = select_and_evaluate(calibration, test, alpha=0.2)
    assert report["answered"] >= 3
    assert report["realized_false_answer_rate"] <= 0.2


def test_no_selection_when_nothing_is_confident():
    calibration = [(0.5, False)] * 10 + [(0.5, True)] * 10   # score carries no signal
    test = [(0.5, False)] * 5
    report = select_and_evaluate(calibration, test, alpha=0.1)
    assert report["answered"] == 0
    assert report["realized_false_answer_rate"] == 0.0
