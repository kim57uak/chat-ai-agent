"""
Centralized Prompt Management System
Manages AI model-specific prompts and common prompts.
"""

from typing import Dict, Any, Optional
from enum import Enum
import json
import os
from core.logging import get_logger
from datetime import datetime

logger = get_logger("prompts")


class ModelType(Enum):
    """Supported AI model types"""

    OPENAI = "openai"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"
    CLAUDE = "claude"
    POLLINATIONS = "pollinations"
    OPENROUTER = "openrouter"
    COMMON = "common"


class PromptManager:
    """Centralized prompt management class"""

    def __init__(self):
        self._prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Dict[str, str]]:
        """Load optimized prompt configuration"""
        return {
            # Common base prompts
            ModelType.COMMON.value: {
                "system_base": (
                    "You are an AI assistant with access to external tools. "
                    "Solve problems systematically with clear reasoning. "
                    "Core principles: "
                    "1) Understand user intent and clarify if needed. "
                    "2) Use available knowledge first, tools for external/real-time data. "
                    "3) Provide clear, actionable answers. "
                    "Always respond in the user's language (Korean→Korean, English→English)."
                ),
                "context_awareness": (
                    "Maintain conversation context: "
                    "Reference previous messages when user says 'that', 'it', 'there'. "
                    "Track topic changes and adapt accordingly. "
                    "Infer missing information from conversation history when reasonable."
                ),
                "response_tone": "Be helpful and concise. Avoid unnecessary verbosity.",
                "emoji_usage": "Use emojis appropriately to enhance readability and user experience. Don't overuse them.",
                "tool_usage": (
                    "Use tools for real-time data, external information, or system operations. "
                    "CRITICAL: Follow inputSchema exactly - use exact function names, parameter names, and data types. "
                    "For multiple tools: execute sequentially if dependent, in parallel if independent. "
                    "Wait for tool results before providing final answer."
                ),
                "formatting": "Use markdown formatting for readability. Use emojis to enhance structure. Code blocks: plain text only, no HTML.",
                "code_rules": "Code blocks: plain text only, no HTML tags/entities.",
                "mermaid_rules": "Diagrams: ```mermaid\n[code]\n```. English only, plain arrows (-->). Mindmap: use 'mindmap' + root((text)), NOT flowchart. ERD: UPPERCASE entities, crow's foot notation, essential attributes only (no FK).",
                "agent_base": "Wait for tool results before final answer. Use exact function names and parameter schemas from tool descriptions.",
                "ask_mode": "Provide comprehensive, well-structured answers with examples when helpful.",
                "react_format": "Execute tools internally. Show only final results to users.",
                "json_format": "Return valid JSON in markdown code blocks only.",
                "execution_rules": "Follow inputSchema precisely - exact function names, parameter names, and data types are mandatory.",
            },
            # OpenAI: Native function calling
            ModelType.OPENAI.value: {
                "system_enhancement": "Uses native OpenAI function calling. Supports parallel tool execution.",
                "agent_system": "Execute tools using OpenAI's function calling API. Present final answers with markdown formatting.",
            },
            # Google: ReAct pattern with model-specific handling
            ModelType.GOOGLE.value: {
                "system_enhancement": "Gemini with multimodal reasoning. Pro models: strict format. Flash models: flexible.",
                "agent_system": "Execute tools using ReAct pattern. Present final answers only, hide intermediate steps.",
            },
            # Perplexity: Research-focused
            ModelType.PERPLEXITY.value: {
                "system_enhancement": "Research-focused model. Prioritize accuracy and cite sources.",
                "react_template": "Thought: [analyze] Action: [tool] Final Answer: [response] Question: {input} Thought:{agent_scratchpad}",
            },
            # Claude: Proactive tool usage with data analysis
            ModelType.CLAUDE.value: {
                "system_enhancement": "Claude with native tool use. Proactive tool selection and comprehensive data analysis.",
                "agent_system": "Execute tools using Claude's tool use API. Analyze all data thoroughly and present in tables when appropriate.",
            },
            # Pollinations: Strict ReAct pattern required
            ModelType.POLLINATIONS.value: {
                "system_enhancement": "Free AI model requiring explicit ReAct format. Use tools for all real-time information.",
                "agent_system": (
                    "Pollinations ReAct Rules:\n"
                    "- Use tools for real-time data (news, weather, sports, current events)\n"
                    "- Use tools for search, file operations, database queries, API calls\n"
                    "- Follow strict ReAct format (see react_template)\n"
                    "- Final Answer: use markdown formatting (headers, lists, tables, bold, emojis)\n"
                    "- Provide comprehensive, detailed responses"
                ),
                "image_generation": (
                    "Image Generation:\n"
                    "- Generate high-quality images from text descriptions\n"
                    "- Focus on detailed and creative visual content"
                ),
                "react_template": (
                    "STRICT FORMAT:\n"
                    "Thought: [brief analysis]\n"
                    "Action: exact_tool_name\n"
                    'Action Input: {{"param": "value"}}\n'
                    "OR\n"
                    "Final Answer: [response]\n\n"
                    "Question: {input}\n"
                    "Thought:{agent_scratchpad}"
                ),
                "tool_decision": "Analyze context to determine if tools would provide better results.",
            },
            # OpenRouter: Advanced AI models
            ModelType.OPENROUTER.value: {
                "system_enhancement": "Advanced AI models via OpenRouter. Flexible tool integration.",
            },
        }

    def get_system_prompt(self, model_type: str, use_tools: bool = True) -> str:
        """Generate system prompt with mode-specific enhancements"""
        from datetime import timezone, timedelta

        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        current_date = f"{now.month:02d}/{now.day:02d}/{now.year}"
        date_info = f" Today is {current_date} (UTC+9)"

        common = self._prompts[ModelType.COMMON.value]
        model_specific = self._prompts.get(model_type, {}).get("system_enhancement", "")

        if use_tools:
            # Agent mode system prompt
            parts = [
                common["system_base"],
                date_info,
                common["context_awareness"],
                common["response_tone"],
                common["emoji_usage"],
                common["tool_usage"],
                common["formatting"],
                common["code_rules"],
                common["mermaid_rules"],
                common["agent_base"],
                common["react_format"],
                common["execution_rules"],
                model_specific,
            ]
        else:
            # Ask mode system prompt
            parts = [
                common["system_base"],
                date_info,
                common["context_awareness"],
                common["response_tone"],
                common["emoji_usage"],
                common["formatting"],
                common["mermaid_rules"],
                common["ask_mode"],
                model_specific,
            ]

        return "\n\n".join(filter(None, parts)).strip()

    def get_tool_prompt(self, model_type: str) -> str:
        """Generate tool usage prompt"""
        return self._prompts[ModelType.COMMON.value]["tool_usage"]

    def get_agent_prompt(self, model_type: str) -> str:
        """Get model-specific agent system prompt"""
        return self._prompts.get(model_type, {}).get("agent_system", "")

    def get_react_template(self, model_type: str) -> str:
        """Get ReAct template for agent creation"""
        return self._prompts.get(model_type, {}).get("react_template", "")

    def get_tool_decision_prompt(
        self, model_type: str, user_input: str, available_tools: list
    ) -> str:
        """Generate tool usage decision prompt"""
        tools_info = (
            "\n".join(
                [
                    f"- {tool.name}: {getattr(tool, 'description', tool.name)[:80]}"
                    for tool in available_tools[:5]
                ]
            )
            if available_tools
            else "No tools"
        )

        return (
            f'User request: "{user_input}"\n\n'
            f"Available tools:\n{tools_info}\n\n"
            f"{self._prompts[ModelType.COMMON.value]['tool_usage']}\n\n"
            "Answer: YES or NO only."
        )

    def get_ocr_prompt(self) -> str:
        """Return OCR prompt"""
        return "Extract all text from this image accurately."

    def get_complete_output_prompt(self) -> str:
        """Return complete output prompt for multi-page data"""
        return "Provide complete output for all data."

    def get_agent_system_prompt(self, model_type: str) -> str:
        """Return agent system prompt (alias for get_agent_prompt)"""
        return self.get_agent_prompt(model_type)

    def get_error_handling_prompt(self) -> str:
        """Return error handling prompt"""
        return self._prompts[ModelType.COMMON.value].get("error_handling", "")

    def get_response_format_prompt(self) -> str:
        """Return response format prompt"""
        return self._prompts[ModelType.COMMON.value]["formatting"]

    def get_conversation_prompt(self, model_type: str) -> str:
        """Return conversation style prompt (for backward compatibility)"""
        return ""

    def get_custom_prompt(self, model_type: str, prompt_key: str) -> Optional[str]:
        """Query custom prompt"""
        return self._prompts.get(model_type, {}).get(prompt_key)

    def update_prompt(self, model_type: str, prompt_key: str, prompt_text: str):
        """Update prompt (runtime)"""
        if model_type not in self._prompts:
            self._prompts[model_type] = {}
        self._prompts[model_type][prompt_key] = prompt_text

    def save_prompts_to_file(self, file_path: str):
        """Save prompts to file"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self._prompts, f, ensure_ascii=False, indent=2)

    def load_prompts_from_file(self, file_path: str):
        """Load prompts from file"""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                self._prompts = json.load(f)

    def get_prompt(self, category: str, key: str) -> str:
        """Query prompt by category and key from internal prompts only"""
        try:
            if category in self._prompts and key in self._prompts[category]:
                return self._prompts[category][key]

            logger.warning(f"Prompt not found: {category}.{key}")
            return ""

        except Exception as e:
            logger.error(f"Prompt query error: {e}")
            return ""

    def get_prompt_for_model(
        self, model_type: str, prompt_type: str = "system", use_tools: bool = True
    ) -> str:
        """Get prompt for specific model and type"""
        if prompt_type == "system":
            return self.get_system_prompt(model_type, use_tools)
        elif prompt_type == "agent":
            return self.get_agent_prompt(model_type)
        elif prompt_type == "tool":
            return self.get_tool_prompt(model_type)
        elif prompt_type == "full":
            return self.get_full_prompt(model_type)
        else:
            return self.get_custom_prompt(model_type, prompt_type) or ""

    def get_full_prompt(self, model_type: str) -> str:
        """Generate complete prompt with all sections"""
        common = self._prompts[ModelType.COMMON.value]
        model_specific = self._prompts.get(model_type, {})

        parts = [
            self.get_system_prompt(model_type),
            self.get_tool_prompt(model_type),
            common["formatting"],
            common["code_rules"],
            common["mermaid_rules"],
            common["execution_rules"],
            model_specific.get("system_enhancement", ""),
        ]

        return "\n\n".join(filter(None, parts))

    def get_provider_from_model(self, model_name: str) -> str:
        """Extract provider from model name"""
        model_name_lower = model_name.lower()
        if "gpt" in model_name_lower or "openai" in model_name_lower:
            return ModelType.OPENAI.value
        elif "gemini" in model_name_lower or "google" in model_name_lower:
            return ModelType.GOOGLE.value
        elif (
            "sonar" in model_name_lower
            or "perplexity" in model_name_lower
            or "r1" in model_name_lower
        ):
            return ModelType.PERPLEXITY.value
        elif "claude" in model_name_lower:
            return ModelType.CLAUDE.value
        elif (
            model_name_lower.startswith("pollinations-")
            or "pollinations" in model_name_lower
        ):
            return ModelType.POLLINATIONS.value
        elif any(
            keyword in model_name_lower
            for keyword in [
                "deepseek/",
                "qwen/",
                "meta-llama/",
                "nvidia/",
                "moonshotai/",
            ]
        ):
            return ModelType.OPENROUTER.value
        else:
            return ModelType.OPENAI.value  # Default value


# Global prompt manager instance
prompt_manager = PromptManager()


# Convenience functions
def get_system_prompt(model_type: str, use_tools: bool = True) -> str:
    """Query system prompt"""
    return prompt_manager.get_system_prompt(model_type, use_tools)


def get_agent_prompt(model_type: str) -> str:
    return prompt_manager.get_agent_prompt(model_type)


def get_full_prompt(model_type: str) -> str:
    return prompt_manager.get_full_prompt(model_type)


def get_tool_prompt(model_type: str) -> str:
    return prompt_manager.get_tool_prompt(model_type)


def update_prompt(model_type: str, prompt_key: str, prompt_text: str):
    prompt_manager.update_prompt(model_type, prompt_key, prompt_text)


def get_prompt_for_model(model_type: str, prompt_type: str = "system") -> str:
    return prompt_manager.get_prompt_for_model(model_type, prompt_type)
