import os
from github import Github, GithubException
from typing import Dict, Any, List, Optional
from datetime import datetime

TOKEN = os.getenv("GITHUB_TOKEN")

def _get_client():
    if not TOKEN: raise ValueError("GITHUB_TOKEN not set.")
    return Github(TOKEN)

def list_repo_issues(repo_full_name):
    try:
        g = _get_client()
        repo = g.get_repo(repo_full_name)
        issues = repo.get_issues(state='open')
        return {"issues": [{"number": i.number, "title": i.title, "url": i.html_url} for i in issues]}
    except GithubException as e: return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e: return {"error": str(e)}

def list_repositories() -> Dict[str, Any]:
    """
    List all repositories accessible by the authenticated user.
    
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "repositories": List[Dict[str, Any]]  # List of repository details
              }
            - {"error": str} if operation fails
            
    Each repository in the list contains:
        - name: Repository name
        - full_name: Full repository name (owner/repo)
        - url: Repository URL
        - description: Repository description
        - private: Whether repository is private
        - stars: Number of stars
        - forks: Number of forks
        
    Example:
        >>> result = list_repositories()
        >>> if "repositories" in result:
        ...     for repo in result["repositories"]:
        ...         print(f"{repo['name']} ({repo['stars']} stars)")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        user = g.get_user()
        repos = user.get_repos()
        return {
            "repositories": [{
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url,
                "description": repo.description,
                "private": repo.private,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count
            } for repo in repos]
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def create_repo(name: str, description: str = "", private: bool = False) -> Dict[str, Any]:
    """
    Create a new GitHub repository.
    
    Args:
        name (str): Name of the repository
        description (str, optional): Repository description. Defaults to "".
        private (bool, optional): Whether repository should be private. Defaults to False.
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "status": "success",
                "repository": Dict[str, Any]  # Repository details
              }
            - {"error": str} if operation fails
            
    Repository details include:
        - name: Repository name
        - full_name: Full repository name
        - url: Repository URL
        - description: Repository description
        - private: Privacy status
        - created_at: Creation timestamp
        
    Example:
        >>> result = create_repo("my-project", "My awesome project", private=True)
        >>> if "status" in result:
        ...     repo = result["repository"]
        ...     print(f"Created: {repo['name']} at {repo['url']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        user = g.get_user()
        repo = user.create_repo(
            name=name,
            description=description,
            private=private,
            has_issues=True,
            has_wiki=True,
            has_downloads=True,
            auto_init=True  # Initialize with README
        )
        return {
            "status": "success",
            "repository": {
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url,
                "description": repo.description,
                "private": repo.private,
                "created_at": repo.created_at.isoformat()
            }
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def fork_repo(repo_full_name: str) -> Dict[str, Any]:
    """
    Fork an existing repository.
    
    Args:
        repo_full_name (str): Full name of the repository to fork (owner/repo)
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "status": "success",
                "forked_repo": Dict[str, Any]  # Forked repository details
              }
            - {"error": str} if operation fails
            
    Forked repository details include:
        - name: Repository name
        - full_name: Full repository name
        - url: Repository URL
        - parent: Original repository name
        
    Example:
        >>> result = fork_repo("octocat/Hello-World")
        >>> if "status" in result:
        ...     fork = result["forked_repo"]
        ...     print(f"Forked to: {fork['full_name']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        user = g.get_user()
        repo = g.get_repo(repo_full_name)
        forked_repo = user.create_fork(repo)
        return {
            "status": "success",
            "forked_repo": {
                "name": forked_repo.name,
                "full_name": forked_repo.full_name,
                "url": forked_repo.html_url,
                "parent": repo.full_name
            }
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def create_issue(repo_full_name: str, title: str, body: str = "", labels: List[str] = None) -> Dict[str, Any]:
    """
    Create a new issue in a repository.
    
    Args:
        repo_full_name (str): Full name of the repository (owner/repo)
        title (str): Issue title
        body (str, optional): Issue description. Defaults to "".
        labels (List[str], optional): List of labels to apply. Defaults to None.
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "status": "success",
                "issue": Dict[str, Any]  # Issue details
              }
            - {"error": str} if operation fails
            
    Issue details include:
        - number: Issue number
        - title: Issue title
        - url: Issue URL
        - state: Issue state
        - created_at: Creation timestamp
        
    Example:
        >>> result = create_issue("owner/repo", "Bug fix", "Fix login issue", ["bug"])
        >>> if "status" in result:
        ...     issue = result["issue"]
        ...     print(f"Created issue #{issue['number']}: {issue['title']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_full_name)
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels or []
        )
        return {
            "status": "success",
            "issue": {
                "number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
                "state": issue.state,
                "created_at": issue.created_at.isoformat()
            }
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def create_pull_request(repo_full_name: str, title: str, head: str, base: str = "main", body: str = "") -> Dict[str, Any]:
    """
    Create a pull request.
    
    Args:
        repo_full_name (str): Full name of the repository (owner/repo)
        title (str): Pull request title
        head (str): Branch containing changes
        base (str, optional): Branch to merge into. Defaults to "main".
        body (str, optional): Pull request description. Defaults to "".
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "status": "success",
                "pull_request": Dict[str, Any]  # PR details
              }
            - {"error": str} if operation fails
            
    PR details include:
        - number: PR number
        - title: PR title
        - url: PR URL
        - state: PR state
        - created_at: Creation timestamp
        
    Example:
        >>> result = create_pull_request("owner/repo", "Add feature", "feature-branch")
        >>> if "status" in result:
        ...     pr = result["pull_request"]
        ...     print(f"Created PR #{pr['number']}: {pr['title']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_full_name)
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )
        return {
            "status": "success",
            "pull_request": {
                "number": pr.number,
                "title": pr.title,
                "url": pr.html_url,
                "state": pr.state,
                "created_at": pr.created_at.isoformat()
            }
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def search_repositories(query: str, sort: str = "stars", order: str = "desc", limit: int = 10) -> Dict[str, Any]:
    """
    Search for repositories.
    
    Args:
        query (str): Search query
        sort (str, optional): Sort criteria (stars, forks, updated). Defaults to "stars".
        order (str, optional): Sort order (asc, desc). Defaults to "desc".
        limit (int, optional): Maximum number of results. Defaults to 10.
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "repositories": List[Dict[str, Any]]  # List of repository details
              }
            - {"error": str} if operation fails
            
    Repository details include:
        - name: Repository name
        - full_name: Full repository name
        - url: Repository URL
        - description: Repository description
        - stars: Number of stars
        - forks: Number of forks
        - language: Primary language
        
    Example:
        >>> result = search_repositories("python web framework", sort="stars")
        >>> if "repositories" in result:
        ...     for repo in result["repositories"]:
        ...         print(f"{repo['name']} ({repo['stars']} stars)")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        repos = g.search_repositories(
            query=query,
            sort=sort,
            order=order
        )
        return {
            "repositories": [{
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language
            } for repo in repos[:limit]]
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def search_code(query: str, repo: Optional[str] = None, language: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Search for code in repositories.
    
    Args:
        query (str): Search query
        repo (Optional[str], optional): Repository to search in. Defaults to None.
        language (Optional[str], optional): Language to filter by. Defaults to None.
        limit (int, optional): Maximum number of results. Defaults to 10.
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "results": List[Dict[str, Any]]  # List of code search results
              }
            - {"error": str} if operation fails
            
    Search results include:
        - name: File name
        - path: File path
        - url: File URL
        - repository: Repository name
        - language: File language
        
    Example:
        >>> result = search_code("def main", repo="owner/repo", language="python")
        >>> if "results" in result:
        ...     for item in result["results"]:
        ...         print(f"Found in {item['path']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        search_query = query
        if repo:
            search_query += f" repo:{repo}"
        if language:
            search_query += f" language:{language}"
            
        results = g.search_code(search_query)
        return {
            "results": [{
                "name": result.name,
                "path": result.path,
                "url": result.html_url,
                "repository": result.repository.full_name,
                "language": result.language
            } for result in results[:limit]]
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def get_pull_requests(repo_full_name: str, state: str = "open") -> Dict[str, Any]:
    """
    List pull requests in a repository.
    
    Args:
        repo_full_name (str): Full name of the repository (owner/repo)
        state (str, optional): PR state (open, closed, all). Defaults to "open".
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "pull_requests": List[Dict[str, Any]]  # List of PR details
              }
            - {"error": str} if operation fails
            
    PR details include:
        - number: PR number
        - title: PR title
        - url: PR URL
        - state: PR state
        - created_at: Creation timestamp
        - user: Author username
        - head: Source branch
        - base: Target branch
        
    Example:
        >>> result = get_pull_requests("owner/repo", state="open")
        >>> if "pull_requests" in result:
        ...     for pr in result["pull_requests"]:
        ...         print(f"PR #{pr['number']}: {pr['title']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_full_name)
        prs = repo.get_pulls(state=state)
        return {
            "pull_requests": [{
                "number": pr.number,
                "title": pr.title,
                "url": pr.html_url,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "user": pr.user.login,
                "head": pr.head.ref,
                "base": pr.base.ref
            } for pr in prs]
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def review_pull_request(repo_full_name: str, pr_number: int, body: str, event: str = "APPROVE") -> Dict[str, Any]:
    """
    Review a pull request.
    
    Args:
        repo_full_name (str): Full name of the repository (owner/repo)
        pr_number (int): Pull request number
        body (str): Review comment
        event (str, optional): Review event (APPROVE, REQUEST_CHANGES, COMMENT).
                             Defaults to "APPROVE".
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "status": "success",
                "review": Dict[str, Any]  # Review details
              }
            - {"error": str} if operation fails
            
    Review details include:
        - id: Review ID
        - state: Review state
        - body: Review comment
        - submitted_at: Submission timestamp
        
    Example:
        >>> result = review_pull_request("owner/repo", 123, "LGTM!", "APPROVE")
        >>> if "status" in result:
        ...     review = result["review"]
        ...     print(f"Submitted review: {review['state']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        review = pr.create_review(
            body=body,
            event=event  # APPROVE, REQUEST_CHANGES, or COMMENT
        )
        return {
            "status": "success",
            "review": {
                "id": review.id,
                "state": review.state,
                "body": review.body,
                "submitted_at": review.submitted_at.isoformat()
            }
        }
    except GithubException as e:
        return {"error": f"GH Error: {e.data.get('message', str(e))}"}
    except Exception as e:
        return {"error": str(e)}

def update_readme(repo_full_name: str, content: str, commit_message: str = "Update README.md") -> Dict[str, Any]:
    """
    Update the README.md file in a repository.
    
    Args:
        repo_full_name (str): Full name of the repository (owner/repo)
        content (str): New content for the README file
        commit_message (str, optional): Commit message. Defaults to "Update README.md".
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "status": "success",
                "message": str,  # Success message
                "repository": str,  # Repository name
                "commit_message": str  # Commit message used
              }
            - {"error": str} if operation fails
            
    Example:
        >>> content = "# My Project\n\nThis is my awesome project."
        >>> result = update_readme("owner/repo", content)
        >>> if "status" in result:
        ...     print(result["message"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        # Split repo name into owner and repo
        owner, repo = repo_full_name.split('/')
        
        # Get the repository
        repository = _get_client().get_repo(repo_full_name)
        
        try:
            # Try to get the existing README
            contents = repository.get_contents("README.md")
            # Update existing README
            repository.update_file(
                path="README.md",
                message=commit_message,
                content=content,
                sha=contents.sha
            )
            action = "updated"
        except GithubException.UnknownObjectException:
            # Create new README if it doesn't exist
            repository.create_file(
                path="README.md",
                message=commit_message,
                content=content
            )
            action = "created"
            
        return {
            "status": "success",
            "message": f"README.md {action} successfully",
            "repository": repo_full_name,
            "commit_message": commit_message
        }
        
    except Exception as e:
        return {"error": f"Failed to update README: {str(e)}"}

print(list_repositories())