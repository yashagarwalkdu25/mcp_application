from pathlib import Path
import os
from pathlib import Path
import shutil
from datetime import datetime
import fnmatch
from typing import List, Dict, Any


def read_file(file_path: str) -> Dict[str, Any]:
    """
    Read the contents of a file.
    
    Args:
        file_path (str): Path to the file to read
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {"content": str} with the file contents if successful
            - {"error": str} with error message if operation fails
            
    Example:
        >>> result = read_file("example.txt")
        >>> if "content" in result:
        ...     print(result["content"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        p = Path(file_path).resolve()
        if not p.is_file(): return {"error": f"Not a file: {file_path}"}
        return {"content": p.read_text(encoding='utf-8')}
    except Exception as e: return {"error": str(e)}

def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file, creating parent directories if they don't exist.
    
    Args:
        file_path (str): Path where the file should be written
        content (str): Content to write to the file
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {"status": "success", "message": str} if successful
            - {"error": str} if operation fails
            
    Example:
        >>> result = write_file("new_file.txt", "Hello, World!")
        >>> if "status" in result:
        ...     print(result["message"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        file_path = "/Users/yashagarwal/Downloads/"+file_path
        p = Path(file_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        return {"status": "success", "message": f"Wrote to {file_path}"}
    except Exception as e: return {"error": str(e)}

def list_directory(dir_path: str) -> Dict[str, Any]:
    """
    List contents of a directory with detailed information about each item.
    
    Args:
        dir_path (str): Path to the directory to list
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "items": List[Dict[str, Any]],  # List of items with details
                "path": str,                     # Absolute path of directory
                "total_items": int               # Total number of items
              }
            - {"error": str} if operation fails
            
    Each item in the items list contains:
        - name: Item name
        - is_dir: Whether item is a directory
        - size: File size in bytes (0 for directories)
        - modified: Last modification timestamp
        
    Example:
        >>> result = list_directory("/path/to/dir")
        >>> if "items" in result:
        ...     for item in result["items"]:
        ...         print(f"{item['name']} ({'dir' if item['is_dir'] else 'file'})")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    print(dir_path)
    try:
        # Convert to absolute path and resolve any symlinks
        p = Path(dir_path).resolve()
        
        # Check if path exists
        if not p.exists():
            return {"error": f"Directory does not exist: {dir_path}"}
            
        # Check if it's a directory
        if not p.is_dir():
            return {"error": f"Not a directory: {dir_path}"}
            
        # Check if we have permission to read the directory
        if not os.access(p, os.R_OK):
            return {"error": f"No permission to read directory: {dir_path}"}
            
        # Get directory contents with more details
        items = []
        for item in p.iterdir():
            try:
                item_info = {
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": item.stat().st_mtime
                }
                items.append(item_info)
            except (PermissionError, Exception) as e:
                print(f"Error accessing {item}: {e}")
                continue
                
        return {
            "items": items,
            "path": str(p),
            "total_items": len(items)
        }
        
    except PermissionError as e:
        return {"error": f"Permission denied: {str(e)}"}
    except Exception as e:
        return {"error": f"Error listing directory: {str(e)}"}

