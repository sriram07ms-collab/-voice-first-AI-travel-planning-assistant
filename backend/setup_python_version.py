#!/usr/bin/env python3
"""
Setup Python version for Render deployment.
Checks PYTHON_VERSION environment variable, falls back to runtime.txt
"""
import os
from pathlib import Path

def setup_python_version():
    """Set up Python version from environment variable or runtime.txt"""
    runtime_file = Path("runtime.txt")
    
    # Check for PYTHON_VERSION environment variable
    python_version = os.getenv("PYTHON_VERSION")
    
    if python_version:
        # Remove any 'python-' prefix if present
        if python_version.startswith("python-"):
            python_version = python_version.replace("python-", "")
        
        version_string = f"python-{python_version}"
        print(f"Using Python version from PYTHON_VERSION environment variable: {version_string}")
        
        # Write to runtime.txt
        runtime_file.write_text(version_string + "\n")
        print(f"Updated runtime.txt with: {version_string}")
    else:
        # Fall back to existing runtime.txt if it exists
        if runtime_file.exists():
            current_version = runtime_file.read_text().strip()
            print(f"Using Python version from runtime.txt: {current_version}")
        else:
            # Default fallback
            default_version = "python-3.11.9"
            print(f"Warning: No PYTHON_VERSION env var and no runtime.txt found.")
            print(f"Creating runtime.txt with default: {default_version}")
            runtime_file.write_text(default_version + "\n")

if __name__ == "__main__":
    setup_python_version()
