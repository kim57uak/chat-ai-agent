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
                    "**LANGUAGE RULE: CRITICAL - ALWAYS respond in the SAME language as the user's input.** "
                    "Korean input → Korean response (한글 입력 → 한글 응답). English input → English response. "
                    "Simply match the user's language without mentioning language detection or translation. "
                    "Be conversational and natural - avoid formal acknowledgments about language preferences."
                ),
                
                "ocr_prompt": "Extract all text from this image accurately and completely. Maintain the original language of the text. Format your response as: ## Extracted Text\n[content]\n## Document Structure\n[layout description]",
                
                "tool_selection": (
                    "**INTELLIGENT TOOL USAGE DECISION:**\n\n"
                    "**CORE PRINCIPLE:** Analyze the user's request and available tools to determine if external capabilities can enhance the response.\n\n"
                    "**USE TOOLS when the request requires capabilities beyond text generation:**\n"
                    "- Creating, generating, or producing content (images, audio, files, documents)\n"
                    "- Accessing external data sources or real-time information\n"
                    "- Performing actions on external systems or services\n"
                    "- Processing, analyzing, or manipulating existing files or data\n"
                    "- Retrieving specific, current, or personalized information\n\n"
                    "**NO TOOLS when the request is:**\n"
                    "- Purely conversational or explanatory\n"
                    "- General knowledge that doesn't require external verification\n"
                    "- Abstract discussions, theories, or conceptual explanations\n\n"
                    "**DECISION PROCESS:**\n"
                    "1. Identify what the user wants to accomplish\n"
                    "2. Check if available tools can fulfill or enhance this request\n"
                    "3. If tools can add value, use them; otherwise, respond directly\n\n"
                    "**KEY INSIGHT:** Tools extend your capabilities - use them when they can provide what text alone cannot."
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
                    "**CRITICAL: ALWAYS use proper Markdown formatting in ALL responses:**\n"
                    "- Headers: Use # ## ### #### for clear hierarchy\n"
                    "- Lists: Use - or * for bullets, 1. 2. 3. for numbered lists\n"
                    "- Emphasis: Use **bold** for important terms, *italic* for emphasis\n"
                    "- Code: Use `inline code` for terms, ```language blocks for code\n"
                    "- **CRITICAL: Code blocks must be CLEAN PLAIN TEXT only:**\n"
                    "  * NO HTML tags: <span>, <div>, <pre>, <code>\n"
                    "  * NO syntax highlighting classes or attributes\n"
                    "  * NO HTML entities: &gt; &lt; &amp; &quot;\n"
                    "  * Example: ```java\nSystem.out.println(\"Hello\");\n```\n"
                    "  * NOT: <div><pre><span class=\"kt\">System</span>...</pre></div>\n"
                    "- Tables: Use | separators with --- header dividers\n"
                    "- Links: Use [text](url) format\n"
                    "- Quotes: Use > for blockquotes\n"
                    "- Separators: Use --- for horizontal rules\n"
                    "- **DIAGRAMS: MANDATORY use ```mermaid code blocks ONLY. NO HTML tags**\n"
                    "- **CRITICAL: In mermaid diagrams, use PLAIN TEXT arrows: --> NOT --&gt;**\n"
                    "- **Math: Use $ for inline math, $$ for block math formulas**\n"
                    "**ABSOLUTE RULE: NEVER generate HTML syntax highlighting. Use ONLY clean plain text in code blocks.**\n"
                    "**For diagrams: Use ONLY ```mermaid\n[diagram code]\n``` format. NO other formatting.**"
                ),
                
                "markdown_standard": (
                    "**MARKDOWN STANDARD COMPLIANCE:**\n"
                    "- Use ONLY standard CommonMark/GitHub Flavored Markdown syntax\n"
                    "- AVOID: Mermaid diagrams, PlantUML, complex LaTeX math formulas\n"
                    "- AVOID: Custom components, shortcodes, platform-specific extensions\n"
                    "- AVOID: Interactive elements, embedded videos, complex HTML\n"
                    "- For diagrams: Use simple ASCII art or describe in text\n"
                    "- For math: Use simple inline notation like x^2 or describe in words\n"
                    "- Stick to: headers, lists, tables, code blocks, links, images, emphasis\n"
                    "**GOAL: Ensure maximum compatibility across all markdown parsers**"
                ),
                
                "readability_enhancement": (
                    "**ENHANCE USER UNDERSTANDING AND READABILITY:**\n"
                    "- Structure information logically with clear sections\n"
                    "- Use visual elements: emojis, bullet points, numbered steps\n"
                    "- Break down complex information into digestible chunks\n"
                    "- Provide examples and practical applications when relevant\n"
                    "- Use consistent formatting patterns throughout responses\n"
                    "- Highlight key points with **bold** or > blockquotes\n"
                    "- Create visual hierarchy with headers and subheaders\n"
                    "- Use tables for comparative or structured data\n"
                    "- Add context and explanations for technical terms"
                ),
                
                "code_block_strict": (
                    "**STRICT CODE BLOCK FORMATTING RULES:**\n"
                    "- Code blocks MUST be clean plain text only\n"
                    "- FORBIDDEN: All HTML tags, classes, spans, divs\n"
                    "- FORBIDDEN: Syntax highlighting markup\n"
                    "- FORBIDDEN: HTML entities (&gt;, &lt;, &amp;, &quot;)\n"
                    "- REQUIRED: Simple ```language\n[clean code]\n``` format\n"
                    "- Line spacing should be normal, not expanded\n"
                    "- Focus on code readability, not visual styling"
                ),
                
                "mermaid_diagram_rule": (
                    "**MERMAID DIAGRAM STRICT RULES (Version 10+ Compatible):**\n"
                    "- When user requests diagrams, flowcharts, sequences, or any visual representation\n"
                    "- ALWAYS respond with PURE mermaid code block format:\n"
                    "```mermaid\n[diagram code here]\n```\n"
                    "- NEVER wrap in HTML tags like <div>, <pre>, <code>\n"
                    "- NEVER add syntax highlighting classes\n"
                    "- NEVER use plain text descriptions instead of mermaid code\n"
                    "- **CRITICAL: Use PLAIN TEXT arrows, NOT HTML entities:**\n"
                    "  * Use --> NOT --&gt;\n"
                    "  * Use --- NOT &#45;&#45;&#45;\n"
                    "  * Use ->> NOT -&gt;&gt;\n"
                    "- **CRITICAL: Use Mermaid version 10+ compatible syntax:**\n"
                    "  * Gantt charts: Use 'gantt' keyword, dateFormat YYYY-MM-DD\n"
                    "  * ER diagrams: Use 'erDiagram' keyword with ||--o{ syntax\n"
                    "  * Flowcharts: Use 'flowchart TD' or 'graph TD'\n"
                    "  * Sequence: Use 'sequenceDiagram' keyword\n"
                    "  * State: Use 'stateDiagram-v2' keyword\n"
                    "- Example formats:\n"
                    "```mermaid\nflowchart TD\n    A[Start] --> B[Process]\n    B --> C[End]\n```\n"
                    "```mermaid\ngantt\n    dateFormat YYYY-MM-DD\n    title Project\n    section Phase\n    Task :2024-01-01, 30d\n```"
                ),
                
                "agent_base": (
                    "**COMMON AGENT RULES:**\n"
                    "- Follow tool schemas exactly with all required parameters\n"
                    "- Use EXACT parameter names from schema\n"
                    "- Include ALL required parameters in function call\n"
                    "- Wait for Observation before Final Answer\n"
                    "- Use tools proactively when solution is evident"
                ),
                
                "ask_mode_enhancement": (
                    "**ASK MODE SPECIFIC RULES:**\n"
                    "- CRITICAL: ALWAYS respond in the SAME language as the user's input (한글 입력 = 한글 응답)\n"
                    "- When tools are not available, provide comprehensive answers using your knowledge\n"
                    "- Give detailed, complete explanations - never leave responses incomplete\n"
                    "- If you mention you will explain something, provide the full explanation immediately\n"
                    "- Structure long answers with clear headings and sections\n"
                    "- Use examples and context to make explanations thorough and helpful\n"
                    "- Aim for informative, educational responses that fully address the user's question"
                ),
                
                "react_format": (
                    "**STANDARD REACT FORMAT:**\n"
                    "Thought: [reasoning]\n"
                    "Action: exact_tool_name\n"
                    "Action Input: {\"param\": \"value\"}\n"
                    "Observation: [system response]\n"
                    "Final Answer: [natural response]"
                ),
                
                "json_output_format": (
                    "**JSON OUTPUT FORMAT:**\n"
                    "Please always return valid JSON fenced inside a markdown code block. Do not output any extra text."
                ),
                
                "common_agent_rules": (
                    "**USER INTENT ANALYSIS:**\n"
                    "- Carefully analyze what the user is actually asking for\n"
                    "- Understand the type of output they expect (comparison, analysis, summary, etc.)\n"
                    "- Consider the context and purpose behind their request\n\n"
                    "**INTELLIGENT EXECUTION:**\n"
                    "- Gather all necessary data to fulfill their specific request\n"
                    "- Use your reasoning to determine when you have sufficient information\n"
                    "- Process and analyze the collected data according to user needs\n"
                    "- Deliver the exact type of result the user requested\n\n"
                    "**TECHNICAL COMPLIANCE:**\n"
                    "- Follow tool schemas exactly with all required parameters\n"
                    "- Use EXACT parameter names from schema\n"
                    "- Wait for Observation before Final Answer\n"
                    "- Extract specific information from tool results"
                ),
                
                "tone_guidelines": (
                    "**Communication Style Guidelines:**\n"
                    "- Use a warm, friendly, and helpful tone in all responses\n"
                    "- Incorporate relevant emojis to enhance readability and visual appeal\n"
                    "- Structure responses clearly with proper formatting for better accessibility\n"
                    "- Be encouraging and supportive while maintaining professionalism\n"
                    "- Always respond in the same language as the user's input"
                )
            },
            
            # OpenAI: Function calling optimized
            ModelType.OPENAI.value: {
                "system_enhancement": "OpenAI model with advanced function calling capabilities. Use parallel calls when beneficial.",
                "agent_system": (
                    "**OPENAI SPECIFIC RULES:**\n"
                    "- ALWAYS provide Final Answer after using tools\n"
                    "- NEVER end with just Action: [tool] - this leaves user hanging\n"
                    "- After tool Observation, IMMEDIATELY provide Final Answer\n"
                    "- Use markdown formatting in Final Answer"
                )
            },
            
            # Google: ReAct pattern optimized
            ModelType.GOOGLE.value: {
                "system_enhancement": "Gemini model with multimodal reasoning. Execute requests with precision using systematic tool usage.",
                "agent_system": "**GEMINI SPECIFIC RULES: Respond ONLY with Final Answer. Do NOT show Thought, Action, or Observation steps to user. Execute tools internally and provide only the final result.**"
            },
            
            # Perplexity: Research focused
            ModelType.PERPLEXITY.value: {
                "system_enhancement": "Perplexity research model with advanced MCP tool integration. ALWAYS use tools when user requests data, search, or external information. Prioritize factual accuracy and comprehensive analysis.",
                "agent_system": (
                    "**PERPLEXITY SPECIFIC RULES:**\n"
                    "- ALWAYS use tools when user asks for: search, data, current info, files, databases, APIs\n"
                    "- Follow EXACT ReAct format: Thought -> Action -> Action Input -> (wait for Observation) -> Final Answer\n"
                    "- Base responses EXCLUSIVELY on tool Observation data\n"
                    "- ALWAYS prefer tool data over your internal knowledge for current information"
                ),
                "react_template": (
                    "You are an expert research analyst with access to comprehensive MCP tools. "
                    "Use tools proactively to gather accurate, current information.\n\n"
                    "**MANDATORY FORMAT:**\n"
                    "Thought: [analyze what information is needed]\n"
                    "Action: [exact_tool_name]\n"
                    "Action Input: {\"param\": \"value\"}\n"
                    "Observation: [system provides tool results]\n"
                    "Final Answer: [comprehensive response based on Observation data]\n\n"
                    "Tools: {tools}\nTool names: {tool_names}\n\nQuestion: {input}\nThought:{agent_scratchpad}"
                ),
                "tool_awareness": (
                    "**PERPLEXITY TOOL AWARENESS:**\n"
                    "- You have access to 15+ MCP tools including: search, databases, files, APIs, Jira, email, travel services\n"
                    "- These tools provide REAL-TIME data that is more accurate than your training data\n"
                    "- ALWAYS prefer tool data over your internal knowledge for current information\n"
                    "- When user asks for specific data, search results, or external information, USE TOOLS IMMEDIATELY\n"
                    "- Tools are your primary source of truth for factual, current information"
                )
            },
            
            # Claude: Proactive tool usage
            ModelType.CLAUDE.value: {
                "system_enhancement": "Claude model with strong reasoning. USE TOOLS IMMEDIATELY when user requests data, search, or external information.",
                "agent_system": "**CLAUDE SPECIFIC RULES: ALWAYS use tools when user asks for data, search, or information. Tools provide better answers than generic knowledge.**"
            },
            
            # Pollinations: Free AI models with context-aware tool usage
            ModelType.POLLINATIONS.value: {
                "system_enhancement": "Pollinations free AI model with intelligent context analysis and comprehensive tool integration.",
                "agent_system": (
                    "**POLLINATIONS SPECIFIC RULES:**\n"
                    "- ALWAYS use tools when user requests: search, data retrieval, file operations, database queries, API calls\n"
                    "- MANDATORY: Use EXACT FULL tool names as shown in tool list - NEVER use shortened names\n"
                    "- Example: Use 'hanatourApi_getBasicCommonCodeByQuery' NOT 'getBasicCommonCodeByQuery'\n"
                    "- CRITICAL: Tool names include prefixes like 'hanatourApi_', 'gmail_', 'excel-stdio_'\n"
                    "- CRITICAL: NEVER end with just 'Thought:' - ALWAYS complete with 'Action:' or 'Final Answer:'\n"
                    "- CRITICAL: Keep Final Answer concise and complete - avoid long explanations that get cut off"
                ),
                "image_generation": (
                    "**IMAGE GENERATION:**\n"
                    "- Generate high-quality images from text descriptions\n"
                    "- Focus on detailed, creative visual content"
                ),
                "react_template": (
                    "**CRITICAL REACT FORMAT RULES:**\n\n"
                    "**MANDATORY STRUCTURE:**\n"
                    "- EVERY response MUST start with 'Thought:'\n"
                    "- After 'Thought:' use either 'Action:' OR 'Final Answer:'\n"
                    "- If using 'Action:', MUST follow with 'Action Input:' on next line\n"
                    "- NEVER output bare JSON without proper labels\n"
                    "- Use EXACT FULL tool names from available tool list: [{tool_names}]\n"
                    "- NEVER use shortened tool names - always include full prefix\n"
                    "- Example: 'hanatourApi_getBasicCommonCodeByQuery' NOT 'getBasicCommonCodeByQuery'\n"
                    "- Follow exact parameter schemas from tool descriptions\n\n"
                    "**LANGUAGE MATCHING:**\n"
                    "- Korean input = Korean Final Answer (한글 입력 = 한글 응답)\n"
                    "- English input = English Final Answer\n\n"
                    "**CORRECT FORMAT PATTERN:**\n"
                    "Thought: [analyze what information is needed]\n"
                    "Action: [exact_tool_name_from_list]\n"
                    "Action Input: {{\"parameter\": \"value\"}}\n\n"
                    "**TOOL USAGE INTELLIGENCE:**\n"
                    "- Analyze user intent and available tools\n"
                    "- Select appropriate tools based on context\n"
                    "- Use exact parameter names from tool schemas\n"
                    "- Provide concise, complete responses based on tool results\n"
                    "- CRITICAL: Write short, direct Final Answer to avoid truncation\n\n"
                    "Question: the input question you must answer\n"
                    "Thought: you should always think about what to do\n"
                    "Action: the action to take, should be one of [{tool_names}]\n"
                    "Action Input: the input to the action\n"
                    "Observation: the result of the action\n"
                    "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
                    "Thought: I now know the final answer\n"
                    "Final Answer: the final answer to the original input question\n\n"

                    "Available tools:\n{tools}\n\n"
                    "Question: {input}\n"
                    "Thought:{agent_scratchpad}"
                )
            }
        }
    
    def get_system_prompt(self, model_type: str, use_tools: bool = True) -> str:
        """Generate system prompt with mode-specific enhancements"""
        from datetime import timezone, timedelta
        kst = timezone(timedelta(hours=9))
        current_date = datetime.now(kst).strftime("%Y-%m-%d")
        date_info = f"Current date: {current_date} (UTC+9)"
        
        common = self._prompts[ModelType.COMMON.value]["system_base"]
        tone_guidelines = self._prompts[ModelType.COMMON.value]["tone_guidelines"]
        model_specific = self._prompts.get(model_type, {}).get("system_enhancement", "")
        
        # ASK 모드 전용 강화 프롬프트 추가
        ask_mode_enhancement = ""
        if not use_tools:
            ask_mode_enhancement = self._prompts[ModelType.COMMON.value]["ask_mode_enhancement"]
        
        parts = [common, date_info, tone_guidelines, model_specific, ask_mode_enhancement]
        return "\n\n".join(filter(None, parts)).strip()
    
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
    
    def get_prompt_for_model(self, model_type: str, prompt_type: str = "system", use_tools: bool = True) -> str:
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
            common["schema_compliance"],
            common["table_formatting"],
            common["error_handling"],
            common["response_format"],
            common["code_block_strict"],
            common["mermaid_diagram_rule"],
            common["markdown_standard"],
            common["readability_enhancement"],
            model_specific.get("markdown_emphasis", "")
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
        elif model_name_lower.startswith("pollinations-") or "pollinations" in model_name_lower:
            return ModelType.POLLINATIONS.value
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