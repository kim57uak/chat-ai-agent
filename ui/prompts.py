"""
Centralized Prompt Management System
Manages AI model-specific prompts and common prompts.
"""

from typing import Dict, Any, Optional
from enum import Enum
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
                    "You are an AI agent with MCP tool access. "
                    "Respond in user's input language (Korean→Korean, English→English). "
                    "Use emojis appropriately."
                ),
                "tool_usage": (
                    "Intelligently analyze user context to determine if external tools are needed. "
                    "Use tools when the request requires information beyond your training data or capabilities. "
                    "CRITICAL: Follow inputSchema exactly - use exact function names, parameter names, and data types. "
                    "MANDATORY: Validate all parameters match the required schema before calling functions. "
                    "Wait for tool results before answering."
                ),
                "formatting": "Use markdown formatting. Code blocks: plain text only. Organize with emojis.",
                "code_rules": "Code blocks: plain text only, no HTML tags/entities.",
                "mermaid_rules": "For diagrams: ```mermaid\n[code]\n``` format. Use English, plain arrows (-->).",
                "agent_base": "Wait for tool results before final answer. MANDATORY: Use exact function names and parameter schemas as defined in tool descriptions.",
                "ask_mode": "Provide comprehensive answers with examples and clear structure.",
                "react_format": "Execute tools immediately. Show only final results to users.",
                "json_format": "Return valid JSON in markdown code blocks only.",
                "execution_rules": "Understand user intent. Use available info first, tools for external data. CRITICAL: Follow inputSchema precisely - exact function names, parameter names, and data types are mandatory. Validate schema compliance before every function call.",
            },
            # OpenAI: Function calling optimized
            ModelType.OPENAI.value: {
                "system_enhancement": "OpenAI model with function calling. Use parallel calls when beneficial.",
                "agent_system": "Execute tools internally, show only final answers. Use markdown formatting in final answers"
            },
            # Google: ReAct pattern optimized
            ModelType.GOOGLE.value: {
                "system_enhancement": "Gemini model with multimodal reasoning.",
                "agent_system": "Show final answers only, not intermediate steps.",
            },
            # Perplexity: Research focused
            ModelType.PERPLEXITY.value: {
                "system_enhancement": "Research model with tool integration.",
                "react_template": "Thought: [analyze] Action: [tool] Final Answer: [response] Question: {input} Thought:{agent_scratchpad}",
            },
            # Claude: Proactive tool usage
            ModelType.CLAUDE.value: {
                "system_enhancement": "Claude model with reasoning capabilities.",
            },
            # Pollinations: Free AI models
            ModelType.POLLINATIONS.value: {
                "system_enhancement": "Ultra-high-performance Pollinations AI model with intelligent context analysis and comprehensive tool integration. MANDATORY: Use tools for ALL real-time information requests including sports results, news, weather, current events.",
                "agent_system": (
                    "**POLLINATIONS Exclusive Rules:**\n"
                    "- MANDATORY: Use tools for real-time information (sports, news, weather, current events)\n"
                    "- Always use tools when users request search, data retrieval, file operations, database queries, API calls\n"
                    "- Show thought process and final answers to users\n"
                    "- CRITICAL: Final Answer MUST use proper markdown formatting (headers, lists, tables, bold, emojis)\n"
                    "- CRITICAL: Final Answer MUST be comprehensive and detailed, never short or incomplete\n"
                ),
                "image_generation": (
                    "**Image Generation:**\n"
                    "- Generate high-quality images from text descriptions\n"
                    "- Focus on detailed and creative visual content"
                ),
                "react_template": (
                    "**CRITICAL REACT FORMAT RULES:**\n\n"
                    "**MANDATORY TOOL USAGE:**\n"
                    "- Real-time info requests (sports, news, weather) = ALWAYS use tools\n"
                    "- Keywords '오늘', '현재', '최신', 'today', 'current' = MANDATORY tool usage\n\n"
                    "**MANDATORY STRUCTURE:**\n"
                    "- EVERY response MUST start with 'Thought:'\n"
                    "- After 'Thought:' use either 'Action:' OR 'Final Answer:'\n"
                    "- If using 'Action:', MUST follow with 'Action Input:' on next line\n"
                    "- Use EXACT FULL tool names from available tool list: [{tool_names}]\n"
                    "- Follow exact parameter inputSchemas from tool descriptions\n\n"
                    "**LANGUAGE MATCHING:**\n"
                    "- Korean input = Korean Final Answer\n"
                    "- English input = English Final Answer\n\n"
                    "**FINAL ANSWER REQUIREMENTS:**\n"
                    "- Apply ALL common formatting rules (response_format, readability_enhancement)\n"
                    "- Use proper markdown: headers, lists, tables, bold, emojis\n"
                    "- Provide comprehensive, detailed responses with all tool data\n"
                    "- Never provide short, incomplete answers\n\n"
                    "Question: {input}\n"
                    "Thought: [analyze what information is needed]\n"
                    "Action: [exact_tool_name_from_list]\n"
                    'Action Input: {{"parameter": "value"}}\n'
                    "Observation: [result of the action]\n"
                    "... (repeat as needed)\n"
                    "Thought: I now know the final answer\n"
                    "Final Answer: [comprehensive markdown-formatted response]\n\n"
                    "Available tools:\n{tools}\n\n"
                    "Question: {input}\n"
                    "Thought:{agent_scratchpad}"
                ),
                "tool_decision": "Use contextual understanding to determine when external tools would enhance your response."
            },
            # OpenRouter: Advanced AI models
            ModelType.OPENROUTER.value: {
                "system_enhancement": "OpenRouter AI model with reasoning capabilities.",
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
        elif any(keyword in model_name_lower for keyword in ["deepseek/", "qwen/", "meta-llama/", "nvidia/", "moonshotai/"]):
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
