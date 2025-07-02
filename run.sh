#!/bin/bash
# Instagram to Etsy Automation Runner
# 
# This script provides a simple interface to run the Instagram-to-Etsy automation workflow.
# It handles activating the virtual environment and running the main application with common options.

# Exit on error
set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists, create if not
if [ ! -d "myenv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv myenv
    source myenv/bin/activate
    pip install -r requirements.txt
else
    source myenv/bin/activate
fi

# Command line argument parsing
WORKFLOW="full"
LIMIT=10
CONTENT_FILTER=false
LANDSCAPE_ONLY=false
SKIP_UPLOAD=false
DEBUG=false
INPUT_DIR="data/raw"
OUTPUT_DIR="data/processed"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workflow|-w)
            WORKFLOW="$2"
            shift 2
            ;;
        --limit|-l)
            LIMIT="$2"
            shift 2
            ;;
        --instagram-user|-u)
            INSTAGRAM_USER="$2"
            shift 2
            ;;
        --content-filter|-cf)
            CONTENT_FILTER=true
            shift
            ;;
        --filter-terms|-ft)
            FILTER_TERMS="$2"
            shift 2
            ;;
        --landscape-only|-lo)
            LANDSCAPE_ONLY=true
            shift
            ;;
        --skip-upload|-s)
            SKIP_UPLOAD=true
            shift
            ;;
        --debug|-d)
            DEBUG=true
            shift
            ;;
        --input-dir|-i)
            INPUT_DIR="$2"
            shift 2
            ;;
        --output-dir|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Instagram to Etsy Automation"
            echo ""
            echo "Usage: ./run.sh [options]"
            echo ""
            echo "Options:"
            echo "  --workflow, -w WORKFLOW     Workflow to run (full, acquisition, processing, pod, etsy, discovery)"
            echo "  --limit, -l LIMIT           Maximum number of images to process (default: 10)"
            echo "  --instagram-user, -u USER   Instagram username to scrape (overrides config)"
            echo "  --content-filter, -cf       Enable content-based filtering with Google Vision API"
            echo "  --filter-terms, -ft TERMS   Comma-separated list of content terms to filter by"
            echo "  --landscape-only, -lo       Filter for landscape images only"
            echo "  --skip-upload, -s           Skip uploading to Printify/Etsy"
            echo "  --debug, -d                 Enable debug logging"
            echo "  --input-dir, -i DIR         Input directory for images (default: data/raw)"
            echo "  --output-dir, -o DIR        Output directory for processed images (default: data/processed)"
            echo "  --help, -h                  Show this help message"
            exit 0
            ;;
        --test)
            echo "Running integration test..."
            python test_integration.py
            exit $?
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python src/main.py --workflow $WORKFLOW --limit $LIMIT --input-dir $INPUT_DIR --output-dir $OUTPUT_DIR"

# Add optional parameters
if [ ! -z "$INSTAGRAM_USER" ]; then
    CMD="$CMD --instagram-user $INSTAGRAM_USER"
fi

if [ "$CONTENT_FILTER" = true ]; then
    CMD="$CMD --content-filter"
fi

if [ ! -z "$FILTER_TERMS" ]; then
    CMD="$CMD --filter-terms \"$FILTER_TERMS\""
fi

if [ "$LANDSCAPE_ONLY" = true ]; then
    CMD="$CMD --landscape-only"
fi

if [ "$SKIP_UPLOAD" = true ]; then
    CMD="$CMD --skip-upload"
fi

if [ "$DEBUG" = true ]; then
    CMD="$CMD --debug"
fi

# Run the command
echo "Running: $CMD"
eval "$CMD"

# Deactivate virtual environment
deactivate

echo "Done."
