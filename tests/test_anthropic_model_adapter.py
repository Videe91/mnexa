import sys
import types

from model_adapter import (
    Generation,
    AnthropicMessagesModel,
)


def test_anthropic_messages_model_generates_generation(
    monkeypatch,
):
    captured = {}

    class FakeMessages:
        def create(
            self,
            *,
            model,
            max_tokens,
            messages,
        ):
            captured["model"] = model
            captured["max_tokens"] = max_tokens
            captured["messages"] = messages

            return types.SimpleNamespace(
                id="msg_test_123",

                content=[
                    types.SimpleNamespace(
                        type="text",
                        text=(
                            "MODE=EMBER-7\n"
                            "WAIT_MS=137\n"
                            "HEADER=X-Relay:cobalt"
                        ),
                    ),
                ],

                usage=types.SimpleNamespace(
                    input_tokens=42,
                    output_tokens=18,
                ),
            )

    class FakeAnthropicClient:
        def __init__(
            self,
        ):
            self.messages = FakeMessages()

    fake_module = types.SimpleNamespace(
        Anthropic=FakeAnthropicClient,
    )

    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        fake_module,
    )

    model = AnthropicMessagesModel(
        "claude-test-model",
        max_tokens=256,
    )

    result = model.generate(
        "Recover ORCHID-729."
    )

    assert isinstance(
        result,
        Generation,
    )

    assert (
        result.text
        ==
        (
            "MODE=EMBER-7\n"
            "WAIT_MS=137\n"
            "HEADER=X-Relay:cobalt"
        )
    )

    assert (
        result.input_tokens
        ==
        42
    )

    assert (
        result.output_tokens
        ==
        18
    )

    assert (
        result.response_id
        ==
        "msg_test_123"
    )

    assert (
        captured["model"]
        ==
        "claude-test-model"
    )

    assert (
        captured["max_tokens"]
        ==
        256
    )

    assert captured[
        "messages"
    ] == [
        {
            "role": "user",
            "content": (
                "Recover ORCHID-729."
            ),
        }
    ]


def test_anthropic_adapter_joins_multiple_text_blocks(
    monkeypatch,
):
    class FakeMessages:
        def create(
            self,
            **kwargs,
        ):
            return types.SimpleNamespace(
                id="msg_multi",

                content=[
                    types.SimpleNamespace(
                        type="text",
                        text="first",
                    ),

                    types.SimpleNamespace(
                        type="tool_use",
                        text=None,
                    ),

                    types.SimpleNamespace(
                        type="text",
                        text="second",
                    ),
                ],

                usage=types.SimpleNamespace(
                    input_tokens=1,
                    output_tokens=2,
                ),
            )

    class FakeAnthropicClient:
        def __init__(
            self,
        ):
            self.messages = FakeMessages()

    monkeypatch.setitem(
        sys.modules,
        "anthropic",

        types.SimpleNamespace(
            Anthropic=(
                FakeAnthropicClient
            ),
        ),
    )

    model = (
        AnthropicMessagesModel(
            "claude-test-model"
        )
    )

    result = model.generate(
        "hello"
    )

    assert (
        result.text
        ==
        "first\nsecond"
    )
