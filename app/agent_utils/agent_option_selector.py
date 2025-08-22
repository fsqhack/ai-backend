from typing import List, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from app.agent_utils.agent_option import AgentOption
from app.llms.openai import LangchainOpenaiJsonEngine

# Load environment variables
load_dotenv()


# =========================
# Independent Option Selection Models
# =========================

class OptionAndSubqueryIndependent(BaseModel):
    """
    Single mapping from option index to the subquery that should be passed to it.
    """
    option_index: int = Field(title="Option Index", description="The index of the chosen option from the list.")
    subquery: str = Field(title="Subquery", description="The specific subquery to send to this option. This subquery should be detailed and specific to the option's intention.")


class OptionAndSubqueryIndependentList(BaseModel):
    """
    A minimal list of <option_index, subquery> pairs needed to answer the user query.
    """
    options: List[OptionAndSubqueryIndependent] = Field(
        title="Options",
        description="List of <option_index, subquery> pairs to execute independently."
    )






# =========================
# Independent Option Selector
# =========================

class AgentIndependentOptionSelector:
    """
    Breaks down a user query into multiple independent subqueries for different options.
    """
    def __init__(self, option_list: Dict[int, AgentOption], model_name: str = "gpt-3.5-turbo", temperature: float = 0.2):
        self.option_list = option_list
        self.model_name = model_name
        self.temperature = temperature

        options_description = "\n".join(
            f"{idx} | {opt.option_name} | {opt.option_intention}"
            for idx, opt in option_list.items()
        )

        self.prompt_template = f"""
You are a task decomposition assistant. Your job is to break a user's query into independent subtasks.

Here is the list of available tools/options:
Option Index | Option Name | Option Intention
---------------------------------------------
{options_description}
---------------------------------------------

**Instructions for response:**
1. Select only the options necessary to answer the query.
2. For each selected option, write the subquery that should be passed to it.
3. The subquery should be detailed and specific to the option's intention.
4. The subquery must match the intention of the associated option. The option should be able to execute the subquery without any additional context.
5. You may reuse the same option multiple times with different subqueries if required.
6. Return the output as a JSON object matching the provided schema.

The user's query:
{{user_query}}
""".strip()

        self.break_down_engine = LangchainOpenaiJsonEngine(
            model_name=self.model_name,
            sampleBaseModel=OptionAndSubqueryIndependentList,
            systemPromptText="You are an assistant that selects relevant independent options and subqueries for a given user request.",
            temperature=self.temperature
        )

    def __call__(self, user_query: str) -> List[dict]:
        prompt = self.prompt_template.format(user_query=user_query)
        result_pydantic = self.break_down_engine.run(prompt)
        return result_pydantic[0]['options']