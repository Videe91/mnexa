from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Generation:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    response_id: str | None


class OpenAIResponsesModel:
    """
    Thin real-model adapter.
    The experiment owns the prompts.
    MNEXA itself remains model-independent.
    """

    def __init__(
        self,
        model: str,
    ):
        from openai import OpenAI

        self.name = model
        self._client = OpenAI()

    def generate(
        self,
        prompt: str,
    ) -> Generation:
        response = self._client.responses.create(
            model=self.name,
            input=prompt,
        )

        usage = getattr(
            response,
            "usage",
            None,
        )

        return Generation(
            text=response.output_text,
            input_tokens=getattr(
                usage,
                "input_tokens",
                None,
            ),
            output_tokens=getattr(
                usage,
                "output_tokens",
                None,
            ),
            response_id=getattr(
                response,
                "id",
                None,
            ),
        )


class SentenceTransformerEmbedder:
    """
    Local semantic retrieval.
    The embedding model is separate from the reasoning model
    and does not perform reasoning.
    """

    def __init__(
        self,
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
    ):
        from sentence_transformers import (
            SentenceTransformer,
        )

        self.name = model_name
        self._model = SentenceTransformer(
            model_name
        )

    def embed(
        self,
        text: str,
    ):
        return self._model.encode(
            text,
            normalize_embeddings=True,
        ).tolist()


class WordMeter:
    """
    Temporary seed measurement convention.
    This is NOT the final ADR-0015 measurement profile.
    It is sufficient for exploratory Seed Growth 001.
    """

    name = "word-meter-v1"

    def count(
        self,
        text: str,
    ) -> int:
        return len(
            text.split()
        )
