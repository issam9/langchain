"""Wrapper around Cohere APIs."""
import os
from typing import Any, Dict, List, Mapping, Optional

from pydantic import BaseModel, Extra, root_validator

from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens


class Cohere(LLM, BaseModel):
    """Wrapper around Cohere large language models.

    To use, you should have the ``cohere`` python package installed, and the
    environment variable ``COHERE_API_KEY`` set with your API key, or pass
    it as a named parameter to the constructor.

    Example:
        .. code-block:: python

            from langchain import Cohere
            cohere = Cohere(model="gptd-instruct-tft", cohere_api_key="my-api-key")
    """

    client: Any  #: :meta private:
    model: Optional[str] = None
    """Model name to use."""

    max_tokens: int = 256
    """Denotes the number of tokens to predict per generation."""

    temperature: float = 0.75
    """A non-negative float that tunes the degree of randomness in generation."""

    k: int = 0
    """Number of most likely tokens to consider at each step."""

    p: int = 1
    """Total probability mass of tokens to consider at each step."""

    frequency_penalty: int = 0
    """Penalizes repeated tokens according to frequency."""

    presence_penalty: int = 0
    """Penalizes repeated tokens."""

    cohere_api_key: Optional[str] = os.environ.get("COHERE_API_KEY")

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        cohere_api_key = values.get("cohere_api_key")

        if cohere_api_key is None or cohere_api_key == "":
            raise ValueError(
                "Did not find Cohere API key, please add an environment variable"
                " `COHERE_API_KEY` which contains it, or pass `cohere_api_key`"
                " as a named parameter."
            )
        try:
            import cohere

            values["client"] = cohere.Client(cohere_api_key)
        except ImportError:
            raise ValueError(
                "Could not import cohere python package. "
                "Please it install it with `pip install cohere`."
            )
        return values

    @property
    def _default_params(self) -> Mapping[str, Any]:
        """Get the default parameters for calling Cohere API."""
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "k": self.k,
            "p": self.p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {**{"model": self.model}, **self._default_params}

    def __call__(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Call out to Cohere's generate endpoint.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string generated by the model.

        Example:
            .. code-block:: python

                response = cohere("Tell me a joke.")
        """
        response = self.client.generate(
            model=self.model, prompt=prompt, stop_sequences=stop, **self._default_params
        )
        text = response.generations[0].text
        # If stop tokens are provided, Cohere's endpoint returns them.
        # In order to make this consistent with other endpoints, we strip them.
        if stop is not None:
            text = enforce_stop_tokens(text, stop)
        return text
