# 🤖 Chat AI Agent

An AI chat agent that can use various tools by integrating with MCP (Model Context Protocol) servers.

## ✨ Key Features

### 🔗 MCP Server Integration
- **Various External Tools**: Support for 15+ MCP servers
- **Real-time Tool Detection**: Automatically recognizes available tools dynamically
- **Intelligent Tool Selection**: AI automatically selects optimal tools for each situation

### 🧠 Multi-LLM Support
- **OpenAI**: GPT-3.5, GPT-4, GPT-4V
- **Google**: Gemini Pro, Gemini 2.0 Flash
- **Perplexity**: Sonar series, R1 models
- **Extensible**: Easy to add new models

### 💬 Advanced Chat Interface
- **PyQt6 Based**: Native desktop app performance
- **WebView Engine**: Advanced text rendering with QWebEngineView
- **Markdown Support**: Bold text, bullet points, code blocks
- **Dark Theme**: Eye-friendly dark interface

### 🔄 Real-time Streaming
- **Large Response Handling**: Complete reception of long responses without interruption
- **Chunk-based Processing**: Memory-efficient streaming
- **Typing Animation**: Natural conversation experience

### 🧠 Conversation History
- **Context Preservation**: Automatically remembers previous conversations
- **Token Optimization**: Cost-efficient history management
- **Persistent Storage**: Maintains conversation continuity after app restart

## 🛠️ Supported Tools

### Search & Web
- Web search (Google, Bing, DuckDuckGo)
- URL page content retrieval
- Wikipedia search

### Database
- MySQL database queries
- Table schema inspection
- SQL query execution

### Travel Services
- Hanatour API integration
- Travel product search
- Regional travel information

### Office Tools
- Excel file read/write
- PowerPoint presentation creation/editing
- PDF, Word document processing

### Development Tools
- Bitbucket repository management
- Jira/Confluence integration
- File system access

### Other Services
- Gmail email management
- Map/location services (OpenStreetMap)
- YouTube transcripts
- Notion API integration

## 🚀 Quick Start

### 1. Installation
```bash
# Clone repository
git clone <repository-url>
cd chat-ai-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Set API keys in `config.json`:
```json
{
  "models": {
    "gpt-3.5-turbo": {
      "api_key": "your-openai-api-key",
      "provider": "openai"
    },
    "gemini-2.0-flash": {
      "api_key": "your-google-api-key",
      "provider": "google"
    }
  }
}
```

### 3. Run
```bash
python main.py
```

## 📖 Usage

### Basic Conversation
- Enter questions in the chat window and AI will respond
- Automatically selects and uses appropriate tools when needed

### Tool Usage Examples
```
User: "Show me the MySQL database list"
AI: [Uses MySQL tool] → Displays database list

User: "Find Paris travel packages"
AI: [Uses Hanatour API] → Shows Paris travel search results

User: "Summarize this Excel file"
AI: [Uses Excel tool] → Analyzes file and provides summary
```

### MCP Server Management
- Check server status in **Settings > MCP Server Management**
- Start/stop/restart individual servers
- Real-time monitoring of available tools

## 🔧 Advanced Configuration

### Conversation History Settings
```json
{
  "conversation_settings": {
    "enable_history": true,
    "max_history_pairs": 5,
    "max_tokens_estimate": 20000
  }
}
```

### Response Settings
```json
{
  "response_settings": {
    "max_tokens": 4096,
    "enable_streaming": true,
    "streaming_chunk_size": 100
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

### MIT License

This project is distributed under the MIT License.

```
MIT License

Copyright (c) 2024 Chat AI Agent Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Open Source Permissions

✅ **Commercial Use**: Free to use for commercial purposes  
✅ **Modification**: Modify and improve the source code  
✅ **Distribution**: Distribute original or modified versions  
✅ **Private Use**: Free to use for personal purposes  
✅ **Patent Use**: Grant of contributor patent rights  

### Requirements

📋 **License Notice**: Must include license text when distributing software  
📋 **Copyright Notice**: Must retain original author information  

### Limitations

⚠️ **No Warranty**: Software provided "as is" without any warranty  
⚠️ **Limited Liability**: Developers not liable for damages from use

## 🐛 Troubleshooting

### Common Issues

**MCP Server Connection Failed**
- Verify Node.js and required packages are installed
- Check if `mcp.json` configuration is correct

**API Key Error**
- Verify correct API keys are set in `config.json`
- Check if API keys have sufficient credits

**Tool Execution Error**
- Verify the service is accessible
- Check if necessary permissions are configured

## 📞 Support

If you encounter issues or have questions, please contact us through GitHub Issues.