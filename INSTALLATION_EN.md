# 📦 Installation Guide

Detailed installation and configuration guide for the Chat AI Agent project.

## 🔧 System Requirements

### Operating Systems
- **Windows**: Windows 10 or later
- **macOS**: macOS 10.15 (Catalina) or later
- **Linux**: Ubuntu 18.04 or later, or equivalent distribution

### Software Requirements
- **Python**: 3.9 or later (3.11 recommended)
- **Node.js**: 16.0 or later (for MCP servers)
- **Git**: Latest version
- **Docker**: Optional (for some MCP servers)

### Hardware Requirements
- **RAM**: Minimum 4GB, recommended 8GB or more
- **Storage**: Minimum 2GB free space
- **Network**: Internet connection (for API calls)

## 🚀 Quick Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd chat-ai-agent
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Settings
```bash
# Set API keys in config.json
# Configure MCP servers in mcp.json
```

### 5. Run
```bash
python main.py
```

## 📋 Detailed Installation Process

### Step 1: Prepare Python Environment

#### Check Python Installation
```bash
python --version
# or
python3 --version
```

#### If Python 3.9+ is not available:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: `brew install python3` or download from python.org
- **Ubuntu/Debian**: `sudo apt update && sudo apt install python3 python3-pip python3-venv`
- **CentOS/RHEL**: `sudo yum install python3 python3-pip`

### Step 2: Prepare Node.js Environment (for MCP servers)

#### Check Node.js Installation
```bash
node --version
npm --version
```

#### Install Node.js 16+:
- **Windows/macOS**: Download LTS version from [nodejs.org](https://nodejs.org/)
- **Ubuntu/Debian**: 
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```
- **macOS (Homebrew)**: `brew install node`

### Step 3: Project Setup

#### Clone Repository and Navigate
```bash
git clone <repository-url>
cd chat-ai-agent
```

#### Create Virtual Environment
```bash
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

#### Activate Virtual Environment
```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

#### Install Python Dependencies
```bash
# Basic installation
pip install -r requirements.txt

# Development environment (optional)
pip install -r requirements-dev.txt
```

### Step 4: MCP Server Setup

#### Install Essential MCP Servers
```bash
# Search server
npm install -g @modelcontextprotocol/server-search

# Filesystem server
npm install -g @modelcontextprotocol/server-filesystem

# MySQL server (optional)
npm install -g mysql-mcp-server

# Gmail server (optional)
npm install -g @gongrzhe/server-gmail-autoauth-mcp
```

#### Docker-based MCP Servers (optional)
```bash
# Check Docker installation
docker --version

# Download MCP server images
docker pull mcp/wikipedia-mcp
docker pull mcp/youtube-transcript
docker pull mcp/duckduckgo
```

## ⚙️ Configuration Files

### config.json Configuration

#### Basic Template
```json
{
  "current_model": "gpt-3.5-turbo",
  "models": {
    "gpt-3.5-turbo": {
      "api_key": "your-openai-api-key",
      "provider": "openai"
    },
    "gemini-2.0-flash": {
      "api_key": "your-google-api-key",
      "provider": "google"
    },
    "sonar": {
      "api_key": "your-perplexity-api-key",
      "provider": "perplexity"
    }
  },
  "conversation_settings": {
    "enable_history": true,
    "max_history_pairs": 5,
    "max_tokens_estimate": 20000
  },
  "response_settings": {
    "max_tokens": 4096,
    "enable_streaming": true,
    "streaming_chunk_size": 100
  }
}
```

#### How to Obtain API Keys

**OpenAI API Key:**
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create account or login
3. Generate new key in API Keys section
4. Add payment information (usage-based billing)

**Google Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/)
2. Login with Google account
3. Generate API key
4. Check free quota

**Perplexity API Key:**
1. Visit [Perplexity API](https://www.perplexity.ai/settings/api)
2. Create account or login
3. Generate API key
4. Purchase credits (paid service)

### mcp.json Configuration

#### Basic MCP Server Configuration
```json
{
  "mcpServers": {
    "search-mcp-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-search"]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/directory"
      ]
    },
    "mysql": {
      "command": "npx",
      "args": ["mysql-mcp-server"],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "your-username",
        "MYSQL_PASSWORD": "your-password",
        "MYSQL_DATABASE": "your-database"
      },
      "disabled": false
    }
  }
}
```

#### Advanced MCP Server Configuration
```json
{
  "mcpServers": {
    "gmail": {
      "command": "npx",
      "args": ["@gongrzhe/server-gmail-autoauth-mcp"]
    },
    "excel-stdio": {
      "command": "uvx",
      "args": ["excel-mcp-server", "stdio"]
    },
    "ppt": {
      "command": "uvx",
      "args": ["--from", "office-powerpoint-mcp-server", "ppt_mcp_server"]
    },
    "osm-mcp-server": {
      "command": "uvx",
      "args": ["osm-mcp-server"]
    },
    "youtube_transcript": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/youtube-transcript"]
    },
    "wikipedia-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/wikipedia-mcp"]
    }
  }
}
```

## 🔧 Additional Tool Installation

### Install uvx (for Python tools)
```bash
pip install uvx
```

### Specific MCP Server Installation

#### Excel MCP Server
```bash
uvx install excel-mcp-server
```

#### PowerPoint MCP Server
```bash
uvx install office-powerpoint-mcp-server
```

#### OpenStreetMap MCP Server
```bash
uvx install osm-mcp-server
```

## 🐛 Installation Troubleshooting

### Common Issues

#### 1. Python Version Issues
```bash
# Error: Python 3.9+ required
# Solution: Upgrade Python
python --version
# If 3.8 or lower, install latest Python
```

#### 2. Virtual Environment Activation Failure
```bash
# Windows PowerShell execution policy error
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# macOS/Linux permission issues
chmod +x venv/bin/activate
```

#### 3. Dependency Installation Failure
```bash
# Upgrade pip
pip install --upgrade pip

