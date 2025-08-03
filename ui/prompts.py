"""
Centralized Prompt Management System
Manages AI model-specific prompts and common prompts.
"""

from typing import Dict, Any, Optional
from enum import Enum
import json
import os
import logging

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported AI model types"""
    OPENAI = "openai"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"
    CLAUDE = "claude"
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
                    "You are a powerful AI assistant that collaborates with users to achieve their goals. "
                    "You have access to various MCP tools for real-time data and operations. "
                    "Always respond in Korean unless requested otherwise."
                ),
                
                "ocr_prompt": "Extract all text from image accurately. Format: ## Text\n[content]\n## Structure\n[layout]",
                
                "tool_selection": (
                    "**TOOL USAGE DECISION:**\n"
                    "- If user mentions 'tool', 'use', 'search', 'find', 'get' = YES\n"
                    "- If user requests data, files, external operations = YES\n"
                    "- If user mentions specific tool names from available list = YES\n"
                    "- For general knowledge, conversations, explanations = NO\n\n"
                    "**SCHEMA COMPLIANCE MANDATORY:**\n"
                    "- ALWAYS use EXACT parameter names from tool schema\n"
                    "- Include ALL required parameters - check schema carefully\n"
                    "- Follow parameter types and formats exactly\n"
                    "- Verify JSON syntax: proper quotes, commas, brackets\n"
                    "- If tool fails with parameter error, check schema and retry\n\n"
                    "**When in doubt about tool usage, choose YES**"
                ),
                
                "error_handling": (
                    "When tools fail: analyze error carefully, try alternative approaches, "
                    "provide helpful explanation, suggest manual alternatives when appropriate."
                ),
                
                "response_format": (
                    "**ALWAYS format output for maximum readability using Markdown:**\n"
                    "- Use code blocks with language tags for code snippets\n"
                    "- Use headers, tables, bullet lists for clarity\n"
                    "- Highlight file paths, commands, function names with inline code formatting\n"
                    "- Structure information clearly with relevant details"
                )
            },
            
            # OpenAI: Function calling optimized
            ModelType.OPENAI.value: {
                "system_enhancement": (
                    "OpenAI model with advanced function calling capabilities. "
                    "Use parallel calls when beneficial. Optimize tokens while maintaining quality."
                ),
                
                "agent_system": (
                    "**TOOL CALLING RULES:**\n"
                    "- Follow tool schemas exactly with all required parameters\n"
                    "- Use EXACT parameter names from schema (check spelling carefully)\n"
                    "- Include ALL required parameters in function call\n"
                    "- Never output Action and Final Answer together\n"
                    "- Format: Either \"Action: [tool]\" OR \"Final Answer: [response]\"\n"
                    "- Use tools proactively when solution is evident\n"
                    "- Always use proper markdown formatting in responses"
                )
            },
            
            # Google: ReAct pattern optimized
            ModelType.GOOGLE.value: {
                "system_enhancement": (
                    "Gemini model with multimodal capabilities and strong reasoning. "
                    "Use ReAct pattern for systematic tool usage. Be proactive in tool selection."
                ),
                
                "agent_system": (
                    "**STEP 1 - Tool Use:**\n"
                    "Thought: [reasoning]\n"
                    "Action: [exact_tool_name]\n"
                    "Action Input: [json_params]\n\n"
                    "**STEP 2 - After Observation:**\n"
                    "Thought: [analyze the observation result]\n"
                    "Final Answer: [Korean response based on observation]\n\n"
                    "**CRITICAL:** Never skip Observation. Never mix steps."
                )
            },
            
            # Perplexity: Research focused with strict MCP usage
            ModelType.PERPLEXITY.value: {
                "system_enhancement": (
                    "Perplexity research model focused on accuracy and fact-checking. "
                    "Always use MCP tools proactively for comprehensive information gathering."
                ),
                
                "agent_system": (
                    "**CRITICAL: SCHEMA COMPLIANCE MANDATORY**\n\n"
                    "**EXACT FORMAT:**\n"
                    "Thought: [Analyze what information is needed]\n"
                    "Action: [exact_tool_name]\n"
                    "Action Input: {\"param\": \"value\"}\n\n"
                    "(System provides Observation)\n\n"
                    "Thought: [Analyze Observation data thoroughly]\n"
                    "Final Answer: [Korean response based ONLY on Observation]\n\n"
                    "**SCHEMA COMPLIANCE (MANDATORY):**\n"
                    "- CHECK TOOL SCHEMA: Verify EXACT parameter names before use\n"
                    "- USE EXACT PARAMETER NAMES: Never modify parameter names from schema\n"
                    "- INCLUDE ALL REQUIRED PARAMETERS: Missing parameters cause validation errors\n"
                    "- CORRECT DATA TYPES: Match expected parameter types exactly\n"
                    "- VALID JSON FORMAT: Proper JSON syntax with correct quotes\n"
                    "- IF PARAMETER ERROR: Check schema and retry with correct parameters\n\n"
                    "**ANALYSIS REQUIREMENTS:**\n"
                    "- Read ENTIRE Observation data\n"
                    "- Extract specific details, numbers, names\n"
                    "- Base response EXCLUSIVELY on tool results\n"
                    "- Never add external knowledge"
                ),
                
                "react_template": (
                    "You are an expert data analyst. Follow tool schemas exactly.\n\n"
                    "**SCHEMA COMPLIANCE MANDATORY:**\n"
                    "- Use EXACT parameter names from tool schema\n"
                    "- Include ALL required parameters\n"
                    "- Match parameter types exactly\n"
                    "- Use valid JSON format\n\n"
                    "**FORMAT:**\n"
                    "Thought: [What information is needed]\n"
                    "Action: [exact_tool_name]\n"
                    "Action Input: {{\"param\": \"value\"}}\n\n"
                    "Thought: [Analyze Observation data]\n"
                    "Final Answer: [Korean response based on Observation]\n\n"
                    "Tools: {tools}\n"
                    "Tool names: {tool_names}\n\n"
                    "Question: {input}\n"
                    "Thought:{agent_scratchpad}"
                )
            },
            
            # Claude: Thoughtful reasoning
            ModelType.CLAUDE.value: {
                "system_enhancement": (
                    "Claude model with strong reasoning capabilities. Provide thoughtful, well-reasoned responses. "
                    "Consider ethical implications and be proactive in tool usage when beneficial."
                ),
                
                "agent_system": (
                    "**TOOL CALLING APPROACH**:\n"
                    "- Follow tool schemas exactly with all required parameters\n"
                    "- Use EXACT parameter names from schema (verify spelling)\n"
                    "- Include ALL required parameters in tool calls\n"
                    "- Use clear structured thinking and standard agent format\n"
                    "- Be proactive: prefer autonomous tool use when solution is evident\n"
                    "- Maintain helpful approach while considering safety implications\n"
                    "- Format responses clearly using markdown for maximum readability"
                )
            }
        }
    
    def get_system_prompt(self, model_type: str) -> str:
        """Generate concise system prompt"""
        common = self._prompts[ModelType.COMMON.value]["system_base"]
        model_specific = self._prompts.get(model_type, {}).get("system_enhancement", "")
        
        return f"{common}\n\n{model_specific}".strip()
    
    def get_tool_prompt(self, model_type: str) -> str:
        """Generate tool usage prompt"""
        return self._prompts[ModelType.COMMON.value]["tool_selection"]
    
    def get_agent_prompt(self, model_type: str) -> str:
        """Get model-specific agent system prompt"""
        return self._prompts.get(model_type, {}).get("agent_system", "")
    
    def get_react_template(self, model_type: str) -> str:
        """Get ReAct template for agent creation"""
        return self._prompts.get(model_type, {}).get("react_template", "")
    
    def get_tool_decision_prompt(self, model_type: str, user_input: str, available_tools: list) -> str:
        """Generate tool usage decision prompt"""
        tools_info = "\n".join([f"- {tool.name}: {getattr(tool, 'description', tool.name)[:80]}" for tool in available_tools[:5]]) if available_tools else "No tools"
        
        return (
            f"User request: \"{user_input}\"\n\n"
            f"Available tools:\n{tools_info}\n\n"
            f"{self._prompts[ModelType.COMMON.value]['tool_selection']}\n\n"
            "Answer: YES or NO only."
        )
    
    def get_ocr_prompt(self) -> str:
        """Return OCR prompt"""
        return self._prompts.get(ModelType.COMMON.value, {}).get("ocr_prompt", "Extract all text from this image accurately.")
    
    def get_complete_output_prompt(self) -> str:
        """Return complete output prompt for multi-page data"""
        return self.get_prompt("common", "complete_output")
    
    def get_agent_system_prompt(self, model_type: str) -> str:
        """Return agent system prompt (alias for get_agent_prompt)"""
        return self.get_agent_prompt(model_type)
    
    def get_error_handling_prompt(self) -> str:
        """Return error handling prompt"""
        return self._prompts[ModelType.COMMON.value]["error_handling"]
    
    def get_response_format_prompt(self) -> str:
        """Return response format prompt"""
        return self._prompts[ModelType.COMMON.value]["response_format"]
    
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
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self._prompts, f, ensure_ascii=False, indent=2)
    
    def load_prompts_from_file(self, file_path: str):
        """Load prompts from file"""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self._prompts = json.load(f)
    
    def get_prompt(self, category: str, key: str) -> str:
        """Query prompt by category and key"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'prompt_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_prompts = json.load(f)
                    if category in file_prompts and key in file_prompts[category]:
                        return file_prompts[category][key]
            
            if category in self._prompts and key in self._prompts[category]:
                return self._prompts[category][key]
            
            logger.warning(f"Prompt not found: {category}.{key}")
            return ""
            
        except Exception as e:
            logger.error(f"Prompt query error: {e}")
            return ""
    
    def get_prompt_for_model(self, model_type: str, prompt_type: str = "system") -> str:
        """Get prompt for specific model and type"""
        if prompt_type == "system":
            return self.get_system_prompt(model_type)
        elif prompt_type == "agent":
            return self.get_agent_prompt(model_type)
        elif prompt_type == "tool":
            return self.get_tool_prompt(model_type)
        elif prompt_type == "full":
            return self.get_full_prompt(model_type)
        else:
            return self.get_custom_prompt(model_type, prompt_type) or ""
    

    
    def get_full_prompt(self, model_type: str) -> str:
        """Generate complete prompt"""
        parts = [
            self.get_system_prompt(model_type),
            self.get_tool_prompt(model_type),
            self._prompts[ModelType.COMMON.value]["error_handling"],
            self._prompts[ModelType.COMMON.value]["response_format"]
        ]
        
        return "\n\n".join(filter(None, parts))
    

    
    def get_provider_from_model(self, model_name: str) -> str:
        """Extract provider from model name"""
        model_name_lower = model_name.lower()
        if "gpt" in model_name_lower or "openai" in model_name_lower:
            return ModelType.OPENAI.value
        elif "gemini" in model_name_lower or "google" in model_name_lower:
            return ModelType.GOOGLE.value
        elif "sonar" in model_name_lower or "perplexity" in model_name_lower or "r1" in model_name_lower:
            return ModelType.PERPLEXITY.value
        elif "claude" in model_name_lower:
            return ModelType.CLAUDE.value
        else:
            return ModelType.OPENAI.value  # Default value
    
    def update_prompt(self, model_type: str, prompt_key: str, prompt_text: str):
        """Update prompt (runtime)"""
        if model_type not in self._prompts:
            self._prompts[model_type] = {}
        self._prompts[model_type][prompt_key] = prompt_text
    
    def save_prompts_to_file(self, file_path: str):
        """Save prompts to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self._prompts, f, ensure_ascii=False, indent=2)
    
    def load_prompts_from_file(self, file_path: str):
        """Load prompts from file"""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self._prompts = json.load(f)
    
    def get_prompt(self, category: str, key: str) -> str:
        """Query prompt by category and key"""
        try:
            # First try to load from file
            config_path = os.path.join(os.path.dirname(__file__), 'prompt_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_prompts = json.load(f)
                    if category in file_prompts and key in file_prompts[category]:
                        return file_prompts[category][key]
            
            # If not in file, query from memory
            if category in self._prompts and key in self._prompts[category]:
                return self._prompts[category][key]
            
            logger.warning(f"Prompt not found: {category}.{key}")
            return ""
            
        except Exception as e:
            logger.error(f"Prompt query error: {e}")
            return ""


# Global prompt manager instance
prompt_manager = PromptManager()


# Convenience functions
def get_system_prompt(model_type: str) -> str:
    """Query system prompt"""
    return prompt_manager.get_system_prompt(model_type)


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