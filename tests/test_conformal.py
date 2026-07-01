import random

from scope.conformal import DepthItem, calibrate_depth, coverage_and_size, depth_item, required_depth, top1_coverage
from scope.designed import necessary_family


def test_necessary_family_gives_coalitions_a_finite_depth():
    # A no-single-cause case has no causal singleton; the leave-two-out pair is what makes it
    # placeable at all — the case the culprit-rank machinery must skip.
    family = necessary_family([], synergy_pairs=[("m", "d")])
    assert required_depth(["a", "m", "b", "d"], family) == 4
    mixed = necessary_family(["c"], synergy_pairs=[("m", "d")])
    assert required_depth(["m", "d", "c"], mixed) == 2


def test_required_depth_covers_the_earliest_family_member():
    order = ["a", "b", "c", "d"]
    assert required_depth(order, [frozenset({"c"})]) == 3
    assert required_depth(order, [frozenset({"a", "c"})]) == 3
    assert required_depth(order, [frozenset({"c"}), frozenset({"a", "b"})]) == 2
    assert required_depth(order, [frozenset({"z"})]) is None
    assert required_depth(order, [frozenset()]) == 0


def test_singleton_family_reduces_to_the_culprit_rank():
    # The benchmark's rank nonconformity is the size-1 corner of the depth score.
    order = ["d1", "culprit", "d2", "d3"]
    assert required_depth(order, [frozenset({"culprit"})]) == 2


def test_calibration_is_the_conformal_order_statistic():
    items = [DepthItem(str(i), depth, 10) for i, depth in enumerate(range(1, 11))]
    assert calibrate_depth(items, alpha=0.5) == 6.0     # ceil(11 * 0.5) = 6th of 1..10
    assert calibrate_depth(items, alpha=0.1) == 10.0    # ceil(11 * 0.9) = 10, capped at n
    assert calibrate_depth([], alpha=0.1) is None


def test_uncoverable_cases_push_tau_to_the_full_context():
    items = [DepthItem("a", 1, 6), DepthItem("b", None, 6), DepthItem("c", None, 6)]
    tau = calibrate_depth(items, alpha=0.1)
    assert tau == float("inf")
    covered, size = coverage_and_size(items, tau)
    assert covered == 1 / 3         # infinite tau still cannot cover a None depth
    assert size == 6.0              # but the returned set is capped at the whole context


def test_split_conformal_coverage_holds_on_exchangeable_data():
    rng = random.Random(0)
    ids = [f"c{i}" for i in range(6)]
    items = []
    for index in range(400):
        order = ids[:]
        rng.shuffle(order)
        family = [frozenset(rng.sample(ids, 2))]
        items.append(depth_item(str(index), order, family))
    calibration, test = items[0::2], items[1::2]
    tau = calibrate_depth(calibration, alpha=0.1)
    covered, size = coverage_and_size(test, tau)
    assert covered >= 0.85          # target 0.90, finite-sample slack
    assert size <= 6.0
    assert top1_coverage(test) < covered  # the single pick is what the guarantee improves on
