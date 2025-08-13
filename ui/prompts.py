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
                    "**LANGUAGE RULE: Respond naturally in the same language the user uses.** "
                    "Simply match the user's language without mentioning language detection or translation. "
                    "Be conversational and natural - avoid formal acknowledgments about language preferences."
                ),
                
                "ocr_prompt": "Extract all text from this image accurately and completely. Maintain the original language of the text. Format your response as: ## Extracted Text\n[content]\n## Document Structure\n[layout description]",
                
                "tool_selection": (
                    "**SMART TOOL USAGE DECISION:**\n\n"
                    "**PRIMARY QUESTION:** Does this request need data or actions I cannot provide myself?\n\n"
                    "**USE TOOLS when request involves:**\n"
                    "- External systems (Jira, databases, APIs, files, websites)\n"
                    "- Current/real-time information (news, weather, stock prices, today's data)\n"
                    "- Specific data retrieval (search, find, get, check, look up)\n"
                    "- User's personal/work data (my issues, assigned to me, my files)\n"
                    "- Time-sensitive information (today, yesterday, recent, latest)\n"
                    "- Actions on external services (create, update, send, download)\n\n"
                    "**NO TOOLS when request is:**\n"
                    "- General knowledge I already know\n"
                    "- Explanations, concepts, how-to guides\n"
                    "- Creative writing, brainstorming, analysis\n"
                    "- Code examples, tutorials, best practices\n\n"
                    "**DECISION RULE:** When in doubt, USE TOOLS to provide better user value."
                ),
                
                "schema_compliance": (
                    "**CRITICAL: EXACT SCHEMA COMPLIANCE MANDATORY:**\n"
                    "- NEVER modify parameter names (productAreaCode ≠ productAreaCd)\n"
                    "- Use EXACT parameter names from tool schema\n"
                    "- Include ALL required parameters\n"
                    "- Match parameter types exactly\n"
                    "- Use valid JSON format\n"
                    "- If parameter error occurs, check schema and retry\n"
                    "- Wait for Observation before Final Answer\n"
                    "- Base responses ONLY on tool results when tools are used"
                ),
                
                "table_formatting": (
                    "**TABLE FORMAT GUIDANCE:**\n"
                    "- Use table format ONLY when it significantly improves user understanding\n"
                    "- Tables are helpful for: comparing data, showing structured information, multiple items with same attributes\n"
                    "- For simple data or single items, use regular text format\n"
                    "- When using tables: proper markdown format with | separators and --- header dividers\n"
                    "- Prioritize readability and user comprehension over rigid formatting"
                ),
                
                "error_handling": (
                    "When tools fail: analyze error carefully, try alternative approaches, "
                    "provide helpful explanation, suggest manual alternatives when appropriate."
                ),
                
                "response_format": (
                    "**ALWAYS format output for maximum readability using Markdown:**\n"
                    "- Use code blocks with language tags for code snippets\n"
                    "- Use headers (# ## ###), tables, bullet lists for clarity\n"
                    "- For tables: Use proper markdown syntax with | separators and --- header dividers\n"
                    "- Use **bold** for emphasis and *italic* for secondary emphasis\n"
                    "- Highlight file paths, commands, function names with `inline code` formatting\n"
                    "- Structure information clearly with relevant details\n"
                    "- Always use proper markdown formatting - the system will render it correctly"
                ),
                
                "agent_base": (
                    "**COMMON AGENT RULES:**\n"
                    "- Follow tool schemas exactly with all required parameters\n"
                    "- Use EXACT parameter names from schema\n"
                    "- Include ALL required parameters in function call\n"
                    "- Wait for Observation before Final Answer\n"
                    "- Use tools proactively when solution is evident"
                ),
                
                "react_format": (
                    "**STANDARD REACT FORMAT:**\n"
                    "Thought: [reasoning]\n"
                    "Action: exact_tool_name\n"
                    "Action Input: {\"param\": \"value\"}\n"
                    "Observation: [system response]\n"
                    "Final Answer: [natural response]"
                )
            },
            
            # OpenAI: Function calling optimized
            ModelType.OPENAI.value: {
                "system_enhancement": "OpenAI model with advanced function calling capabilities. Use parallel calls when beneficial.",
                "agent_system": "Format: Either \"Action: [tool]\" OR \"Final Answer: [response]\". Never output both together."
            },
            
            # Google: ReAct pattern optimized
            ModelType.GOOGLE.value: {
                "system_enhancement": "Gemini model with multimodal reasoning. Execute requests with precision using systematic tool usage.",
                "agent_system": "**CRITICAL: Respond ONLY with Final Answer. Do NOT show Thought, Action, or Observation steps to user. Execute tools internally and provide only the final result.**"
            },
            
            # Perplexity: Research focused
            ModelType.PERPLEXITY.value: {
                "system_enhancement": "Perplexity research model. Use MCP tools proactively for comprehensive information gathering. Prioritize factual accuracy.",
                "agent_system": "Base response EXCLUSIVELY on tool results. Extract specific details, numbers, names from Observation data.",
                "react_template": (
                    "You are an expert data analyst. Follow tool schemas exactly.\n\n"
                    "Tools: {tools}\nTool names: {tool_names}\n\nQuestion: {input}\nThought:{agent_scratchpad}"
                )
            },
            
            # Claude: Proactive tool usage
            ModelType.CLAUDE.value: {
                "system_enhancement": "Claude model with strong reasoning. USE TOOLS IMMEDIATELY when user requests data, search, or external information.",
                "agent_system": "ALWAYS use tools when user asks for data, search, or information. Tools provide better answers than generic knowledge."
            }
        }
    
    def get_system_prompt(self, model_type: str) -> str:
        """Generate concise system prompt with current date and tone guidelines"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        date_info = f"Current date: {current_date}"
        
        tone_guidelines = (
            "**Communication Style Guidelines:**\n"
            "- Use a warm, friendly, and helpful tone in all responses\n"
            "- Incorporate relevant emojis to enhance readability and visual appeal\n"
            "- Structure responses clearly with proper formatting for better accessibility\n"
            "- Be encouraging and supportive while maintaining professionalism\n"
            "- Always respond in the same language as the user's input"
        )
        
        common = self._prompts[ModelType.COMMON.value]["system_base"]
        model_specific = self._prompts.get(model_type, {}).get("system_enhancement", "")
        
        return f"{common}\n\n{date_info}\n\n{tone_guidelines}\n\n{model_specific}".strip()
    
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
            f"{self._prompts[ModelType.COMMON.value]['schema_compliance']}\n\n"
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
        """Query prompt by category and key from internal prompts only"""
        try:
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
        """Generate complete prompt with all sections"""
        common = self._prompts[ModelType.COMMON.value]
        parts = [
            self.get_system_prompt(model_type),
            self.get_tool_prompt(model_type),
            common["schema_compliance"],
            common["table_formatting"],
            common["error_handling"],
            common["response_format"]
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