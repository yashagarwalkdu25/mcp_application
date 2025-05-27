import asyncio
import os
import sys
from typing import Annotated, List, Optional

# Ensure parent directories are in the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# MCP imports
import mcp.server.stdio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.shared.exceptions import McpError
from mcp.types import TextContent, Tool, INVALID_PARAMS

# Pydantic for input validation
from pydantic import BaseModel, Field

# Import all our tool logic
from tools import filesystem, github_handler, sentry_handler, weather_client

# Environment loading
from dotenv import load_dotenv
load_dotenv()

# Initialize a single server
server = Server("unified_tool_suite")

# --- Pydantic Models for ALL Tool Inputs ---

# Filesystem
class FSReadFileInput(BaseModel):
    file_path: Annotated[str, Field(description="Path to the file to read")]

class FSWriteFileInput(BaseModel):
    file_path: Annotated[str, Field(description="Path to write the file")]
    content: Annotated[str, Field(description="Content to write")]

class FSListDirectoryInput(BaseModel):
    dir_path: Annotated[str, Field(description="Path to the directory to list")]

class FSCreateDirectoryInput(BaseModel):
    dir_path: Annotated[str, Field(description="Path of the directory to create")]

class FSDeleteDirectoryInput(BaseModel):
    dir_path: Annotated[str, Field(description="Path of the directory to delete")]
    recursive: Annotated[bool, Field(description="Whether to delete directory contents recursively")] = False

class FSSearchFilesInput(BaseModel):
    dir_path: Annotated[str, Field(description="Directory to search in")]
    pattern: Annotated[str, Field(description="File pattern to match (e.g., '*.txt')")] = "*"
    recursive: Annotated[bool, Field(description="Whether to search recursively in subdirectories")] = False

class FSGetMetadataInput(BaseModel):
    file_path: Annotated[str, Field(description="Path to the file to get metadata for")]

class FSDeleteFileInput(BaseModel):
    file_path: Annotated[str, Field(description="Path to the file to delete")]

class FSCopyFileInput(BaseModel):
    src_path: Annotated[str, Field(description="Source file path")]
    dst_path: Annotated[str, Field(description="Destination file path")]

class FSMoveFileInput(BaseModel):
    src_path: Annotated[str, Field(description="Source file path")]
    dst_path: Annotated[str, Field(description="Destination file path")]

# GitHub
class GHListRepoIssuesInput(BaseModel):
    repo_full_name: Annotated[str, Field(description="Full name of the repo (e.g., 'owner/repo')")]

class GHCreateRepoInput(BaseModel):
    name: Annotated[str, Field(description="Name for the new repository")]
    description: Annotated[Optional[str], Field(description="Optional description")] = ""
    private: Annotated[Optional[bool], Field(description="Make repo private (default: False)")] = False

class GHListRepositoriesInput(BaseModel):
    """No input parameters needed for listing repositories"""
    pass

class GHForkRepoInput(BaseModel):
    repo_full_name: Annotated[str, Field(description="Full name of the repo to fork (e.g., 'owner/repo')")]

class GHCreateIssueInput(BaseModel):
    repo_full_name: Annotated[str, Field(description="Full name of the repo (e.g., 'owner/repo')")]
    title: Annotated[str, Field(description="Title of the issue")]
    body: Annotated[Optional[str], Field(description="Body/description of the issue")] = ""
    labels: Annotated[Optional[List[str]], Field(description="List of labels to apply")] = []

class GHCreatePRInput(BaseModel):
    repo_full_name: Annotated[str, Field(description="Full name of the repo (e.g., 'owner/repo')")]
    title: Annotated[str, Field(description="Title of the pull request")]
    head: Annotated[str, Field(description="Branch containing changes")]
    base: Annotated[str, Field(description="Base branch to merge into")] = "main"
    body: Annotated[Optional[str], Field(description="Description of the changes")] = ""

