from typing import Callable, Any, Type
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =========================
# Pydantic v1/v2 Compatibility Helpers
# =========================

def model_to_dict(m: BaseModel) -> dict:
    """Convert a Pydantic model instance to a Python dict, compatible with v1/v2."""
    if hasattr(m, "model_dump"):  # v2
        return m.model_dump()
    return m.dict()

def model_schema(cls: Type[BaseModel]) -> dict:
    """Get JSON schema for a Pydantic model class, compatible with v1/v2."""
    if hasattr(cls, "model_json_schema"):  # v2
        return cls.model_json_schema()
    return cls.schema()  # v1




# =========================
# Core Agent Option
# =========================

class AgentOption:
    """
    Wraps a single option/tool for the agent, storing its metadata, output schema, and callable.
    """
    def __init__(
        self,
        option_name: str,
        option_intention: str,
        option_output_model: Type[BaseModel],
        option_callable: Callable[..., Any]
    ):
        if not callable(option_callable):
            raise TypeError("option_callable must be callable")

        self.option_name = option_name
        self.option_intention = option_intention
        self.option_output_model_cls = option_output_model
        self.option_output_model_schema = model_schema(option_output_model).get("properties", {})
        self.option_callable = option_callable

    def __call__(self, *args, **kwargs) -> dict:
        raw_result = self.option_callable(*args, **kwargs)

        if isinstance(raw_result, BaseModel):
            raw_result = model_to_dict(raw_result)

        return raw_result



