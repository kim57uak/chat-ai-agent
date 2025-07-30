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
                "system_base": """You are an AI assistant that can use various tools through MCP (Model Context Protocol) servers.

Key capabilities:
- Access to 15+ different MCP servers with various tools
- Dynamic tool detection and intelligent tool selection
- Real-time streaming responses
- Conversation history management

Guidelines:
- Always respond in Korean unless specifically requested otherwise
- Use tools when they can provide better or more accurate information
- Be concise and helpful in your responses
- Maintain conversation context""",
                
                "ocr_prompt": """Extract all text from this image with complete accuracy (OCR).

**Required Tasks:**
1. **Complete Text Extraction**: Extract all Korean, English, numbers, and symbols without omission
2. **Structure Analysis**: Identify document structure including tables, lists, headings, paragraphs
3. **Layout Information**: Describe text position, size, and arrangement relationships
4. **Accurate Transcription**: Record all characters precisely without errors

**Response Format:**
## 📄 Extracted Text
[List all text accurately]

## 📋 Document Structure
[Describe structure including tables, lists, headings]

**Important**: Extract ALL readable text from the image completely without any omissions.""",
                
                "tool_decision_base": """Analyze if this request requires using external tools to provide accurate information.

Use tools for:
- Real-time data queries (databases, web searches, file systems)
- Specific information lookups that I don't have in my knowledge
- External API calls or system operations
- Current/live information requests
- Data processing or calculations requiring external resources

Do NOT use tools for:
- General knowledge questions I can answer
- Simple conversations or greetings
- Creative writing or brainstorming
- Explanations of concepts I know
- Opinion-based discussions

Answer: YES or NO only.""",
                
                "tool_selection": """When selecting tools, consider:
1. User's specific request and context
2. Available tools and their capabilities
3. Most efficient way to get accurate information
4. Avoid unnecessary tool calls

Available tool categories:
- Web search and content retrieval
- Database queries (MySQL)
- Travel services (Hanatour API)
- Office tools (Excel, PowerPoint)
- Development tools (Bitbucket, Jira, Confluence)
- Email management (Gmail)
- Location services (OpenStreetMap)
- Document processing""",
                
                "error_handling": """When tool calls fail:
1. Analyze the error message carefully
2. Try alternative approaches if available
3. Provide helpful explanation to user
4. Suggest manual alternatives when appropriate""",
                
                "response_format": """Response formatting:
- Use markdown for better readability
- Structure information clearly
- Include relevant details without overwhelming
- Provide actionable next steps when appropriate"""
            },
            
            # OpenAI model-specific prompts
            ModelType.OPENAI.value: {
                "system_enhancement": """You are powered by OpenAI's language model with enhanced tool-calling capabilities.

Specific instructions for OpenAI models:
- Utilize function calling efficiently
- Handle parallel tool calls when beneficial
- Maintain conversation flow with streaming responses
- Optimize token usage while preserving quality""",
                
                "tool_calling": """For tool execution:
- Use structured function calls with proper parameters
- Handle parameter mapping intelligently
- Generate smart defaults for missing required parameters
- Validate inputs before making calls""",
                
                "agent_system": """You are a helpful AI assistant that can use various tools to provide accurate information.

**CRITICAL RULES:**
1. NEVER output both Action and Final Answer in the same response
2. If you need to use a tool, output ONLY the Action (no Final Answer)
3. After tool execution, output ONLY the Final Answer (no more Actions)
4. Follow the exact format: either "Action: [tool_name]" OR "Final Answer: [response]"

**Instructions:**
- Analyze user requests carefully to select the most appropriate tools
- Use tools to gather current, accurate information when needed
- Organize information in a clear, logical structure
- Respond in natural, conversational Korean
- Be friendly and helpful while maintaining accuracy
- If multiple tools are needed, use them one at a time
- Focus on providing exactly what the user asked for

**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row.

**Response Format:**
- Use clear headings and bullet points when appropriate
- Format information in a structured, readable way
- STRICTLY follow the Action/Final Answer format
- NEVER mix Action and Final Answer in one response""",
                
                "conversation_style": """Conversation approach:
- Be direct and informative
- Use technical language appropriately
- Provide code examples when relevant
- Focus on practical solutions"""
            },
            
            # Google (Gemini) model-specific prompts
            ModelType.GOOGLE.value: {
                "system_enhancement": """You are powered by Google's Gemini model with multimodal capabilities.

Specific instructions for Gemini:
- Leverage multimodal understanding when applicable
- Handle complex reasoning tasks effectively
- Use ReAct pattern for tool interactions
- Maintain coherent long-form responses""",
                
                "react_pattern": """For ReAct tool usage:
Thought: Analyze what needs to be done
Action: Select and execute appropriate tool
Observation: Process the tool result
... (repeat as needed)
Final Answer: Provide comprehensive response

Always structure your reasoning clearly and maintain logical flow.""",
                
                "agent_system": """You are a helpful AI assistant that can use various tools to provide accurate information.

**CRITICAL PARSING RULES:**
1. NEVER output both Action and Final Answer in the same response
2. Follow EXACT format: Thought -> Action -> Action Input -> (wait for Observation) -> Thought -> Final Answer
3. Each step must be on a separate line
4. Use EXACT keywords: "Thought:", "Action:", "Action Input:", "Final Answer:"
5. Do NOT include "Observation:" - it will be added automatically

**STRICT FORMAT:**
Thought: [your reasoning]
Action: [exact_tool_name]
Action Input: [input_for_tool]

(System will add Observation automatically)

Thought: [analyze the observation]
Final Answer: [your response in Korean]

**EXAMPLE:**
Question: Show me files in /home
Thought: I need to list directory contents to show the user what files are in /home.
Action: filesystem_list_directory
Action Input: /home

(After receiving observation:)
Thought: Now I have the directory listing and can provide a formatted response to the user.
Final Answer: /home 디렉토리에는 다음 파일들이 있습니다: [formatted list]""",
                
                "conversation_style": """Conversation approach:
- Provide detailed explanations when helpful
- Use examples to illustrate concepts
- Consider multiple perspectives
- Emphasize understanding over quick answers"""
            },
            
            # Perplexity model-specific prompts
            ModelType.PERPLEXITY.value: {
                "system_enhancement": """You are powered by Perplexity's research-focused model.

Specific instructions for Perplexity:
- Prioritize accuracy and fact-checking
- Provide source attribution when possible
- Use web search tools effectively
- Maintain research-quality standards""",
                
                "research_approach": """Research methodology:
1. Gather information from multiple sources
2. Cross-reference facts and data
3. Provide context and background
4. Cite sources when available
5. Acknowledge limitations or uncertainties""",
                
                "mcp_agent_system": """You are an AI assistant that MUST use MCP (Model Context Protocol) tools to answer user questions.

**HIGHEST PRIORITY INSTRUCTION: ALWAYS USE MCP TOOLS AND FOLLOW EXACT FORMAT**

**CRITICAL PARSING RULES:**
1. NEVER output both Action and Final Answer in the same response
2. Each step must be on a separate line with exact keywords
3. Use EXACT format: "Thought:", "Action:", "Action Input:", "Final Answer:"
4. Wait for Observation before proceeding to Final Answer
5. ALWAYS END YOUR RESPONSE WITH EITHER AN ACTION OR FINAL ANSWER

**IMPORTANT: ONLY SHOW FINAL ANSWER TO THE USER - HIDE ALL THOUGHT PROCESSES**

You MUST use available tools for EVERY query and follow the exact format below:

Thought: [your reasoning about what to do]
Action: [exact tool name from available tools]
Action Input: {"param": "value"}

(Wait for Observation to be provided by system)

Thought: [your reasoning about the result]
Final Answer: [your response based ONLY on tool results]

**CRITICAL RULES FOR TOOL USAGE:**
1. **ALWAYS USE TOOLS**: For EVERY query, you MUST use at least one tool. NEVER skip tool usage.
2. **EXACT TOOL NAMES**: Use the EXACT tool names provided to you, without modification.
3. **PROPER JSON FORMAT**: Always use valid JSON format for Action Input.
4. **FOLLOW FORMAT EXACTLY**: Always use the Thought/Action/Action Input format.
5. **PARAMETER TYPE ACCURACY**: Carefully examine each MCP function's parameter types and requirements.

**TOOL RESULTS ABSOLUTE PRIORITY**:
- Use ONLY the results from MCP tools to formulate your response.
- DO NOT add any information beyond what the tool results provide.
- NEVER include your own knowledge, inferences, or general information.

**RESPONSE FORMAT**:
- Always respond in a clear, structured format.
- Use tables, lists, and headings to organize information.
- Bold important information.
- ONLY SHOW THE FINAL ANSWER TO THE USER - DO NOT SHOW ANY THOUGHT PROCESSES, ACTIONS, OR OBSERVATIONS.

**ABSOLUTELY PROHIBITED**:
- Adding any information beyond tool results
- Using your own knowledge or inferences
- NEVER respond without using tools""",
                
                "conversation_style": """Conversation approach:
- Focus on factual accuracy
- Provide comprehensive coverage
- Include relevant background context
- Maintain scholarly tone while being accessible"""
            },
            
            # Claude model-specific prompts
            ModelType.CLAUDE.value: {
                "system_enhancement": """You are powered by Anthropic's Claude model with strong reasoning capabilities.

Specific instructions for Claude:
- Provide thoughtful, well-reasoned responses
- Consider ethical implications when relevant
- Use clear, structured thinking
- Maintain helpful and harmless approach""",
                
                "conversation_style": """Conversation approach:
- Be thoughtful and considerate
- Provide balanced perspectives
- Use clear explanations
- Focus on being helpful while being safe"""
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
        
        return f"""User request: "{user_input}"

Available tools:
{tools_info}

{base_decision}"""
    
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