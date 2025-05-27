import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Replace with your actual token securely
TOKEN = os.getenv("SENTRY_AUTH_TOKEN")
ORG_SLUG = "ibe08"
BASE_URL = "https://sentry.io/api/0"

def _validate_config() -> Dict[str, Any]:
    """
    Validates the Sentry configuration by checking required environment variables.
    
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {"status": "ok"} if configuration is valid
            - {"error": "error message"} if configuration is invalid
    
    Example:
        >>> config = _validate_config()
        >>> if "error" in config:
        ...     print(f"Configuration error: {config['error']}")
    """
    errors = []
    if not TOKEN:
        errors.append("SENTRY_AUTH_TOKEN not set in environment variables")
    if not ORG_SLUG:
        errors.append("SENTRY_ORG_SLUG not set in environment variables")
    
    if errors:
        return {"error": "Configuration errors: " + "; ".join(errors)}
    return {"status": "ok"}

def _get_headers() -> Dict[str, str]:
    """
    Generates the headers required for Sentry API requests.
    
    Returns:
        Dict[str, str]: Dictionary containing Authorization and Content-Type headers
        
    Raises:
        ValueError: If configuration validation fails
        
    Example:
        >>> headers = _get_headers()
        >>> # Use headers in API request
        >>> response = requests.get(url, headers=headers)
    """
    config_status = _validate_config()
    if "error" in config_status:
        raise ValueError(config_status["error"])
    return {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }

def _handle_api_error(response: requests.Response) -> Dict[str, Any]:
    """
    Handles and formats Sentry API error responses.
    
    Args:
        response (requests.Response): The response object from a failed API request
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - error: Human-readable error message
            - status_code: HTTP status code
            - url: The URL that caused the error
            
    Example:
        >>> response = requests.get(url)
        >>> if response.status_code != 200:
        ...     error = _handle_api_error(response)
        ...     print(f"API Error: {error['error']}")
    """
    try:
        error_data = response.json()
        error_message = error_data.get('detail', str(error_data))
    except:
        error_message = response.text or f"HTTP {response.status_code}"
    
    return {
        "error": f"Sentry API Error ({response.status_code}): {error_message}",
        "status_code": response.status_code,
        "url": response.url
    }

