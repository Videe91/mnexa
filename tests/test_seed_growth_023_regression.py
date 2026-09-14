from experiments.seed_growth_023 import (
    classify_assembly_effect,
)


def test_upstream_rank_miss_takes_precedence_over_no_change():
    result = classify_assembly_effect(
        target_family_id="target",
        fixed_selected_ids=[
            "a",
            "b",
            "c",
        ],
        dynamic_selected_ids=[
            "a",
            "b",
            "c",
        ],
    )

    assert (
        result["assembly_class"]
        ==
        "upstream_rank_miss"
    )

    assert (
        result["target_in_fixed_top3"]
        is False
    )

    assert (
        result["target_retained"]
        is False
    )
