# 🔧 Developer Guide

Detailed guide for developers of the Chat AI Agent project.

## 📁 Project Structure

```
chat-ai-agent/
├── core/                           # Core business logic
│   ├── application/               # Application initialization and execution
│   │   ├── app_initializer.py    # App initializer
│   │   ├── app_runner.py         # App runner
│   │   └── signal_handler.py     # Signal handler
│   ├── chat/                     # Chat processors
│   │   ├── base_chat_processor.py    # Base chat processor
│   │   ├── simple_chat_processor.py  # Simple chat processing
│   │   └── tool_chat_processor.py    # Tool-enabled chat processing
│   ├── client/                   # Client management
│   │   ├── chat_client.py        # Chat client
│   │   ├── conversation_manager.py   # Conversation manager
│   │   └── prompt_manager.py     # Prompt manager
│   ├── config/                   # Configuration management
│   │   ├── config_manager.py     # Configuration manager
│   │   └── model_config.py       # Model configuration
│   ├── llm/                      # LLM provider implementations
│   │   ├── google/               # Google Gemini
│   │   ├── openai/               # OpenAI GPT
│   │   └── perplexity/           # Perplexity
│   ├── mcp/                      # MCP services
│   │   ├── interfaces.py         # MCP interfaces
│   │   └── service_impl.py       # MCP service implementation
│   ├── models/                   # AI model strategy pattern
│   │   ├── base_model_strategy.py    # Base model strategy
│   │   ├── openai_strategy.py        # OpenAI strategy
│   │   ├── gemini_strategy.py        # Gemini strategy
│   │   ├── perplexity_strategy.py    # Perplexity strategy
│   │   ├── claude_strategy.py        # Claude strategy
│   │   └── model_strategy_factory.py # Strategy factory
│   ├── processors/               # Message processors
│   │   ├── message_converter.py  # Message conversion
│   │   ├── image_processor.py    # Image processing
│   │   └── tool_result_formatter.py # Tool result formatting
│   ├── ai_agent.py              # Main AI agent
│   ├── ai_agent_v2.py           # Refactored AI agent
│   ├── conversation_history.py   # Conversation history management
│   └── file_utils.py            # File utilities
├── mcp/                         # All MCP-related functionality
│   ├── client/                  # MCP client
│   │   ├── mcp_client.py        # Main MCP client
│   │   ├── mcp_simple.py        # Simple MCP client
│   │   └── mcp_state.py         # MCP state management
│   ├── servers/                 # MCP server management
│   │   └── mcp.py               # MCP server control
│   └── tools/                   # MCP tool management
│       └── tool_manager.py      # Tool manager
├── tools/                       # Independent tools
│   ├── langchain/               # LangChain tool wrapper
│   │   └── langchain_tools.py   # LangChain tool integration
│   └── strategies/              # Tool selection strategies
│       └── tool_decision_strategy.py # Tool decision strategy
├── ui/                          # GUI interface
│   ├── components/              # UI components
│   │   ├── ai_processor.py      # AI processing component
│   │   ├── chat_display.py      # Chat display
│   │   ├── file_handler.py      # File handler
│   │   └── ui_manager.py        # UI manager
│   ├── handlers/                # Event handlers
│   │   └── dialog_handler.py    # Dialog handler
│   ├── menu/                    # Menu system
│   │   └── menu_factory.py      # Menu factory
│   ├── services/                # UI services
│   │   └── mcp_service.py       # MCP UI service
│   ├── styles/                  # Style management
│   │   └── theme_manager.py     # Theme manager
│   ├── main_window.py           # Main window
│   ├── chat_widget.py           # Chat widget
│   ├── settings_dialog.py       # Settings dialog
│   └── mcp_dialog.py            # MCP settings dialog
├── config.json                  # Configuration file
├── mcp.json                     # MCP server configuration
├── requirements.txt             # Python dependencies
└── main.py                      # Application entry point
```

## 🏗️ Architecture Principles

### SOLID Principles Applied

#### 1. Single Responsibility Principle (SRP)
Each class has one clear responsibility:
- `ChatClient`: Only handles chat client management
- `ConversationManager`: Only handles conversation history
- `ModelStrategy`: Only handles specific AI model processing

#### 2. Open/Closed Principle (OCP)
Open for extension, closed for modification:
```python
# Adding new model strategy without modifying existing code
class NewModelStrategy(BaseModelStrategy):
    def create_llm(self):
        # New model implementation
        pass
```

#### 3. Liskov Substitution Principle (LSP)
Subtypes can completely replace their base types:
```python
# All strategies fully implement BaseModelStrategy
strategy: BaseModelStrategy = OpenAIStrategy()
strategy = GeminiStrategy()  # Completely substitutable
```

#### 4. Interface Segregation Principle (ISP)
Clients don't depend on interfaces they don't use:
```python
# Interfaces separated by role
class ChatProcessor(ABC):
    @abstractmethod
    def process_chat(self, message): pass

class ToolManager(ABC):
    @abstractmethod
    def get_tools(self): pass
```

#### 5. Dependency Inversion Principle (DIP)
Depend on abstractions, not concretions:
```python
# Depend on abstraction, not concrete class
class AIAgent:
    def __init__(self, strategy: BaseModelStrategy):
        self.strategy = strategy  # Depends on abstraction
```

### GoF Design Patterns

