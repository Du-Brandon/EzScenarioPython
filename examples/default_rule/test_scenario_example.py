"""Port of ezspec-sample's default-rule Scenario example.

Adapted from example/defaultrule/ScenarioExample.java for Python and pytest.
See NOTICE and docs/SOURCE_PROVENANCE.md for source and project attribution.
"""

from ezspec import EzFeature, EzScenario, Feature, ScenarioEnvironment


@EzFeature
class ScenarioExample:
    feature = Feature.New("Scenario example")

    @EzScenario
    def scenario_example_with_default_rule(self) -> None:
        def remember_tax_excluded_price(env: ScenarioEnvironment) -> None:
            assert env.hasArgument()
            assert len(env.getArgs()) == 1
            assert env.getArgs()[0].value() == "20000"
            assert env.getArg(0) == "20000"
            env.put("tax excluded price", env.getArgi(0))

        def remember_vat_rate(env: ScenarioEnvironment) -> None:
            assert len(env.getArgs()) == 1
            assert env.getArg("VAT") == "0.05"
            assert env.getArgs()[0].key() == "VAT"
            env.put("vat rate", env.getArgd("VAT"))

        def calculate_tax_included_price(env: ScenarioEnvironment) -> None:
            price = env.get("tax excluded price") * (1 + env.get("vat rate"))
            env.put("tax included price", price)

        def verify_total_price(env: ScenarioEnvironment) -> None:
            assert env.getArgi("total_price") == env.get("tax included price")

        (
            self.feature.newScenario()
            .Given(
                "the tax excluded price of a computer is $20000",
                remember_tax_excluded_price,
            )
            .And("the VAT rate is ${VAT=0.05}", remember_vat_rate)
            .When("I buy the computer", calculate_tax_included_price)
            .Then("I need to pay ${total_price:21,000}", verify_total_price)
            .Execute()
        )