class GHSearchReposInput(BaseModel):
    query: Annotated[str, Field(description="Search query")]
    sort: Annotated[str, Field(description="Sort by (stars, forks, updated)")] = "stars"
    order: Annotated[str, Field(description="Sort order (asc, desc)")] = "desc"
    limit: Annotated[int, Field(description="Maximum number of results")] = 10

class GHSearchCodeInput(BaseModel):
    query: Annotated[str, Field(description="Search query")]
    repo: Annotated[Optional[str], Field(description="Limit search to specific repo")] = None
    language: Annotated[Optional[str], Field(description="Filter by programming language")] = None
    limit: Annotated[int, Field(description="Maximum number of results")] = 10

class GHGetPRsInput(BaseModel):
    repo_full_name: Annotated[str, Field(description="Full name of the repo (e.g., 'owner/repo')")]
    state: Annotated[str, Field(description="PR state (open, closed, all)")] = "open"

class GHReviewPRInput(BaseModel):
    repo_full_name: Annotated[str, Field(description="Full name of the repo (e.g., 'owner/repo')")]
    pr_number: Annotated[int, Field(description="Pull request number")]
    body: Annotated[str, Field(description="Review comment")]
    event: Annotated[str, Field(description="Review event (APPROVE, REQUEST_CHANGES, COMMENT)")] = "APPROVE"

class GHUpdateReadmeInput(BaseModel):
    repo_full_name: Annotated[str, Field(description="Full name of the repo (e.g., 'owner/repo')")]
    content: Annotated[str, Field(description="New content for the README file")]
    commit_message: Annotated[Optional[str], Field(description="Commit message for the update")] = "Update README.md"

# Sentry
class SentryGetIssuesInput(BaseModel):
    project_slug: Annotated[str, Field(description="Sentry project slug")]
    query: Annotated[Optional[str], Field(description="Optional search query to filter issues")] = ""
    stats_period: Annotated[Optional[str], Field(description="Time period for stats (e.g., '24h', '7d')")] = "24h"

class SentryGetIssueDetailsInput(BaseModel):
    project_slug: Annotated[str, Field(description="Sentry project slug")]
    issue_id: Annotated[str, Field(description="ID of the issue to get details for")]

class SentryGetErrorFrequencyInput(BaseModel):
    project_slug: Annotated[str, Field(description="Sentry project slug")]
    days: Annotated[int, Field(description="Number of days to analyze")] = 7

class SentryGetErrorPatternsInput(BaseModel):
    project_slug: Annotated[str, Field(description="Sentry project slug")]
    days: Annotated[int, Field(description="Number of days to analyze patterns")] = 7

class SentryUpdateIssueStatusInput(BaseModel):
    project_slug: Annotated[str, Field(description="Sentry project slug")]
    issue_id: Annotated[str, Field(description="ID of the issue to update")]
    status: Annotated[str, Field(description="New status (resolved, ignored, unresolved)")]

class SentryGetProjectStatsInput(BaseModel):
    project_slug: Annotated[str, Field(description="Sentry project slug")]

class SentryGetDetailedStacktraceInput(BaseModel):
    project_slug: Annotated[str, Field(description="Sentry project slug")]
    issue_id: Annotated[str, Field(description="ID of the issue to get detailed stacktrace for")]

class SentryAnalyzeErrorPatternsInput(BaseModel):
    project_slug: Annotated[str, Field(description="Sentry project slug")]
    days: Annotated[int, Field(description="Number of days to analyze patterns")] = 7

# Weather
class WeatherGetCurrentInput(BaseModel):
    location: Annotated[str, Field(description="City name or zip code for weather")]

# --- MCP Tool Implementation ---

