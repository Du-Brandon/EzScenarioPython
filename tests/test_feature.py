import pytest

from ezspec.feature import Feature


def test_feature_factory_and_rules():
    feature = Feature.New("Checkout", "Customers pay for their cart")
    vip = feature.NewRule("VIP", "VIP customers receive a discount")

    assert feature.getName() == "Checkout"
    assert feature.getDescription() == "Customers pay for their cart"
    assert feature.getRule("VIP") is vip
    assert feature.getRules() == (vip,)
    assert feature.getDefaultRule() is not None


def test_feature_rejects_duplicate_rule_name():
    feature = Feature.New("Checkout")
    feature.NewRule("VIP")

    with pytest.raises(ValueError, match="cannot be duplicated"):
        feature.NewRule("VIP")


def test_scenario_can_move_from_default_rule_to_named_rule():
    feature = Feature.New("Checkout")
    vip = feature.NewRule("VIP")
    scenario = feature.newScenario("discount")

    returned = scenario.withRule("VIP")

    assert returned is scenario
    assert feature.getDefaultRule().getScenarios() == []
    assert vip.getScenarios() == [scenario]
    assert scenario.rule is vip


def test_feature_renders_default_and_named_rules():
    feature = Feature.New("Checkout", "Customers pay")
    feature.newScenario("regular checkout")
    feature.NewRule("VIP").newScenario("discount checkout")

    text = str(feature)
    assert text.startswith("Feature: Checkout\n\nCustomers pay")
    assert "Scenario: regular checkout" in text
    assert "Rule: VIP" in text
    assert "Scenario: discount checkout" in text


def test_omitted_scenario_name_uses_calling_function_name():
    feature = Feature.New("Checkout")

    def vip_customer_gets_discount():
        return feature.newScenario()

    scenario = vip_customer_gets_discount()

    assert scenario.getName() == "vip_customer_gets_discount"
