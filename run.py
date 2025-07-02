#!/usr/bin/env python3
"""
Instagram to Etsy Automation - Main Runner

This script provides a convenient entry point to run the entire workflow.
"""

import os
import sys
import argparse
from src.main import parse_arguments, run_workflow

def main():
    """Main entry point for the application."""
    # Parse arguments
    args = parse_arguments()
    
    # Run the workflow
    metrics = run_workflow(args)
    
    # Exit with appropriate code
    sys.exit(0 if metrics['errors'] == 0 else 1)

if __name__ == "__main__":
    # Ensure we're running from the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Run the main function
    main()
