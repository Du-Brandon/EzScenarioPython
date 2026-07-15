"""A scenario assigned to a user-created Rule."""

from ezspec import EzFeature, EzScenario, Feature, ScenarioEnvironment


TOTAL_PRICE_RULE = "Total price includes tax"

@EzFeature
class ScenarioExample:
    """Equivalent of ezspec-sample's named-rule ScenarioExample."""

    feature = Feature.New("Scenario example")
    feature.NewRule(TOTAL_PRICE_RULE)

    @EzScenario
    def scenario_example_with_user_created_rule(self) -> None:
        (
            self.feature.newScenario()
            .withRule(TOTAL_PRICE_RULE)
            .Given(
                "the tax excluded price of a computer is $20000",
                remember_tax_excluded_price,
            )
            .And("the VAT rate is ${VAT=0.05}", remember_vat_rate)
            .When("I buy the computer", calculate_tax_included_price)
            .Then(
                "I need to pay ${total_price:21,000}",
                verify_tax_included_price,
            )
            .Execute()
        )


def remember_tax_excluded_price(env: ScenarioEnvironment) -> None:
    """Verify and store the positional argument parsed from the Given step."""

    assert env.hasArgument()
    assert len(env.getArgs()) == 1
    assert env.getArgs()[0].value() == "20000"
    assert env.getArg(0) == "20000"

    env.put("tax excluded price", env.getArgi(0))


def remember_vat_rate(env: ScenarioEnvironment) -> None:
    """Verify and store the named argument parsed from the And step."""

    assert len(env.getArgs()) == 1
    assert env.getArg("VAT") == "0.05"
    assert env.getArgs()[0].key() == "VAT"

    env.put("vat rate", env.getArgd("VAT"))


def calculate_tax_included_price(env: ScenarioEnvironment) -> None:
    price = env.get("tax excluded price") * (1 + env.get("vat rate"))
    env.put("tax included price", price)


def verify_tax_included_price(env: ScenarioEnvironment) -> None:
    assert env.getArgi("total_price") == env.get("tax included price")