# Try installing individual packages
pip install PyQt6
pip install PyQt6-WebEngine
```

#### 4. Node.js Package Installation Failure
```bash
# Clear npm cache
npm cache clean --force

# Permission issues (macOS/Linux)
sudo npm install -g <package-name>
```

#### 5. MCP Server Connection Failure
```bash
# Check server status
node --version
npm list -g

# Check port conflicts
netstat -an | grep :3000
```

### Platform-Specific Issues

#### Windows
```bash
# If Visual C++ build tools are needed
# Install Microsoft C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Long path name issues
git config --system core.longpaths true
```

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (recommended)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Linux
```bash
# Install additional system packages (Ubuntu/Debian)
sudo apt update
sudo apt install build-essential python3-dev python3-venv

# Qt-related packages
sudo apt install qt6-base-dev qt6-webengine-dev
```

## ✅ Installation Verification

### 1. Check Python Environment
```bash
python --version
pip list | grep PyQt6
pip list | grep langchain
```

### 2. Check Node.js Environment
```bash
node --version
npm list -g | grep mcp
```

### 3. Test Application Launch
```bash
python main.py
```

### 4. Test MCP Server Connection
```bash
# Check in GUI: Settings > MCP Server Management
# Or programmatically
python -c "from mcp.client.mcp_client import MCPClient; print('MCP OK')"
```

## 🔄 Update Guide

### Update Project
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Update MCP Servers
```bash
npm update -g @modelcontextprotocol/server-search
npm update -g @modelcontextprotocol/server-filesystem
```

### Update Docker Images
```bash
docker pull mcp/wikipedia-mcp:latest
docker pull mcp/youtube-transcript:latest
```

## 🚀 Performance Optimization

### System Optimization
```bash
# Compile Python bytecode
python -m compileall .

# Optimize virtual environment
pip install --upgrade pip setuptools wheel
```

### Memory Usage Optimization
```json
{
  "response_settings": {
    "max_tokens": 2048,
    "streaming_chunk_size": 50,
    "enable_length_limit": true,
    "max_response_length": 10000
  }
}
```

## 📚 Additional Resources

### Official Documentation
- [MCP Protocol](https://modelcontextprotocol.io/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython-6/)
- [LangChain Documentation](https://python.langchain.com/)

### Community
- GitHub Issues: Bug reports and feature requests
- Discord/Slack: Real-time support (when links provided)

### Examples and Tutorials
- Sample code in `examples/` directory
- Detailed guides in `docs/` directory

Following this guide will help you successfully install and run Chat AI Agent. If you encounter issues, please seek help through GitHub Issues.