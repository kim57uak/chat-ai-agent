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
        """Load prompt configuration"""
        return {
            # Common prompts
            ModelType.COMMON.value: {
                "system_base": (
                    "You are an AI assistant that can use various tools through MCP (Model Context Protocol) servers.\n\n"
                    "Key capabilities:\n"
                    "- Access to 15+ different MCP servers with various tools\n"
                    "- Dynamic tool detection and intelligent tool selection\n"
                    "- Real-time streaming responses\n"
                    "- Conversation history management\n\n"
                    "Guidelines:\n"
                    "- Always respond in Korean unless specifically requested otherwise\n"
                    "- Use tools when they can provide better or more accurate information\n"
                    "- Be concise and helpful in your responses\n"
                    "- Maintain conversation context"
                ),
                
                "ocr_prompt": (
                    "Extract all text from this image with complete accuracy (OCR).\n\n"
                    "**Required Tasks:**\n"
                    "1. **Complete Text Extraction**: Extract all Korean, English, numbers, and symbols without omission\n"
                    "2. **Structure Analysis**: Identify document structure including tables, lists, headings, paragraphs\n"
                    "3. **Layout Information**: Describe text position, size, and arrangement relationships\n"
                    "4. **Accurate Transcription**: Record all characters precisely without errors\n\n"
                    "**Response Format:**\n"
                    "## 📄 Extracted Text\n"
                    "[List all text accurately]\n\n"
                    "## 📋 Document Structure\n"
                    "[Describe structure including tables, lists, headings]\n\n"
                    "**Important**: Extract ALL readable text from the image completely without any omissions."
                ),
                
                "tool_decision_base": (
                    "Analyze if this request requires using external tools to provide accurate information.\n\n"
                    "Use tools for:\n"
                    "- Real-time data queries (databases, web searches, file systems)\n"
                    "- Specific information lookups that I don't have in my knowledge\n"
                    "- External API calls or system operations\n"
                    "- Current/live information requests\n"
                    "- Data processing or calculations requiring external resources\n\n"
                    "Do NOT use tools for:\n"
                    "- General knowledge questions I can answer\n"
                    "- Simple conversations or greetings\n"
                    "- Creative writing or brainstorming\n"
                    "- Explanations of concepts I know\n"
                    "- Opinion-based discussions\n\n"
                    "Answer: YES or NO only."
                ),
                
                "tool_selection": (
                    "When selecting tools, consider:\n"
                    "1. User's specific request and context\n"
                    "2. Available tools and their capabilities\n"
                    "3. Most efficient way to get accurate information\n"
                    "4. Avoid unnecessary tool calls\n\n"
                    "Available tool categories:\n"
                    "- Web search and content retrieval\n"
                    "- Database queries (MySQL)\n"
                    "- Travel services (Hanatour API)\n"
                    "- Office tools (Excel, PowerPoint)\n"
                    "- Development tools (Bitbucket, Jira, Confluence)\n"
                    "- Email management (Gmail)\n"
                    "- Location services (OpenStreetMap)\n"
                    "- Document processing"
                ),
                
                "error_handling": (
                    "When tool calls fail:\n"
                    "1. Analyze the error message carefully\n"
                    "2. Try alternative approaches if available\n"
                    "3. Provide helpful explanation to user\n"
                    "4. Suggest manual alternatives when appropriate"
                ),
                
                "response_format": (
                    "Response formatting:\n"
                    "- Use markdown for better readability\n"
                    "- Structure information clearly\n"
                    "- Include relevant details without overwhelming\n"
                    "- Provide actionable next steps when appropriate"
                )
            },
            
            # OpenAI model-specific prompts
            ModelType.OPENAI.value: {
                "system_enhancement": (
                    "You are powered by OpenAI's language model with enhanced tool-calling capabilities.\n\n"
                    "Specific instructions for OpenAI models:\n"
                    "- Utilize function calling efficiently\n"
                    "- Handle parallel tool calls when beneficial\n"
                    "- Maintain conversation flow with streaming responses\n"
                    "- Optimize token usage while preserving quality"
                ),
                
                "tool_calling": (
                    "For tool execution:\n"
                    "- Use structured function calls with proper parameters\n"
                    "- Handle parameter mapping intelligently\n"
                    "- Generate smart defaults for missing required parameters\n"
                    "- Validate inputs before making calls"
                ),
                
                "agent_system": (
                    "**CRITICAL RULES:**\n"
                    "1. NEVER output both Action and Final Answer in the same response\n"
                    "2. If you need to use a tool, output ONLY the Action (no Final Answer)\n"
                    "3. After tool execution, output ONLY the Final Answer (no more Actions)\n"
                    "4. Follow the exact format: either \"Action: [tool_name]\" OR \"Final Answer: [response]\"\n\n"
                    "**OpenAI-specific Instructions:**\n"
                    "- Analyze user requests carefully to select the most appropriate tools\n"
                    "- Use tools to gather current, accurate information when needed\n"
                    "- If multiple tools are needed, use them one at a time\n"
                    "- Focus on providing exactly what the user asked for\n\n"
                    "**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row.\n\n"
                    "**Format Requirements:**\n"
                    "- STRICTLY follow the Action/Final Answer format\n"
                    "- NEVER mix Action and Final Answer in one response"
                ),
                
                "conversation_style": (
                    "OpenAI-specific conversation approach:\n"
                    "- Be direct and informative\n"
                    "- Use technical language appropriately\n"
                    "- Provide code examples when relevant\n"
                    "- Focus on practical solutions"
                )
            },
            
            # Google (Gemini) model-specific prompts
            ModelType.GOOGLE.value: {
                "system_enhancement": (
                    "You are powered by Google's Gemini model with multimodal capabilities.\n\n"
                    "Specific instructions for Gemini:\n"
                    "- Leverage multimodal understanding when applicable\n"
                    "- Handle complex reasoning tasks effectively\n"
                    "- Use ReAct pattern for tool interactions\n"
                    "- Maintain coherent long-form responses"
                ),
                
                "react_pattern": (
                    "For ReAct tool usage:\n"
                    "Thought: Analyze what needs to be done\n"
                    "Action: Select and execute appropriate tool\n"
                    "Observation: Process the tool result\n"
                    "... (repeat as needed)\n"
                    "Final Answer: Provide comprehensive response\n\n"
                    "Always structure your reasoning clearly and maintain logical flow."
                ),
                
                "agent_system": (
                    "**CRITICAL PARSING RULES:**\n"
                    "1. NEVER output both Action and Final Answer in the same response\n"
                    "2. Follow EXACT format: Thought -> Action -> Action Input -> (wait for Observation) -> Thought -> Final Answer\n"
                    "3. Each step must be on a separate line\n"
                    "4. Use EXACT keywords: \"Thought:\", \"Action:\", \"Action Input:\", \"Final Answer:\"\n"
                    "5. Do NOT include \"Observation:\" - it will be added automatically\n\n"
                    "**STRICT FORMAT:**\n"
                    "Thought: [your reasoning]\n"
                    "Action: [exact_tool_name]\n"
                    "Action Input: [input_for_tool]\n\n"
                    "(System will add Observation automatically)\n\n"
                    "Thought: [analyze the observation]\n"
                    "Final Answer: [your response in Korean]\n\n"
                    "**EXAMPLE:**\n"
                    "Question: Show me files in /home\n"
                    "Thought: I need to list directory contents to show the user what files are in /home.\n"
                    "Action: filesystem_list_directory\n"
                    "Action Input: /home\n\n"
                    "(After receiving observation:)\n"
                    "Thought: Now I have the directory listing and can provide a formatted response to the user.\n"
                    "Final Answer: /home 디렉토리에는 다음 파일들이 있습니다: [formatted list]"
                ),
                
                "conversation_style": (
                    "Gemini-specific conversation approach:\n"
                    "- Provide detailed explanations when helpful\n"
                    "- Use examples to illustrate concepts\n"
                    "- Consider multiple perspectives\n"
                    "- Emphasize understanding over quick answers"
                )
            },
            
            # Perplexity model-specific prompts
            ModelType.PERPLEXITY.value: {
                "system_enhancement": (
                    "You are powered by Perplexity's research-focused model.\n\n"
                    "Specific instructions for Perplexity:\n"
                    "- Prioritize accuracy and fact-checking\n"
                    "- Provide source attribution when possible\n"
                    "- Use web search tools effectively\n"
                    "- Maintain research-quality standards"
                ),
                
                "research_approach": (
                    "Research methodology:\n"
                    "1. Gather information from multiple sources\n"
                    "2. Cross-reference facts and data\n"
                    "3. Provide context and background\n"
                    "4. Cite sources when available\n"
                    "5. Acknowledge limitations or uncertainties"
                ),
                
                "mcp_agent_system": (
                    "**HIGHEST PRIORITY INSTRUCTION: ALWAYS USE MCP TOOLS AND FOLLOW EXACT FORMAT**\n\n"
                    "**CRITICAL PARSING RULES:**\n"
                    "1. NEVER output both Action and Final Answer in the same response\n"
                    "2. Each step must be on a separate line with exact keywords\n"
                    "3. Use EXACT format: \"Thought:\", \"Action:\", \"Action Input:\", \"Final Answer:\"\n"
                    "4. Wait for Observation before proceeding to Final Answer\n"
                    "5. ALWAYS END YOUR RESPONSE WITH EITHER AN ACTION OR FINAL ANSWER\n\n"
                    "**IMPORTANT: ONLY SHOW FINAL ANSWER TO THE USER - HIDE ALL THOUGHT PROCESSES**\n\n"
                    "You MUST use available tools for EVERY query and follow the exact format below:\n\n"
                    "Thought: [your reasoning about what to do]\n"
                    "Action: [exact tool name from available tools]\n"
                    "Action Input: {\"param\": \"value\"}\n\n"
                    "(Wait for Observation to be provided by system)\n\n"
                    "Thought: [your reasoning about the result]\n"
                    "Final Answer: [your response based ONLY on tool results]\n\n"
                    "**CRITICAL RULES FOR TOOL USAGE:**\n"
                    "1. **ALWAYS USE TOOLS**: For EVERY query, you MUST use at least one tool. NEVER skip tool usage.\n"
                    "2. **EXACT TOOL NAMES**: Use the EXACT tool names provided to you, without modification.\n"
                    "3. **PROPER JSON FORMAT**: Always use valid JSON format for Action Input.\n"
                    "4. **FOLLOW FORMAT EXACTLY**: Always use the Thought/Action/Action Input format.\n"
                    "5. **PARAMETER TYPE ACCURACY**: Carefully examine each MCP function's parameter types and requirements.\n\n"
                    "**TOOL RESULTS ABSOLUTE PRIORITY**:\n"
                    "- Use ONLY the results from MCP tools to formulate your response.\n"
                    "- DO NOT add any information beyond what the tool results provide.\n"
                    "- NEVER include your own knowledge, inferences, or general information.\n\n"
                    "**ABSOLUTELY PROHIBITED**:\n"
                    "- Adding any information beyond tool results\n"
                    "- Using your own knowledge or inferences\n"
                    "- NEVER respond without using tools"
                ),
                
                "conversation_style": (
                    "Perplexity-specific conversation approach:\n"
                    "- Focus on factual accuracy\n"
                    "- Provide comprehensive coverage\n"
                    "- Include relevant background context\n"
                    "- Maintain scholarly tone while being accessible"
                )
            },
            
            # Claude model-specific prompts
            ModelType.CLAUDE.value: {
                "system_enhancement": (
                    "You are powered by Anthropic's Claude model with strong reasoning capabilities.\n\n"
                    "Specific instructions for Claude:\n"
                    "- Provide thoughtful, well-reasoned responses\n"
                    "- Consider ethical implications when relevant\n"
                    "- Use clear, structured thinking\n"
                    "- Maintain helpful and harmless approach"
                ),
                
                "conversation_style": (
                    "Claude-specific conversation approach:\n"
                    "- Be thoughtful and considerate\n"
                    "- Provide balanced perspectives\n"
                    "- Use clear explanations\n"
                    "- Focus on being helpful while being safe"
                )
            }
        }
    
    def get_system_prompt(self, model_type: str, include_common: bool = True) -> str:
        """Generate system prompt"""
        prompts = []
        
        # Add common prompts
        if include_common:
            common_prompts = self._prompts.get(ModelType.COMMON.value, {})
            prompts.append(common_prompts.get("system_base", ""))
        
        # Add model-specific prompts
        model_prompts = self._prompts.get(model_type, {})
        if "system_enhancement" in model_prompts:
            prompts.append(model_prompts["system_enhancement"])
        
        return "\n\n".join(filter(None, prompts))
    
    def get_tool_prompt(self, model_type: str) -> str:
        """Generate tool usage prompt"""
        prompts = []
        
        # Common tool selection guide
        common_prompts = self._prompts.get(ModelType.COMMON.value, {})
        prompts.append(common_prompts.get("tool_selection", ""))
        
        # Model-specific tool usage guide
        model_prompts = self._prompts.get(model_type, {})
        if "tool_calling" in model_prompts:
            prompts.append(model_prompts["tool_calling"])
        elif "react_pattern" in model_prompts:
            prompts.append(model_prompts["react_pattern"])
        elif "research_approach" in model_prompts:
            prompts.append(model_prompts["research_approach"])
        
        return "\n\n".join(filter(None, prompts))
    
    def get_conversation_prompt(self, model_type: str) -> str:
        """Generate conversation style prompt"""
        model_prompts = self._prompts.get(model_type, {})
        return model_prompts.get("conversation_style", "")
    
    def get_error_handling_prompt(self) -> str:
        """Return error handling prompt"""
        common_prompts = self._prompts.get(ModelType.COMMON.value, {})
        return common_prompts.get("error_handling", "")
    
    def get_response_format_prompt(self) -> str:
        """Return response format prompt"""
        common_prompts = self._prompts.get(ModelType.COMMON.value, {})
        return common_prompts.get("response_format", "")
    
    def get_full_prompt(self, model_type: str, include_tools: bool = True) -> str:
        """Generate full prompt"""
        prompts = []
        
        # System prompt
        prompts.append(self.get_system_prompt(model_type))
        
        # Tool usage prompt
        if include_tools:
            prompts.append(self.get_tool_prompt(model_type))
        
        # Conversation style
        conversation_style = self.get_conversation_prompt(model_type)
        if conversation_style:
            prompts.append(conversation_style)
        
        # Error handling
        prompts.append(self.get_error_handling_prompt())
        
        # Response format
        prompts.append(self.get_response_format_prompt())
        
        return "\n\n".join(filter(None, prompts))
    
    def get_custom_prompt(self, model_type: str, prompt_key: str) -> Optional[str]:
        """Query custom prompt"""
        model_prompts = self._prompts.get(model_type, {})
        return model_prompts.get(prompt_key)
    
    def get_ocr_prompt(self) -> str:
        """Return common OCR prompt"""
        common_prompts = self._prompts.get(ModelType.COMMON.value, {})
        return common_prompts.get("ocr_prompt", "")
    
    def get_tool_decision_prompt(self, model_type: str, user_input: str, available_tools: list) -> str:
        """Generate tool usage decision prompt"""
        common_prompts = self._prompts.get(ModelType.COMMON.value, {})
        base_decision = common_prompts.get("tool_decision_base", "")
        
        tools_info = "\n".join([f"- {tool.name}: {getattr(tool, 'description', tool.name)[:80]}" for tool in available_tools[:5]]) if available_tools else "No available tools"
        
        return (
            f"User request: \"{user_input}\"\n\n"
            f"Available tools:\n{tools_info}\n\n"
            f"{base_decision}"
        )
    
    def get_agent_system_prompt(self, model_type: str) -> str:
        """Return agent system prompt"""
        model_prompts = self._prompts.get(model_type, {})
        return model_prompts.get("agent_system", model_prompts.get("mcp_agent_system", ""))
    
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


def get_tool_prompt(model_type: str) -> str:
    """Query tool usage prompt"""
    return prompt_manager.get_tool_prompt(model_type)


def get_full_prompt(model_type: str) -> str:
    """Query full prompt"""
    return prompt_manager.get_full_prompt(model_type)


def update_prompt(model_type: str, prompt_key: str, prompt_text: str):
    """Update prompt"""
    prompt_manager.update_prompt(model_type, prompt_key, prompt_text)