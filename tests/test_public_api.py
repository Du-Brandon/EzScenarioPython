from ezspec import (
    ContinuousAfterFailure,
    EzFeature,
    EzScenario,
    EzRule,
    Feature,
    Result,
    ScenarioEnvironment,
    Table,
    pending,
)


def test_vip_checkout_fluent_public_api() -> None:
    feature = Feature.New("購物車結帳")

    def prepare_cart(env: ScenarioEnvironment) -> None:
        env.put("price", 1000)

    def checkout(env: ScenarioEnvironment) -> None:
        env.put("total", env.geti("price") * 0.9)

    def verify_total(env: ScenarioEnvironment) -> None:
        assert env.get("total", float) == 900

    scenario = (
        feature.newScenario("VIP 顧客結帳享有九折優惠")
        .Given("購物車金額為 1000 元", prepare_cart)
        .When("VIP 顧客進行結帳", checkout)
        .Then("應付金額為 900 元", verify_total)
    )

    scenario.Execute()

    assert all(step.getResult().isSuccess() for step in scenario.steps())


def test_public_compatibility_symbols_are_importable() -> None:
    assert ContinuousAfterFailure is True
    assert Result.Success().isSuccess()
    assert isinstance(Table("| value |\n| one |"), Table)
    assert callable(pending)
    assert callable(EzFeature)
    assert callable(EzScenario)


def test_feature_visitor_traverses_feature_scenario_and_steps() -> None:
    visited: list[str] = []

    class Visitor:
        def visit(self, element: object) -> None:
            visited.append(type(element).__name__)

    feature = Feature.New("checkout")
    feature.newScenario("pay").Given("a cart", lambda env: None)

    feature.accept(Visitor())

    assert visited == ["Feature", "RuntimeScenario", "Given"]


def test_dynamic_execute_preserves_fluent_scenario_object() -> None:
    scenario = Feature.New("feature").newScenario("scenario").Given(
        "given", lambda env: None
    )

    assert scenario.DynamicExecute() is scenario


def test_scenario_decorator_rule_is_applied_automatically() -> None:
    feature = Feature.New("checkout")
    rule = feature.NewRule("VIP")

    @EzScenario(rule="VIP")
    def scenario_spec() -> None:
        feature.newScenario("discount")

    scenario_spec()

    assert [item.getName() for item in rule.getScenarios()] == ["discount"]
    assert feature.getDefaultRule().getScenarios() == []


def test_class_level_rule_is_applied_automatically() -> None:
    feature = Feature.New("checkout")
    rule = feature.NewRule("VIP")

    @EzRule("VIP")
    class RuleSpec:
        @EzScenario
        def scenario_spec(self) -> None:
            feature.newScenario("discount")

    RuleSpec().scenario_spec()

    assert [item.getName() for item in rule.getScenarios()] == ["discount"]