@server.list_tools()
async def list_tools() -> List[Tool]:
    """Lists ALL available tools from every integrated service."""
    return [
        # Filesystem Tools
        Tool(
            name="fs_read_file",
            description="Reads the content of a local file.",
            inputSchema=FSReadFileInput.model_json_schema(),
        ),
        Tool(
            name="fs_write_file",
            description="Writes content to a local file.",
            inputSchema=FSWriteFileInput.model_json_schema(),
        ),
        Tool(
            name="fs_list_directory",
            description="Lists files and directories in a local path.",
            inputSchema=FSListDirectoryInput.model_json_schema(),
        ),
        Tool(
            name="fs_create_directory",
            description="Creates a new directory and any necessary parent directories.",
            inputSchema=FSCreateDirectoryInput.model_json_schema(),
        ),
        Tool(
            name="fs_delete_directory",
            description="Deletes a directory, optionally recursively.",
            inputSchema=FSDeleteDirectoryInput.model_json_schema(),
        ),
        Tool(
            name="fs_search_files",
            description="Searches for files matching a pattern in a directory.",
            inputSchema=FSSearchFilesInput.model_json_schema(),
        ),
        Tool(
            name="fs_get_metadata",
            description="Gets detailed metadata about a file.",
            inputSchema=FSGetMetadataInput.model_json_schema(),
        ),
        Tool(
            name="fs_delete_file",
            description="Deletes a file.",
            inputSchema=FSDeleteFileInput.model_json_schema(),
        ),
        Tool(
            name="fs_copy_file",
            description="Copies a file from source to destination.",
            inputSchema=FSCopyFileInput.model_json_schema(),
        ),
        Tool(
            name="fs_move_file",
            description="Moves a file from source to destination.",
            inputSchema=FSMoveFileInput.model_json_schema(),
        ),
        # GitHub Tools
        Tool(
            name="gh_list_repositories",
            description="Lists all GitHub repositories accessible by the authenticated user.",
            inputSchema=GHListRepositoriesInput.model_json_schema(),
        ),
        Tool(
            name="gh_list_repo_issues",
            description="Lists open issues for a GitHub repository.",
            inputSchema=GHListRepoIssuesInput.model_json_schema(),
        ),
        Tool(
            name="gh_create_repo",
            description="Creates a new GitHub repository.",
            inputSchema=GHCreateRepoInput.model_json_schema(),
        ),
        Tool(
            name="gh_fork_repo",
            description="Forks an existing GitHub repository.",
            inputSchema=GHForkRepoInput.model_json_schema(),
        ),
        Tool(
            name="gh_create_issue",
            description="Creates a new issue in a repository.",
            inputSchema=GHCreateIssueInput.model_json_schema(),
        ),
        Tool(
            name="gh_create_pr",
            description="Creates a new pull request.",
            inputSchema=GHCreatePRInput.model_json_schema(),
        ),
        Tool(
            name="gh_search_repos",
            description="Searches for GitHub repositories.",
            inputSchema=GHSearchReposInput.model_json_schema(),
        ),
        Tool(
            name="gh_search_code",
            description="Searches for code in GitHub repositories.",
            inputSchema=GHSearchCodeInput.model_json_schema(),
        ),
        Tool(
            name="gh_get_prs",
            description="Lists pull requests in a repository.",
            inputSchema=GHGetPRsInput.model_json_schema(),
        ),
        Tool(
            name="gh_review_pr",
            description="Reviews a pull request.",
            inputSchema=GHReviewPRInput.model_json_schema(),
        ),
        Tool(
            name="gh_update_readme",
            description="Updates or creates the README.md file in a repository.",
            inputSchema=GHUpdateReadmeInput.model_json_schema(),
        ),
        # Sentry Tools
        Tool(
            name="sentry_get_issues",
            description="Gets issues for a Sentry project with optional filtering.",
            inputSchema=SentryGetIssuesInput.model_json_schema(),
        ),
        Tool(
            name="sentry_get_issue_details",
            description="Gets detailed information about a specific issue including stacktrace.",
            inputSchema=SentryGetIssueDetailsInput.model_json_schema(),
        ),
        Tool(
            name="sentry_get_error_frequency",
            description="Gets error frequency statistics over a time period.",
            inputSchema=SentryGetErrorFrequencyInput.model_json_schema(),
        ),
        Tool(
            name="sentry_get_error_patterns",
            description="Analyzes error patterns and groups similar errors.",
            inputSchema=SentryGetErrorPatternsInput.model_json_schema(),
        ),
        Tool(
            name="sentry_update_issue_status",
            description="Updates the status of a Sentry issue.",
            inputSchema=SentryUpdateIssueStatusInput.model_json_schema(),
        ),
        Tool(
            name="sentry_get_project_stats",
            description="Gets overall project statistics and health metrics.",
            inputSchema=SentryGetProjectStatsInput.model_json_schema(),
        ),
        Tool(
            name="sentry_get_detailed_stacktrace",
            description="Gets detailed stacktrace analysis including frame-by-frame analysis, context, and error propagation path.",
            inputSchema=SentryGetDetailedStacktraceInput.model_json_schema(),
        ),
        Tool(
            name="sentry_analyze_error_patterns",
            description="Analyzes error patterns in detail including frequency trends, user impact, and correlation patterns.",
            inputSchema=SentryAnalyzeErrorPatternsInput.model_json_schema(),
        ),
        # Weather Tools
        Tool(
            name="weather_get_current",
            description="Gets the current weather for a location.",
            inputSchema=WeatherGetCurrentInput.model_json_schema(),
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handles incoming tool calls and routes them to the correct logic."""
    print(f"Unified MCP: Received {name} with {arguments}") # Debug log

    result_dict = {}

    try:
        # --- Route to Filesystem Tools ---
        if name == "fs_read_file":
            args = FSReadFileInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.read_file, args.file_path)
        elif name == "fs_write_file":
            args = FSWriteFileInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.write_file, args.file_path, args.content)
        elif name == "fs_list_directory":
            args = FSListDirectoryInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.list_directory, args.dir_path)
        elif name == "fs_create_directory":
            args = FSCreateDirectoryInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.create_directory, args.dir_path)
        elif name == "fs_delete_directory":
            args = FSDeleteDirectoryInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.delete_directory, args.dir_path, args.recursive)
        elif name == "fs_search_files":
            args = FSSearchFilesInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.search_files, args.dir_path, args.pattern, args.recursive)
        elif name == "fs_get_metadata":
            args = FSGetMetadataInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.get_file_metadata, args.file_path)
        elif name == "fs_delete_file":
            args = FSDeleteFileInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.delete_file, args.file_path)
        elif name == "fs_copy_file":
            args = FSCopyFileInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.copy_file, args.src_path, args.dst_path)
        elif name == "fs_move_file":
            args = FSMoveFileInput(**arguments)
            result_dict = await asyncio.to_thread(filesystem.move_file, args.src_path, args.dst_path)

        # --- Route to GitHub Tools ---
        elif name == "gh_list_repositories":
            args = GHListRepositoriesInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.list_repositories)
        elif name == "gh_list_repo_issues":
            args = GHListRepoIssuesInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.list_repo_issues, args.repo_full_name)
        elif name == "gh_create_repo":
            args = GHCreateRepoInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.create_repo, args.name, args.description, args.private)
        elif name == "gh_fork_repo":
            args = GHForkRepoInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.fork_repo, args.repo_full_name)
        elif name == "gh_create_issue":
            args = GHCreateIssueInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.create_issue, args.repo_full_name, args.title, args.body, args.labels)
        elif name == "gh_create_pr":
            args = GHCreatePRInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.create_pull_request, args.repo_full_name, args.title, args.head, args.base, args.body)
        elif name == "gh_search_repos":
            args = GHSearchReposInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.search_repositories, args.query, args.sort, args.order, args.limit)
        elif name == "gh_search_code":
            args = GHSearchCodeInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.search_code, args.query, args.repo, args.language, args.limit)
        elif name == "gh_get_prs":
            args = GHGetPRsInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.get_pull_requests, args.repo_full_name, args.state)
        elif name == "gh_review_pr":
            args = GHReviewPRInput(**arguments)
            result_dict = await asyncio.to_thread(github_handler.review_pull_request, args.repo_full_name, args.pr_number, args.body, args.event)
        elif name == "gh_update_readme":
            args = GHUpdateReadmeInput(**arguments)
            result_dict = await asyncio.to_thread(
                github_handler.update_readme,
                args.repo_full_name,
                args.content,
                args.commit_message
            )

        # --- Route to Sentry Tools ---
        elif name == "sentry_get_issues":
            args = SentryGetIssuesInput(**arguments)
            result_dict = await asyncio.to_thread(
                sentry_handler.get_sentry_issues,
                args.project_slug,
                args.query,
                args.stats_period
            )
        elif name == "sentry_get_issue_details":
            args = SentryGetIssueDetailsInput(**arguments)
            result_dict = await asyncio.to_thread(
                sentry_handler.get_issue_details,
                args.project_slug,
                args.issue_id
            )
        elif name == "sentry_get_error_frequency":
            args = SentryGetErrorFrequencyInput(**arguments)
            result_dict = await asyncio.to_thread(
                sentry_handler.get_error_frequency,
                args.project_slug,
                args.days
            )
        elif name == "sentry_get_error_patterns":
            args = SentryGetErrorPatternsInput(**arguments)
            result_dict = await asyncio.to_thread(
                sentry_handler.get_error_patterns,
                args.project_slug,
                args.days
            )
        elif name == "sentry_update_issue_status":
            args = SentryUpdateIssueStatusInput(**arguments)
            result_dict = await asyncio.to_thread(
                sentry_handler.update_issue_status,
                args.project_slug,
                args.issue_id,
                args.status
            )
        elif name == "sentry_get_project_stats":
            args = SentryGetProjectStatsInput(**arguments)
            result_dict = await asyncio.to_thread(
                sentry_handler.get_project_stats,
                args.project_slug
            )
        elif name == "sentry_get_detailed_stacktrace":
            args = SentryGetDetailedStacktraceInput(**arguments)
            result_dict = await asyncio.to_thread(
                sentry_handler.get_detailed_stacktrace,
                args.project_slug,
                args.issue_id
            )
        elif name == "sentry_analyze_error_patterns":
            args = SentryAnalyzeErrorPatternsInput(**arguments)
            result_dict = await asyncio.to_thread(
                sentry_handler.analyze_error_patterns,
                args.project_slug,
                args.days
            )

        # --- Route to Weather Tools ---
        elif name == "weather_get_current":
            args = WeatherGetCurrentInput(**arguments)
            # This calls our custom API client, which uses 'requests',
            # which is blocking, so use to_thread.
            result_dict = await asyncio.to_thread(weather_client.get_current_weather, args.location)

        # --- Handle Unknown Tools ---
        else:
            raise McpError(INVALID_PARAMS, f"Unknown tool: {name}")

        # --- Process Results ---
        if isinstance(result_dict, dict) and "error" in result_dict:
            raise McpError(INVALID_PARAMS, result_dict["error"])

        # Simple formatting: Convert dict/list to string for TextContent
        # You can make this more sophisticated for better Claude output.
        if isinstance(result_dict, (dict, list)):
           import json
           response_text = json.dumps(result_dict, indent=2)
        else:
           response_text = str(result_dict)

        return [TextContent(type="text", text=response_text)]

    except ValueError as e: # Pydantic validation error
        print(f"Unified MCP Pydantic Error: {e}")
        raise McpError(INVALID_PARAMS, f"Invalid parameters for {name}: {e}")
    except McpError as e: # Re-raise known MCP errors
        print(f"Unified MCP Error: {e.message}")
        raise e
    except Exception as e: # Catch any other unexpected errors
        print(f"Unified MCP Unexpected Error: {type(e).__name__} - {e}")
        raise McpError(INVALID_PARAMS, f"An unexpected server error occurred: {e}")

async def main():
    """Main entry point for the Unified MCP server."""
    print("--- Starting Unified MCP Server (stdio) ---")
    print("!!! Ensure API Keys & FS Paths are set in .env !!!")
    print("!!! Ensure custom_weather_api.py is running !!!")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="unified_tool_suite",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Unified MCP Server failed: {e}")
        sys.exit(1)