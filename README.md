# MCP Application - Unified Tool Suite

A powerful and extensible tool suite that integrates multiple services including Sentry error tracking, GitHub repository management, filesystem operations, and weather data retrieval. This application provides a unified interface for managing and monitoring your development workflow.

## 🌟 Features

### Sentry Integration
- Comprehensive error tracking and monitoring
- Detailed stacktrace analysis
- Error pattern analysis and grouping
- Project health metrics
- Issue management and status updates
- Real-time error frequency tracking

### GitHub Integration
- Repository management (create, fork, list)
- Issue tracking and management
- Pull request handling
- Code search capabilities
- Repository search
- README management

### Filesystem Operations
- File reading and writing
- Directory management
- File search and metadata
- File operations (copy, move, delete)
- Recursive directory operations

### Weather Service
- Current weather data retrieval
- Location-based weather information

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- uv (Python package installer and resolver)
- Sentry account and API token
- GitHub account and API token (for GitHub features)
- Claude API access (for AI integration)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yashagarwalkdu25/mcp_application.git
cd mcp_application
```

2. Create and activate a virtual environment using uv:
```bash
# Create virtual environment with Python 3.11
uv venv --python 3.11

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# OR
.venv\Scripts\activate     # On Windows

# Install dependencies using uv
uv pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with the following variables:
```env
# Weather API Configuration
OPENWEATHER_API_KEY=your_openweather_api_key
CUSTOM_WEATHER_API_PORT=5000

# GitHub Configuration
GITHUB_TOKEN=your_github_token

# Sentry Configuration
SENTRY_AUTH_TOKEN=your_sentry_token
SENTRY_ORG_SLUG=your_org_slug

# Filesystem Configuration
ALLOWED_FS_PATHS=/path/to/allowed/directory
```

### Connecting to Claude

To connect the MCP server to Claude:

1. Create a configuration file for Claude at:
```bash
~/.config/claude/config.json  # On Unix/macOS
# OR
%APPDATA%\claude\config.json  # On Windows
```

2. Add the following configuration:
```json
{
  "unified_tool_suite": {
    "command": "/path/to/your/venv/bin/python",
    "args": [
      "/path/to/mcp_application/mcp_servers/mcp_server.py"
    ],
    "env": {
      "OPENWEATHER_API_KEY": "your_openweather_api_key",
      "CUSTOM_WEATHER_API_PORT": "5000",
      "GITHUB_TOKEN": "your_github_token",
      "SENTRY_AUTH_TOKEN": "your_sentry_token",
      "SENTRY_ORG_SLUG": "your_org_slug",
      "ALLOWED_FS_PATHS": "/path/to/allowed/directory"
    }
  }
}
```

Replace the paths and tokens with your actual values:
- `command`: Path to your Python virtual environment executable
- `args`: Path to your mcp_server.py file
- Environment variables: Your actual API keys and configuration values

3. Start the MCP server:
```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Start the MCP server
python mcp_servers/mcp_server.py
```

4. Verify the connection:
- The MCP server should start without errors
- You should see a message indicating successful startup
- Claude should be able to access the MCP tools

Note: Keep your API keys and tokens secure. Never commit them to version control.

## 📚 Usage

### Sentry Tools
```python
from tools import sentry_handler

# Test connection
connection = sentry_handler.test_connection()

# Get project issues
issues = sentry_handler.get_sentry_issues("my-project")

# Analyze error patterns
patterns = sentry_handler.analyze_error_patterns("my-project", days=7)

# Get detailed stacktrace
stacktrace = sentry_handler.get_detailed_stacktrace("my-project", "issue-id")
```

### GitHub Tools
```python
from tools import github_handler

# List repositories
repos = github_handler.list_repositories()

# Create repository
new_repo = github_handler.create_repo("my-new-repo", "Description", private=True)

# Create issue
issue = github_handler.create_issue("owner/repo", "Issue title", "Issue description")
```

### Filesystem Tools
```python
from tools import filesystem

# List directory contents
contents = filesystem.list_directory("/path/to/directory")

# Read file
content = filesystem.read_file("/path/to/file.txt")

# Write file
filesystem.write_file("/path/to/file.txt", "New content")
```

## 🔧 Configuration

### Sentry Configuration
- `SENTRY_AUTH_TOKEN`: Your Sentry authentication token
- `SENTRY_ORG_SLUG`: Your Sentry organization slug

### GitHub Configuration
- `GITHUB_TOKEN`: Your GitHub personal access token

### Filesystem Configuration
- `ALLOWED_FS_PATHS`: Comma-separated list of allowed filesystem paths

## 📊 API Documentation

Detailed API documentation is available in the code through docstrings. Each module and function includes:
- Description
- Parameters
- Return values
- Examples
- Error handling

## 🛠️ Development

### Project Structure
```
mcp_application/
├── mcp_servers/
│   ├── mcp_server.py
│   └── filesystem_server.py
├── tools/
│   ├── sentry_handler.py
│   ├── github_handler.py
│   ├── filesystem.py
│   └── weather_client.py
├── requirements.txt
├── .env
└── README.md
```

### Adding New Tools
1. Create a new handler in the `tools/` directory
2. Add input models in `mcp_servers/mcp_server.py`
3. Register the tool in the `list_tools()` function
4. Add the tool handler in the `call_tool()` function

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Sentry for error tracking capabilities
- GitHub for repository management features
- Python community for excellent libraries and tools

## 📞 Support

For support, please:
1. Check the [documentation](docs/)
2. Open an issue in the repository
3. Contact the maintainers

## 🔄 Updates

Stay updated with the latest changes by:
- Watching the repository
- Following the release notes
- Checking the changelog

---

Made with ❤️ by the MCP Application Team