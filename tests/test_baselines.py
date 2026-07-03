from pytest import approx

from dragnet import grow_prune
from dragnet.baselines import exact_banzhaf, exact_shapley, exact_shapley_interaction, ranking, sampled_shapley
from dragnet.interactions import exact_effects
from dragnet.testbed import and_game, formula_game, or_game


def test_shapley_axioms_on_the_or_cover():
    values = exact_shapley(or_game(["s1", "s2"], distractors=["d1", "d2"]))
    assert sum(values.values()) == approx(1.0)                # efficiency: the unit of blame
    assert values["s1"] == approx(values["s2"])               # symmetry
    assert values["d1"] == approx(0.0, abs=1e-12)             # null player
    assert values["s1"] == approx(0.5)


def test_shapley_confuses_redundancy_with_synergy():
    # The paper's core blindness, exactly: a redundant OR-cover and a joint AND-pair hand every
    # member the same one-half, so no additive score can tell "either alone" from "only
    # together". The order-2 surrogate separates them by the sign of the pairwise term.
    redundant = exact_shapley(or_game(["x", "y"], distractors=["d1"]))
    joint = exact_shapley(and_game(["x", "y"], distractors=["d1"]))
    assert redundant["x"] == approx(0.5) and joint["x"] == approx(0.5)
    assert redundant["y"] == approx(0.5) and joint["y"] == approx(0.5)

    surrogate_or = exact_effects(or_game(["x", "y"], distractors=["d1"]))
    surrogate_and = exact_effects(and_game(["x", "y"], distractors=["d1"]))
    assert surrogate_or.pair("x", "y") < -0.5 < 0.5 < surrogate_and.pair("x", "y")


def test_shapley_interaction_index_agrees_with_the_surrogate_signs():
    redundant = exact_shapley_interaction(or_game(["x", "y"], distractors=["d1"]))
    joint = exact_shapley_interaction(and_game(["x", "y"], distractors=["d1"]))
    assert redundant[frozenset({"x", "y"})] == approx(-1.0)
    assert joint[frozenset({"x", "y"})] == approx(1.0)
    assert redundant[frozenset({"x", "d1"})] == approx(0.0, abs=1e-12)


def test_banzhaf_matches_shapley_on_symmetric_games():
    game = or_game(["s1", "s2"], distractors=["d1"])
    banzhaf = exact_banzhaf(game)
    shapley = exact_shapley(or_game(["s1", "s2"], distractors=["d1"]))
    assert banzhaf["d1"] == approx(0.0, abs=1e-12)
    assert banzhaf["s1"] == approx(banzhaf["s2"])
    assert ranking(banzhaf) == ranking(shapley)


def test_sampled_shapley_converges_to_exact():
    exact = exact_shapley(formula_game(["a", "b", "c"], lambda s: ("a" in s and "b" in s) or "c" in s))
    sampled = sampled_shapley(
        formula_game(["a", "b", "c"], lambda s: ("a" in s and "b" in s) or "c" in s),
        n_permutations=400,
        seed=0,
    )
    for cid in exact:
        assert sampled[cid] == approx(exact[cid], abs=0.08)


def test_shapley_ranking_feeds_the_extractor():
    game = and_game(["a", "b"], distractors=["d1", "d2"])
    order = ranking(exact_shapley(and_game(["a", "b"], distractors=["d1", "d2"])))
    assert set(order[:2]) == {"a", "b"}
    result = grow_prune(game, order=order)
    assert result.subset == frozenset({"a", "b"})


def test_efficiency_holds_on_an_arbitrary_structure():
    game = formula_game(["a", "b", "c", "d"], lambda s: ("a" in s and "b" in s) or ("c" in s and "d" in s))
    values = exact_shapley(game)
    assert sum(values.values()) == approx(1.0)