#### 1. Strategy Pattern
AI model-specific processing strategies:
```python
class ModelStrategyFactory:
    @classmethod
    def get_strategy(cls, model_name: str) -> BaseModelStrategy:
        if 'gpt' in model_name:
            return OpenAIStrategy()
        elif 'gemini' in model_name:
            return GeminiStrategy()
        # ...
```

#### 2. Factory Pattern
Encapsulate object creation in factories:
```python
class LLMFactory:
    @staticmethod
    def create_llm(model_name: str, api_key: str):
        # Create model-specific LLM instance
        pass
```

#### 3. Observer Pattern
UI state change notifications:
```python
class UIStateManager:
    def __init__(self):
        self.observers = []
    
    def notify_observers(self, event):
        for observer in self.observers:
            observer.update(event)
```

#### 4. Chain of Responsibility Pattern
File processor chain:
```python
class FileProcessor:
    def __init__(self):
        self.next_processor = None
    
    def process(self, file_path):
        if self.can_process(file_path):
            return self.do_process(file_path)
        elif self.next_processor:
            return self.next_processor.process(file_path)
```

## 🔧 Development Guide

### Adding New AI Model

#### Step 1: Create Strategy Class
```python
# core/models/new_model_strategy.py
from core.models.base_model_strategy import BaseModelStrategy

class NewModelStrategy(BaseModelStrategy):
    def get_model_type(self) -> str:
        return "new_model"
    
    def supports_model(self, model_name: str) -> bool:
        return 'new_model' in model_name.lower()
    
    def create_llm(self, api_key: str, model_name: str):
        # Create new model's LLM instance
        pass
    
    def create_messages(self, user_input: str, system_prompt: str = None):
        # Implement model-specific message format
        pass
```

#### Step 2: Register in Factory
```python
# core/models/model_strategy_factory.py
from .new_model_strategy import NewModelStrategy

class ModelStrategyFactory:
    _strategies = {
        'new_model': NewModelStrategy,
        # Existing strategies...
    }
```

#### Step 3: Update Configuration
```json
{
  "models": {
    "new-model-name": {
      "api_key": "your-api-key",
      "provider": "new_model"
    }
  }
}
```

### Adding New MCP Server

#### Step 1: Add MCP Configuration
```json
{
  "mcpServers": {
    "new-server": {
      "command": "node",
      "args": ["/path/to/server.js"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

#### Step 2: Tool Mapping (Optional)
```python
# tools/langchain/langchain_tools.py
TOOL_EMOJI_MAP = {
    'new_tool_name': '🆕',
    # Existing mappings...
}
```

### Adding New UI Component

#### Step 1: Create Component Class
```python
# ui/components/new_component.py
from PyQt6.QtWidgets import QWidget

class NewComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # UI setup
        pass
```

#### Step 2: Integrate into Main Window
```python
# ui/main_window.py
from ui.components.new_component import NewComponent

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.new_component = NewComponent(self)
        # Add to layout
```

## 🧪 Testing Guide

### Writing Unit Tests
```python
# tests/test_model_strategy.py
import unittest
from core.models.openai_strategy import OpenAIStrategy

class TestOpenAIStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = OpenAIStrategy()
    
    def test_supports_model(self):
        self.assertTrue(self.strategy.supports_model('gpt-3.5-turbo'))
        self.assertFalse(self.strategy.supports_model('gemini-pro'))
```

### Integration Tests
```python
# tests/test_integration.py
from core.ai_agent import AIAgent

class TestIntegration(unittest.TestCase):
    def test_full_conversation_flow(self):
        agent = AIAgent(api_key, 'gpt-3.5-turbo')
        response, tools = agent.process_message("Hello")
        self.assertIsNotNone(response)
```

## 🔍 Debugging Guide

### Logging Configuration
```python
import logging

# Enable debug logging during development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### MCP Server Debugging
```bash
# Check MCP server status
python -c "from mcp.client.mcp_client import MCPClient; print(MCPClient().get_server_status())"
```

### UI Debugging
```python
# Output Qt debug information
import os
os.environ['QT_LOGGING_RULES'] = '*=true'
```

## 📦 Deployment Guide

### Creating Executable
```bash
# Using PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

### Docker Container
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

## 🔒 Security Considerations

### API Key Management
- Use environment variables recommended
- Add config files to `.gitignore`
- Use encrypted storage in production

### Input Validation
```python
def validate_user_input(user_input: str) -> bool:
    # Validate against malicious input
    if len(user_input) > MAX_INPUT_LENGTH:
        return False
    # Additional validation logic
    return True
```

## 🚀 Performance Optimization

### Memory Management
```python
# Process large responses in chunks
def process_large_response(response: str):
    chunk_size = 1000
    for i in range(0, len(response), chunk_size):
        chunk = response[i:i + chunk_size]
        yield chunk
```

### Asynchronous Processing
```python
import asyncio

async def async_tool_execution(tool, input_data):
    # Asynchronous tool execution
    result = await tool.execute_async(input_data)
    return result
```

## 📚 References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython-6/)
- [LangChain Documentation](https://python.langchain.com/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [GoF Design Patterns](https://en.wikipedia.org/wiki/Design_Patterns)

## 🤝 Contributing Guide

### Coding Style
- Follow PEP 8
- Use type hints
- Write docstrings (Google style)

### Commit Message Rules
```
feat: add new feature
fix: fix bug
docs: update documentation
style: change code style
refactor: refactor code
test: add/modify tests
chore: other tasks
```

### Pull Request Guide
1. Create feature branch
2. Write test code
3. Update documentation
4. Request code review