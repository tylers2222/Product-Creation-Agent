from dataclasses import dataclass

@dataclass(frozen=True)
class AgentConfig:
    """
    Configuration for an agent - prompts, models, tool requirements.
    Store jsonB  in the database and bind to this model
    """
    name: str
    model: str
    temperature: float
    system_prompt: str | None
    tools: list

    @classmethod
    def build_agent_config(cls, name: str,
        model: str, temperature: float, tools: list, system_prompt: str | None = None):
        """Class method to build an agent"""
        cls.name = name,
        cls.model = model,
        cls.temperature = temperature,
        cls.tools = tools
        if system_prompt is not None:
          cls.system_prompt = system_prompt