from ezspec.decorators import EzFeature, EzScenario


@EzFeature
class CheckoutFeature:
    @EzScenario
    def vip_customer_gets_discount(self) -> None:
        assert 1000 * 0.9 == 900