def create_directory(dir_path: str) -> Dict[str, Any]:
    """
    Create a new directory and any necessary parent directories.
    
    Args:
        dir_path (str): Path of the directory to create
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {"status": "success", "message": str} if successful
            - {"error": str} if operation fails
            
    Example:
        >>> result = create_directory("new/directory/path")
        >>> if "status" in result:
        ...     print(result["message"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        p = Path(dir_path).resolve()
        if p.exists():
            return {"error": f"Directory already exists: {dir_path}"}
        p.mkdir(parents=True, exist_ok=True)
        return {"status": "success", "message": f"Created directory: {dir_path}"}
    except Exception as e:
        return {"error": str(e)}

def delete_directory(dir_path: str, recursive: bool = False) -> Dict[str, Any]:
    """
    Delete a directory, optionally with all its contents.
    
    Args:
        dir_path (str): Path of the directory to delete
        recursive (bool, optional): If True, delete directory and all contents.
                                  If False, only delete if empty. Defaults to False.
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {"status": "success", "message": str} if successful
            - {"error": str} if operation fails
            
    Example:
        >>> # Delete empty directory
        >>> result = delete_directory("empty_dir")
        >>> # Delete directory and all contents
        >>> result = delete_directory("dir_with_contents", recursive=True)
    """
    try:
        p = Path(dir_path).resolve()
        if not p.exists():
            return {"error": f"Directory does not exist: {dir_path}"}
        if not p.is_dir():
            return {"error": f"Not a directory: {dir_path}"}
            
        if recursive:
            shutil.rmtree(p)
        else:
            p.rmdir()  # Will fail if directory is not empty
        return {"status": "success", "message": f"Deleted directory: {dir_path}"}
    except Exception as e:
        return {"error": str(e)}

def search_files(dir_path: str, pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
    """
    Search for files matching a pattern in a directory.
    
    Args:
        dir_path (str): Directory to search in
        pattern (str, optional): File pattern to match (e.g., "*.txt"). Defaults to "*".
        recursive (bool, optional): Whether to search in subdirectories. Defaults to False.
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "matches": List[Dict[str, Any]],  # List of matching files
                "total_matches": int,              # Number of matches
                "search_path": str,                # Absolute search path
                "pattern": str                     # Search pattern used
              }
            - {"error": str} if operation fails
            
    Example:
        >>> # Search for all .txt files
        >>> result = search_files("/path/to/dir", "*.txt", recursive=True)
        >>> if "matches" in result:
        ...     print(f"Found {result['total_matches']} matches")
        ...     for match in result["matches"]:
        ...         print(f"- {match['path']}")
    """
    try:
        p = Path(dir_path).resolve()
        if not p.exists():
            return {"error": f"Directory does not exist: {dir_path}"}
        if not p.is_dir():
            return {"error": f"Not a directory: {dir_path}"}
            
        matches = []
        if recursive:
            search_path = p.rglob(pattern)
        else:
            search_path = p.glob(pattern)
            
        for item in search_path:
            if item.is_file():  # Only include files, not directories
                try:
                    matches.append({
                        "path": str(item),
                        "name": item.name,
                        "size": item.stat().st_size,
                        "modified": item.stat().st_mtime
                    })
                except Exception as e:
                    print(f"Error accessing {item}: {e}")
                    continue
                    
        return {
            "matches": matches,
            "total_matches": len(matches),
            "search_path": str(p),
            "pattern": pattern
        }
    except Exception as e:
        return {"error": str(e)}

def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Get detailed metadata about a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {
                "path": str,           # Absolute file path
                "name": str,           # File name
                "size": int,           # File size in bytes
                "created": float,      # Creation timestamp
                "modified": float,     # Last modification timestamp
                "accessed": float,     # Last access timestamp
                "is_symlink": bool,    # Whether file is a symlink
                "extension": str,      # File extension
                "parent": str          # Parent directory path
              }
            - {"error": str} if operation fails
            
    Example:
        >>> result = get_file_metadata("example.txt")
        >>> if "size" in result:
        ...     print(f"File: {result['name']}")
        ...     print(f"Size: {result['size']} bytes")
        ...     print(f"Modified: {result['modified']}")
    """
    try:
        p = Path(file_path).resolve()
        if not p.exists():
            return {"error": f"File does not exist: {file_path}"}
        if not p.is_file():
            return {"error": f"Not a file: {file_path}"}
            
        stat = p.stat()
        return {
            "path": str(p),
            "name": p.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "is_symlink": p.is_symlink(),
            "extension": p.suffix,
            "parent": str(p.parent)
        }
    except Exception as e:
        return {"error": str(e)}

def delete_file(file_path: str) -> Dict[str, Any]:
    """
    Delete a file.
    
    Args:
        file_path (str): Path to the file to delete
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {"status": "success", "message": str} if successful
            - {"error": str} if operation fails
            
    Example:
        >>> result = delete_file("unwanted.txt")
        >>> if "status" in result:
        ...     print(result["message"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        p = Path(file_path).resolve()
        if not p.exists():
            return {"error": f"File does not exist: {file_path}"}
        if not p.is_file():
            return {"error": f"Not a file: {file_path}"}
            
        p.unlink()
        return {"status": "success", "message": f"Deleted file: {file_path}"}
    except Exception as e:
        return {"error": str(e)}

def copy_file(src_path: str, dst_path: str) -> Dict[str, Any]:
    """
    Copy a file from source to destination.
    
    Args:
        src_path (str): Source file path
        dst_path (str): Destination file path
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {"status": "success", "message": str} if successful
            - {"error": str} if operation fails
            
    Example:
        >>> result = copy_file("source.txt", "destination.txt")
        >>> if "status" in result:
        ...     print(result["message"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        src = Path(src_path).resolve()
        dst = Path(dst_path).resolve()
        
        if not src.exists():
            return {"error": f"Source file does not exist: {src_path}"}
        if not src.is_file():
            return {"error": f"Source is not a file: {src_path}"}
            
        shutil.copy2(src, dst)
        return {"status": "success", "message": f"Copied {src_path} to {dst_path}"}
    except Exception as e:
        return {"error": str(e)}

def move_file(src_path: str, dst_path: str) -> Dict[str, Any]:
    """
    Move a file from source to destination.
    
    Args:
        src_path (str): Source file path
        dst_path (str): Destination file path
        
    Returns:
        Dict[str, Any]: A dictionary containing either:
            - {"status": "success", "message": str} if successful
            - {"error": str} if operation fails
            
    Example:
        >>> result = move_file("old_location.txt", "new_location.txt")
        >>> if "status" in result:
        ...     print(result["message"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        src = Path(src_path).resolve()
        dst = Path(dst_path).resolve()
        
        if not src.exists():
            return {"error": f"Source file does not exist: {src_path}"}
        if not src.is_file():
            return {"error": f"Source is not a file: {src_path}"}
            
        shutil.move(src, dst)
        return {"status": "success", "message": f"Moved {src_path} to {dst_path}"}
    except Exception as e:
        return {"error": str(e)}

# --- Add other functions (create_dir, delete_dir, etc.) ---