def list_projects() -> Dict[str, Any]:
    """
    Retrieves a list of all available projects in the Sentry organization.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - projects: List of project objects with details like:
                - id: Project ID
                - slug: Project slug
                - name: Project name
                - platform: Project platform
                - status: Project status
                - dateCreated: Creation date
                - isBookmarked: Bookmark status
            - error: Error message if the request fails
            
    Example:
        >>> projects = list_projects()
        >>> for project in projects.get("projects", []):
        ...     print(f"Project: {project['name']} ({project['slug']})")
    """
    try:
        # Validate configuration first
        config_status = _validate_config()
        if "error" in config_status:
            return config_status
        
        url = f"{BASE_URL}/organizations/{ORG_SLUG}/projects/"
        headers = _get_headers()
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return _handle_api_error(response)
        
        projects = response.json()
        return {
            "projects": [{
                "id": project["id"],
                "slug": project["slug"],
                "name": project["name"],
                "platform": project.get("platform"),
                "status": project.get("status"),
                "dateCreated": project.get("dateCreated"),
                "isBookmarked": project.get("isBookmarked", False)
            } for project in projects]
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def validate_project(project_slug: str) -> Dict[str, Any]:
    """
    Validates if a project exists and is accessible in the Sentry organization.
    
    Args:
        project_slug (str): The slug of the project to validate
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status: "valid" if project exists
            - project: Project details if valid
            - error: Error message if validation fails
            
    Example:
        >>> status = validate_project("my-project")
        >>> if status.get("status") == "valid":
        ...     print(f"Project {status['project']['name']} is valid")
    """
    try:
        url = f"{BASE_URL}/projects/{ORG_SLUG}/{project_slug}/"
        headers = _get_headers()
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return {"error": f"Project '{project_slug}' not found in organization '{ORG_SLUG}'"}
        elif response.status_code != 200:
            return _handle_api_error(response)
        
        project_data = response.json()
        return {
            "status": "valid",
            "project": {
                "id": project_data["id"],
                "slug": project_data["slug"],
                "name": project_data["name"],
                "platform": project_data.get("platform"),
                "status": project_data.get("status")
            }
        }
    except Exception as e:
        return {"error": f"Project validation failed: {str(e)}"}

def get_sentry_issues(project_slug: str, query: str = "", stats_period: str = "24h") -> Dict[str, Any]:
    """
    Retrieves issues for a specific project with optional filtering.
    
    Args:
        project_slug (str): The slug of the project
        query (str, optional): Search query to filter issues. Defaults to "".
        stats_period (str, optional): Time period for statistics. Defaults to "24h".
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - project: Project details
            - issues: List of issue objects with details like:
                - id: Issue ID
                - title: Issue title
                - count: Number of occurrences
                - userCount: Number of affected users
                - firstSeen: First occurrence timestamp
                - lastSeen: Last occurrence timestamp
                - level: Error level
                - status: Issue status
                - permalink: Issue URL
            - error: Error message if the request fails
            
    Example:
        >>> issues = get_sentry_issues("my-project", query="is:unresolved")
        >>> for issue in issues.get("issues", []):
        ...     print(f"Issue: {issue['title']} ({issue['count']} occurrences)")
    """
    try:
        # Validate configuration first
        config_status = _validate_config()
        if "error" in config_status:
            return config_status
            
        # Validate project exists
        project_status = validate_project(project_slug)
        if "error" in project_status:
            return project_status
        
        url = f"{BASE_URL}/projects/{ORG_SLUG}/{project_slug}/issues/"
        
        headers = _get_headers()
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return {"error": f"Project '{project_slug}' not found in organization '{ORG_SLUG}'"}
        elif response.status_code == 403:
            return {"error": "Authentication failed. Please check your SENTRY_AUTH_TOKEN"}
        elif response.status_code != 200:
            return _handle_api_error(response)
        
        issues = response.json()
        
        return {
            "project": project_status["project"],
            "issues": [{
                "id": issue["id"],
                "title": issue["title"],
                "count": issue["count"],
                "userCount": issue["userCount"],
                "firstSeen": issue["firstSeen"],
                "lastSeen": issue["lastSeen"],
                "level": issue["level"],
                "status": issue["status"],
                "permalink": issue["permalink"],
                "culprit": issue.get("culprit", ""),
                "type": issue["type"],
                "metadata": issue.get("metadata", {})
            } for issue in issues]
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# Test the connection
def test_connection() -> Dict[str, Any]:
    """Test the Sentry API connection and configuration."""
    try:
        # First validate configuration
        config_status = _validate_config()
        if "error" in config_status:
            return config_status
        
        # Try to get organization info
        url = f"{BASE_URL}/organizations/{ORG_SLUG}/"
        headers = _get_headers()
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            org_data = response.json()
            return {
                "status": "success",
                "organization": {
                    "name": org_data.get("name"),
                    "slug": org_data.get("slug"),
                    "id": org_data.get("id")
                },
                "config": {
                    "base_url": BASE_URL,
                    "org_slug": ORG_SLUG,
                    "token_status": "valid" if TOKEN else "missing"
                }
            }
        else:
            return _handle_api_error(response)
            
    except Exception as e:
        return {"error": f"Connection test failed: {str(e)}"}

def get_issue_details(project_slug: str, issue_id: str) -> Dict[str, Any]:
    """
    Retrieves detailed information about a specific issue including stacktrace.
    
    Args:
        project_slug (str): The slug of the project
        issue_id (str): The ID of the issue
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - issue: Detailed issue information
            - stacktrace: Stacktrace data if available
            - error: Error message if the request fails
            
    Example:
        >>> details = get_issue_details("my-project", "12345")
        >>> print(f"Issue: {details['issue']['title']}")
        >>> print(f"Stacktrace frames: {len(details['stacktrace'])}")
    """
    if not ORG_SLUG:
        return {"error": "SENTRY_ORG_SLUG not set."}
    
    url = f"{BASE_URL}/projects/{ORG_SLUG}/{project_slug}/issues/{issue_id}/"
    
    try:
        headers = _get_headers()
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        issue = response.json()
        
        # Get the latest event for stacktrace
        events_url = f"{BASE_URL}/projects/{ORG_SLUG}/{project_slug}/issues/{issue_id}/events/latest/"
        events_response = requests.get(events_url, headers=headers)
        events_response.raise_for_status()
        event = events_response.json()
        
        return {
            "issue": {
                "id": issue["id"],
                "title": issue["title"],
                "count": issue["count"],
                "userCount": issue["userCount"],
                "firstSeen": issue["firstSeen"],
                "lastSeen": issue["lastSeen"],
                "level": issue["level"],
                "status": issue["status"],
                "permalink": issue["permalink"],
                "culprit": issue.get("culprit", ""),
                "type": issue["type"],
                "metadata": issue.get("metadata", {}),
                "stacktrace": event.get("entries", []),
                "tags": issue.get("tags", []),
                "assignedTo": issue.get("assignedTo", None),
                "subscribed": issue.get("subscribed", False)
            }
        }
    except Exception as e:
        return {"error": str(e)}

def get_error_frequency(project_slug: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyzes error frequency statistics over a specified time period.
    
    Args:
        project_slug (str): The slug of the project
        days (int, optional): Number of days to analyze. Defaults to 7.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - statistics: Error statistics including:
                - timeframe: Analysis period
                - data: Raw statistics data
                - total_errors: Total error count
                - average_per_day: Average errors per day
            - error: Error message if the request fails
            
    Example:
        >>> stats = get_error_frequency("my-project", days=30)
        >>> print(f"Total errors: {stats['statistics']['total_errors']}")
        >>> print(f"Average per day: {stats['statistics']['average_per_day']}")
    """
    if not ORG_SLUG:
        return {"error": "SENTRY_ORG_SLUG not set."}
    
    url = f"{BASE_URL}/projects/{ORG_SLUG}/{project_slug}/stats/"
    end = datetime.now()
    start = end - timedelta(days=days)
    
    params = {
        "stat": "received",
        "resolution": "1d",
        "since": start.isoformat(),
        "until": end.isoformat()
    }
    
    try:
        headers = _get_headers()
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        stats = response.json()
        
        return {
            "statistics": {
                "timeframe": f"Last {days} days",
                "data": stats,
                "total_errors": sum(stats),
                "average_per_day": sum(stats) / len(stats) if stats else 0
            }
        }
    except Exception as e:
        return {"error": str(e)}

def get_error_patterns(project_slug: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyzes and groups similar errors to identify patterns.
    
    Args:
        project_slug (str): The slug of the project
        days (int, optional): Number of days to analyze. Defaults to 7.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - patterns: Error patterns including:
                - timeframe: Analysis period
                - total_issues: Total number of issues
                - by_type: Distribution by error type
                - by_level: Distribution by error level
                - by_culprit: Distribution by error culprit
                - most_frequent_culprits: Top 5 most frequent error sources
            - error: Error message if the request fails
            
    Example:
        >>> patterns = get_error_patterns("my-project")
        >>> print(f"Total issues: {patterns['patterns']['total_issues']}")
        >>> print("Most frequent culprits:", patterns['patterns']['most_frequent_culprits'])
    """
    if not ORG_SLUG:
        return {"error": "SENTRY_ORG_SLUG not set."}
    
    # First get all issues
    issues = get_sentry_issues(project_slug, stats_period=f"{days}d")
    if "error" in issues:
        return issues
    
    # Group issues by type and level
    patterns = {
        "by_type": {},
        "by_level": {},
        "by_culprit": {}
    }
    
    for issue in issues["issues"]:
        # Group by type
        issue_type = issue["type"]
        if issue_type not in patterns["by_type"]:
            patterns["by_type"][issue_type] = []
        patterns["by_type"][issue_type].append(issue)
        
        # Group by level
        level = issue["level"]
        if level not in patterns["by_level"]:
            patterns["by_level"][level] = []
        patterns["by_level"][level].append(issue)
        
        # Group by culprit (function/method)
        if "culprit" in issue:
            culprit = issue["culprit"]
            if culprit not in patterns["by_culprit"]:
                patterns["by_culprit"][culprit] = []
            patterns["by_culprit"][culprit].append(issue)
    
    return {
        "patterns": {
            "timeframe": f"Last {days} days",
            "total_issues": len(issues["issues"]),
            "by_type": {k: len(v) for k, v in patterns["by_type"].items()},
            "by_level": {k: len(v) for k, v in patterns["by_level"].items()},
            "by_culprit": {k: len(v) for k, v in patterns["by_culprit"].items()},
            "most_frequent_culprits": sorted(
                [(k, len(v)) for k, v in patterns["by_culprit"].items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    }

def update_issue_status(project_slug: str, issue_id: str, status: str) -> Dict[str, Any]:
    """
    Updates the status of a specific issue.
    
    Args:
        project_slug (str): The slug of the project
        issue_id (str): The ID of the issue
        status (str): New status (resolved, ignored, unresolved)
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status: "success" if update was successful
            - message: Status update message
            - issue: Updated issue details
            - error: Error message if the request fails
            
    Example:
        >>> result = update_issue_status("my-project", "12345", "resolved")
        >>> print(f"Status: {result['message']}")
    """
    if not ORG_SLUG:
        return {"error": "SENTRY_ORG_SLUG not set."}
    
    url = f"{BASE_URL}/projects/{ORG_SLUG}/{project_slug}/issues/{issue_id}/"
    
    try:
        headers = _get_headers()
        data = {"status": status}
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": f"Issue {issue_id} status updated to {status}",
            "issue": response.json()
        }
    except Exception as e:
        return {"error": str(e)}

def get_project_stats(project_slug: str) -> Dict[str, Any]:
    """
    Retrieves overall project statistics and health metrics.
    
    Args:
        project_slug (str): The slug of the project
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - project_health: Project health metrics including:
                - name: Project name
                - organization: Organization slug
                - statistics: Various time period statistics
                - current_issues: Number of current issues
                - error_rates: Error rates for different time periods
            - error: Error message if the request fails
            
    Example:
        >>> stats = get_project_stats("my-project")
        >>> print(f"Current issues: {stats['project_health']['current_issues']}")
        >>> print("Error rates:", stats['project_health']['error_rates'])
    """
    if not ORG_SLUG:
        return {"error": "SENTRY_ORG_SLUG not set."}
    
    url = f"{BASE_URL}/projects/{ORG_SLUG}/{project_slug}/stats/"
    
    try:
        headers = _get_headers()
        # Get various stats periods
        stats = {}
        for period in ["1h", "24h", "7d", "30d"]:
            params = {"stat": "received", "resolution": "1h" if period == "1h" else "1d"}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            stats[period] = response.json()
        
        # Get current issues
        issues = get_sentry_issues(project_slug, stats_period="24h")
        
        return {
            "project_health": {
                "name": project_slug,
                "organization": ORG_SLUG,
                "statistics": stats,
                "current_issues": len(issues.get("issues", [])),
                "error_rates": {
                    period: sum(data) / len(data) if data else 0
                    for period, data in stats.items()
                }
            }
        }
    except Exception as e:
        return {"error": str(e)}

def get_detailed_stacktrace(project_slug: str, issue_id: str) -> Dict[str, Any]:
    """
    Retrieves and analyzes detailed stacktrace information for a specific issue.
    
    Args:
        project_slug (str): The slug of the project
        issue_id (str): The ID of the issue
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - issue: Detailed issue information
            - stacktrace_analysis: Stacktrace analysis including:
                - total_frames: Total number of stack frames
                - in_app_frames: Number of in-app frames
                - frames: Detailed frame information
                - error_propagation: Root cause and error origin
            - error: Error message if the request fails
            
    Example:
        >>> stacktrace = get_detailed_stacktrace("my-project", "12345")
        >>> print(f"Total frames: {stacktrace['stacktrace_analysis']['total_frames']}")
        >>> print("Root cause:", stacktrace['stacktrace_analysis']['error_propagation']['root_cause'])
    """
    if not ORG_SLUG:
        return {"error": "SENTRY_ORG_SLUG not set."}
    
    try:
        headers = _get_headers()
        
        # Get issue details
        issue_url = f"{BASE_URL}/issues/{issue_id}/"
        response = requests.get(issue_url, headers=headers)
        response.raise_for_status()
        issue_data = response.json()
        
        # Get the latest event for stacktrace
        events_url = f"{BASE_URL}/issues/{issue_id}/events/latest/"
        events_response = requests.get(events_url, headers=headers)
        events_response.raise_for_status()
        event = events_response.json()
        
        # Extract stacktrace information
        stacktrace_data = []
        for entry in event.get("entries", []):
            if entry.get("type") == "exception":
                for exc in entry.get("data", {}).get("values", []):
                    stacktrace = exc.get("stacktrace", {})
                    frames = stacktrace.get("frames", [])
                    
                    # Analyze each frame in detail
                    for frame in frames:
                        frame_data = {
                            "filename": frame.get("filename"),
                            "function": frame.get("function"),
                            "line_number": frame.get("lineno"),
                            "column_number": frame.get("colno"),
                            "context": frame.get("context", []),
                            "variables": frame.get("vars", {}),
                            "is_in_app": frame.get("in_app", False),
                            "module": frame.get("module"),
                            "package": frame.get("package"),
                            "abs_path": frame.get("abs_path"),
                            "pre_context": frame.get("pre_context", []),
                            "post_context": frame.get("post_context", [])
                        }
                        stacktrace_data.append(frame_data)
        
        return {
            "issue": {
                "id": issue_data.get("id"),
                "title": issue_data.get("title"),
                "type": issue_data.get("type"),
                "level": issue_data.get("level"),
                "status": issue_data.get("status"),
                "priority": issue_data.get("priority"),
                "platform": issue_data.get("platform"),
                "count": issue_data.get("count"),
                "userCount": issue_data.get("userCount"),
                "firstSeen": issue_data.get("firstSeen"),
                "lastSeen": issue_data.get("lastSeen"),
                "culprit": issue_data.get("culprit"),
                "metadata": issue_data.get("metadata", {}),
                "permalink": issue_data.get("permalink")
            },
            "stacktrace_analysis": {
                "total_frames": len(stacktrace_data),
                "in_app_frames": len([f for f in stacktrace_data if f["is_in_app"]]),
                "frames": stacktrace_data,
                "error_propagation": {
                    "root_cause": stacktrace_data[-1] if stacktrace_data else None,
                    "error_origin": stacktrace_data[0] if stacktrace_data else None
                }
            }
        }
    except Exception as e:
        return {"error": f"Failed to get detailed stacktrace: {str(e)}"}

def analyze_error_patterns(project_slug: str, days: int = 7) -> Dict[str, Any]:
    """
    Performs comprehensive analysis of error patterns over a time period.
    
    Args:
        project_slug (str): The slug of the project
        days (int, optional): Number of days to analyze. Defaults to 7.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - timeframe: Analysis period
            - total_issues: Total number of issues
            - error_distribution: Distribution by type, level, platform, and priority
            - frequency_analysis: Error frequency analysis
            - platform_analysis: Platform-specific analysis
            - priority_analysis: Priority-based analysis
            - error: Error message if the request fails
            
    Example:
        >>> analysis = analyze_error_patterns("my-project")
        >>> print(f"Total issues: {analysis['total_issues']}")
        >>> print("Platform distribution:", analysis['error_distribution']['by_platform'])
    """
    if not ORG_SLUG:
        return {"error": "SENTRY_ORG_SLUG not set."}
    
    try:
        headers = _get_headers()
        
        # Get all issues for the period
        issues_url = f"{BASE_URL}/projects/{ORG_SLUG}/{project_slug}/issues/"
        response = requests.get(issues_url, headers=headers)
        response.raise_for_status()
        issues = response.json()
        
        # Analyze patterns
        patterns = {
            "timeframe": f"Last {days} days",
            "total_issues": len(issues),
            "error_distribution": {
                "by_type": {},
                "by_level": {},
                "by_platform": {},
                "by_priority": {}
            },
            "frequency_analysis": {
                "total_errors": 0,
                "total_users_affected": 0,
                "most_frequent_errors": []
            },
            "platform_analysis": {},
            "priority_analysis": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # Process each issue
        for issue in issues:
            # Error type distribution
            error_type = issue.get("type", "unknown")
            patterns["error_distribution"]["by_type"][error_type] = patterns["error_distribution"]["by_type"].get(error_type, 0) + 1
            
            # Error level distribution
            level = issue.get("level", "unknown")
            patterns["error_distribution"]["by_level"][level] = patterns["error_distribution"]["by_level"].get(level, 0) + 1
            
            # Platform distribution
            platform = issue.get("platform", "unknown")
            patterns["error_distribution"]["by_platform"][platform] = patterns["error_distribution"]["by_platform"].get(platform, 0) + 1
            
            # Priority distribution
            priority = issue.get("priority", "medium")
            patterns["error_distribution"]["by_priority"][priority] = patterns["error_distribution"]["by_priority"].get(priority, 0) + 1
            patterns["priority_analysis"][priority] = patterns["priority_analysis"].get(priority, 0) + 1
            
            # User impact
            user_count = int(issue.get("userCount", 0))
            patterns["frequency_analysis"]["total_users_affected"] += user_count
            
            # Error count
            error_count = int(issue.get("count", 0))
            patterns["frequency_analysis"]["total_errors"] += error_count
            
            # Platform analysis
            if platform not in patterns["platform_analysis"]:
                patterns["platform_analysis"][platform] = {
                    "total_errors": 0,
                    "total_users": 0,
                    "issues": []
                }
            patterns["platform_analysis"][platform]["total_errors"] += error_count
            patterns["platform_analysis"][platform]["total_users"] += user_count
            patterns["platform_analysis"][platform]["issues"].append({
                "id": issue.get("id"),
                "title": issue.get("title"),
                "count": error_count,
                "userCount": user_count,
                "priority": priority
            })
        
        # Sort and get most frequent errors
        patterns["frequency_analysis"]["most_frequent_errors"] = sorted(
            [{
                "id": issue.get("id"),
                "title": issue.get("title"),
                "count": int(issue.get("count", 0)),
                "userCount": int(issue.get("userCount", 0)),
                "priority": issue.get("priority"),
                "platform": issue.get("platform"),
                "firstSeen": issue.get("firstSeen"),
                "lastSeen": issue.get("lastSeen")
            } for issue in issues],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        return patterns
        
    except Exception as e:
        return {"error": f"Failed to analyze error patterns: {str(e)}"}

if __name__ == "__main__":
    # Test connection first
    print("Testing Sentry connection...")
    connection_test = test_connection()
    print("Connection test result:", json.dumps(connection_test, indent=2))
    
    if "error" not in connection_test:
        # Test project validation
        project_slug = "ibe"
        issue_id = "6634924607"  # Using the issue ID from your example
        
        print(f"\nValidating project '{project_slug}'...")
        project_status = validate_project(project_slug)
        print("Project validation result:", json.dumps(project_status, indent=2))
        
        if "status" in project_status and project_status["status"] == "valid":
            # Test detailed stacktrace
            print(f"\nFetching detailed stacktrace for issue {issue_id}...")
            stacktrace = get_detailed_stacktrace(project_slug, issue_id)
            print("Detailed stacktrace result:", json.dumps(stacktrace, indent=2))
            
            # Test error pattern analysis
            print(f"\nAnalyzing error patterns for project '{project_slug}'...")
            patterns = analyze_error_patterns(project_slug, days=7)
            print("Error patterns analysis:", json.dumps(patterns, indent=2))
        else:
            print("\nSkipping issue analysis due to invalid project")
    else:
        print("\nSkipping all tests due to connection error")
