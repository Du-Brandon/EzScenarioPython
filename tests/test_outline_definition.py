import pytest

from ezspec import Feature, OutlineDefinition, normalize_examples
from ezspec.runtime_context import rule_scope


def test_definition_is_new_unregistered_and_has_the_fluent_dsl():
    feature = Feature.New("math")
    first = feature.defineScenarioOutline("sum", "description")
    second = feature.defineScenarioOutline("sum", "description")
    assert first is not second
    assert isinstance(first, OutlineDefinition)
    assert first.rule is feature.getDefaultRule()
    assert feature.getDefaultRule().getScenarios() == []

    callback = lambda env: None
    assert first.Given("given", callback).When("when", True, callback).Then("then", callback) is first
    assert first.And("and", callback).But("but", callback) is first
    assert first.ThenSuccess(callback).ThenFailure("failure", callback) is first
    assert [step.getName() for step in first.steps()] == [
        "Given", "When", "Then", "And", "But", "Then success", "Then failure"
    ]
    assert first.getName() == "sum"
    assert first.getDescription() == "description"
    assert second.steps() == ()
    assert not hasattr(first, "Execute")
    assert not hasattr(first, "WithExamples")


def test_build_case_keeps_row_index_and_isolates_internal_runtime_state():
    feature = Feature.New("math")
    definition = feature.defineScenarioOutline("sum").Given(
        "value <value> $number", lambda env: env.put("seen", env.gets("value"))
    )
    case = normalize_examples("| value |\n| 1 |\n| 2 |").cases[1]
    first = definition.build_case(case)
    second = definition.build_case(case)

    assert first is not second
    assert first.getScenarioOutline() is definition
    assert first.isFromScenarioOutline()
    assert first.getIndex() == 1
    assert first.getEnvironment().getExecutionCount() == 2
    assert first.getEnvironment().getInput().get("value") == "2"
    assert first.getEnvironment() is not second.getEnvironment()
    assert first.steps()[0] is not second.steps()[0]
    assert first.steps()[0] is not definition.steps()[0]
    assert first.steps()[0].description() == "value <2> $number"
    first.Execute()
    assert first.getEnvironment().gets("seen") == "2"
    assert second.getEnvironment().get("seen") is None
    assert first.steps()[0].getResult().isSuccess()
    assert second.steps()[0].getResult().isPending()
    assert second.getEnvironment().getArgs() == ()
    assert second.getEnvironment().getHistoricalArgs() == ()


def test_named_rule_background_is_cloned_with_shallow_user_values():
    feature = Feature.New("feature")
    rule = feature.NewRule("named")
    shared: list[int] = []
    rule.getBackground().getEnvironment().put("shared", shared)
    definition = feature.defineScenarioOutline("case").withRule(rule)
    definition.Then("check", lambda env: env.get("shared").append(1))
    case = normalize_examples("| value |\n| A |").cases[0]
    first = definition.build_case(case)
    second = definition.build_case(case)
    assert definition.rule is rule
    assert rule.getScenarios() == []
    assert first.getEnvironment() is not second.getEnvironment()
    assert first.getEnvironment().get("shared") is shared
    assert second.getEnvironment().get("shared") is shared
    first.Execute()
    assert shared == [1]


def test_definition_uses_decorator_rule_context_when_present():
    feature = Feature.New("feature")
    rule = feature.NewRule("VIP")
    with rule_scope("VIP"):
        definition = feature.defineScenarioOutline("case")
    assert definition.rule is rule
    assert rule.getScenarios() == []


@pytest.mark.parametrize("callback_kind", ["coroutine", "generator", "async_generator"])
def test_new_definition_rejects_lazy_callback_without_changing_legacy_dsl(callback_kind):
    async def coroutine(env):
        return None

    def generator(env):
        yield None

    async def async_generator(env):
        yield None

    callback = {
        "coroutine": coroutine,
        "generator": generator,
        "async_generator": async_generator,
    }[callback_kind]
    feature = Feature.New("feature")
    with pytest.raises(TypeError, match="synchronous"):
        feature.defineScenarioOutline("case").Given("async", callback)
    legacy = feature.newScenarioOutline("legacy").Given("async", callback)
    assert legacy.steps()[0].getCallback() is callback


@pytest.mark.parametrize(
    "callback_kind",
    [
        "async_callable",
        "returns_awaitable",
        "generator_callable",
        "returns_generator",
        "async_generator_callable",
        "returns_async_generator",
    ],
)
def test_new_runtime_rejects_lazy_callback_result(callback_kind):
    called = []

    async def operation():
        called.append("coroutine")
        assert False, "a lazy callback body must not silently pass"

    def generator():
        called.append("generator")
        assert False, "a lazy callback body must not silently pass"
        yield None

    async def async_generator():
        called.append("async generator")
        assert False, "a lazy callback body must not silently pass"
        yield None

    class AsyncCallable:
        async def __call__(self, env):
            await operation()

    class GeneratorCallable:
        def __call__(self, env):
            yield from generator()

    class AsyncGeneratorCallable:
        async def __call__(self, env):
            async for value in async_generator():
                yield value

    def returns_awaitable(env):
        return operation()

    def returns_generator(env):
        return generator()

    def returns_async_generator(env):
        return async_generator()

    callback = {
        "async_callable": AsyncCallable(),
        "returns_awaitable": returns_awaitable,
        "generator_callable": GeneratorCallable(),
        "returns_generator": returns_generator,
        "async_generator_callable": AsyncGeneratorCallable(),
        "returns_async_generator": returns_async_generator,
    }[callback_kind]
    definition = Feature.New("feature").defineScenarioOutline("case").Then(
        "must fail", callback
    )
    runtime = definition.build_case(normalize_examples("| value |\n| 1 |").cases[0])

    with pytest.raises(TypeError, match="synchronous"):
        runtime.Execute()
    assert runtime.steps()[0].getResult().isFailure()
    assert called == []


def test_no_examples_on_legacy_outline_stays_noop():
    feature = Feature.New("feature")
    called = []
    feature.newScenarioOutline("legacy").Then("step", lambda env: called.append(1)).Execute()
    assert called == []
