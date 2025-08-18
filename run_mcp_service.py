#!/usr/bin/env python3
"""
Simple script to run the OGM API MCP service.
This can be called directly by Claude Desktop.
"""

import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Activate virtual environment if it exists
venv_python = os.path.join(project_dir, '.venv', 'bin', 'python')
if os.path.exists(venv_python):
    # Use the virtual environment's Python with proper module path
    env = os.environ.copy()
    env['PYTHONPATH'] = project_dir
    os.execve(venv_python, [venv_python, '-m', 'app.services.mcp_service'] + sys.argv[1:], env)
else:
    # Fall back to system Python with proper module path
    env = os.environ.copy()
    env['PYTHONPATH'] = project_dir
    os.execve(sys.executable, [sys.executable, '-m', 'app.services.mcp_service'] + sys.argv[1:], env)
