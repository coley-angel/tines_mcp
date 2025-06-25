# Tines MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with Tines workflows and automation platform. This server enables AI assistants to read, create, and manage Tines stories, actions, and workflows programmatically.

## Features

- **Story Management**: Create, read, update, and delete Tines stories
- **Action Management**: Add various action types (webhooks, AI agents, email, HTTP requests, etc.)
- **Workflow Automation**: Connect actions, manage drafts, and organize workflows
- **Note Management**: Add documentation and comments to workflows
- **Search & Discovery**: Find stories, actions, and workflows across your Tines tenant

## Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver
- A Tines account with API access
- VS Code (for MCP integration)

## Installation

### 1. Install uv (Python Package Manager)

If you don't have `uv` installed, visit [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/) for installation instructions, or install via:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

### 2. Clone and Setup

```bash
git clone <your-repo-url>
cd tines_mcp
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Configure Environment

Copy the example environment file and configure your Tines API credentials:

```bash
cp example.env .env
```

Edit `.env` with your Tines API details:

```env
TINES_API_TOKEN=your_tines_api_token_here
TINES_API_URL=https://your-tenant.tines.com/api/v1
```

**To get your Tines API token:**
1. Log into your Tines tenant
2. Go to Settings → API Keys
3. Create a new API key with appropriate permissions
4. Copy the token to your `.env` file

## Usage

### Running in VS Code (Recommended)

This MCP server is designed to work with VS Code and AI assistants that support the Model Context Protocol.

#### 1. VS Code MCP Configuration

The repository includes a VS Code MCP configuration file at `.vscode/mcp.json`. This configuration tells VS Code how to connect to the Tines MCP server.

#### 2. Start the MCP Server

You can start the server in several ways:

**Option A: Using uv directly**
```bash
uv run main.py
```

**Option B: Using VS Code tasks**
If VS Code tasks are configured, you can run the server via the Command Palette:
1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Tasks: Run Task"
3. Select the Tines MCP server task

**Option C: Terminal in VS Code**
1. Open VS Code integrated terminal (`Ctrl+` ` or `Cmd+` `)
2. Run: `uv run python main.py`

#### 3. Verify Connection

When the server starts successfully, you should see:
```
INFO - TinesMCP - MCP Server started on stdio
INFO - TinesMCP - Using Tines API at: https://your-tenant.tines.com/api/v1
```

### Available Tools

The MCP server provides the following tools for AI assistants:

#### Story Management
- `mcp_tines_create_story` - Create new stories
- `mcp_tines_get_story` - Retrieve story details
- `mcp_tines_list_stories` - List all stories
- `mcp_tines_update_story` - Update story properties
- `mcp_tines_search_stories` - Search stories by name

#### Action Management
- `mcp_tines_create_webhook_action` - Create webhook triggers
- `mcp_tines_create_ai_action` - Create AI/LLM actions
- `mcp_tines_create_email_action` - Create email actions
- `mcp_tines_create_event_transform_action` - Create data transformation actions
- `mcp_tines_create_send_to_story_action` - Create inter-story communication
- `mcp_tines_update_action` - Update existing actions
- `mcp_tines_delete_action` - Remove actions

#### Workflow Management
- `mcp_tines_connect_actions` - Link actions together
- `mcp_tines_get_story_actions` - Get all actions in a story
- `mcp_tines_list_story_drafts` - Manage story drafts

#### Documentation
- `mcp_tines_create_note` - Add notes/comments to workflows
- `mcp_tines_list_notes` - Retrieve workflow documentation
- `mcp_tines_update_note` - Edit existing notes

## Example Workflows

### Creating a Simple Alert Workflow

```python
# Example: Create a story with webhook → AI analysis → email alert
# This would be done through AI assistant commands, not direct Python

1. Create a new story
2. Add a webhook action to receive data
3. Add an AI action to analyze the incoming data
4. Add an email action to send alerts
5. Connect the actions in sequence
6. Add documentation notes
```

### Cloning and Adapting Existing Workflows

```python
# Example: Clone a workflow and adapt it for different use cases
# Through AI assistant:

1. Search for existing stories
2. Get the story structure and actions
3. Create a new story based on the template
4. Modify actions for new requirements
5. Update connections and configurations
```

## Development

### Project Structure

```
tines_mcp/
├── main.py              # MCP server implementation
├── pyproject.toml       # Project configuration
├── uv.lock             # Locked dependencies
├── example.env         # Environment template
├── .env                # Your API credentials (not tracked)
├── .vscode/
│   └── mcp.json        # VS Code MCP configuration
└── README.md           # This file
```

### Dependencies

- **FastMCP**: MCP server framework
- **requests**: HTTP client for Tines API
- **python-dotenv**: Environment variable management

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your Tines tenant
5. Submit a pull request

## Troubleshooting

### Common Issues

**Server won't start:**
- Check that your `.env` file exists and has valid credentials
- Verify your Tines API token has sufficient permissions
- Ensure the API URL format is correct: `https://your-tenant.tines.com/api/v1`

**API Authentication errors:**
- Verify your API token in Tines Settings → API Keys
- Check that the token hasn't expired
- Ensure your user has appropriate permissions for the operations you're trying to perform

**VS Code MCP connection issues:**
- Restart VS Code after configuring MCP
- Check the VS Code developer console for error messages
- Verify the `.vscode/mcp.json` configuration is correct

### Logging

The server provides detailed logging. To increase verbosity for debugging, modify the logging level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Security

- **Never commit your `.env` file** - it contains sensitive API credentials
- **Use environment variables** for all sensitive configuration
- **Limit API token permissions** to only what's needed for your use case
- **Regularly rotate your API tokens** in production environments

## License

[Add your license information here]

## Support

For issues related to:
- **This MCP server**: Open an issue in this repository
- **Tines platform**: Contact Tines support
- **VS Code MCP integration**: Check VS Code documentation
- **uv package manager**: Visit [uv documentation](https://docs.astral.sh/uv/)