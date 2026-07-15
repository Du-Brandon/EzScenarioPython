from ezspec.decorators import (
    EzDynamicScenario,
    EzDynamicScenarioOutline,
    EzFeature,
    EzRule,
    EzScenario,
    EzScenarioOutline,
)


def test_feature_decorator_records_kind() -> None:
    @EzFeature
    class CheckoutFeature:
        pass

    assert CheckoutFeature.__ezspec_kind__ == "feature"


def test_scenario_decorator_supports_direct_and_configured_forms() -> None:
    @EzScenario
    def first() -> None:
        pass

    @EzScenario(rule="VIP checkout")
    def second() -> None:
        pass

    assert first.__ezspec_kind__ == "scenario"
    assert second.__ezspec_metadata__ == {"rule": "VIP checkout"}


def test_other_decorators_record_their_semantics() -> None:
    @EzRule(value="checkout")
    class CheckoutRule:
        pass

    @EzScenarioOutline
    def outline() -> None:
        pass

    @EzDynamicScenario
    def dynamic() -> None:
        pass

    @EzDynamicScenarioOutline
    def dynamic_outline() -> None:
        pass

    assert CheckoutRule.__ezspec_metadata__ == {"value": "checkout"}
    assert outline.__ezspec_kind__ == "scenario_outline"
    assert dynamic.__ezspec_kind__ == "dynamic_scenario"
    assert dynamic_outline.__ezspec_kind__ == "dynamic_scenario_outline"


def test_feature_and_rule_markers_can_coexist_on_a_class() -> None:
    @EzFeature
    @EzRule(value="checkout")
    class CheckoutSpec:
        pass

    assert CheckoutSpec.__ezspec_kinds__ == frozenset({"feature", "rule"})


def test_rule_decorator_accepts_java_style_positional_value() -> None:
    @EzRule("checkout")
    class CheckoutRule:
        pass

    assert CheckoutRule.__ezspec_metadata__ == {"value": "checkout"}
