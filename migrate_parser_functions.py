#!/usr/bin/env python3
"""
Script to migrate application code from old parser function names to new ones.
Updates imports and function calls in all Python files in the project.
"""

import os
import re
from pathlib import Path

# Define replacement patterns
REPLACEMENTS = [
    # Function name replacements
    (r'extract_text_to_json\(', 'extract_markdown_to_json('),
    (r'parse_ontology_text\(', 'parse_markdown_ontology('),
    
    # Import replacements
    (r'from app\.utils\.ontology_parser import extract_text_to_json', 
     'from app.utils.ontology_parser import extract_markdown_to_json'),
    (r'from app\.utils\.ontology_parser import parse_ontology_text', 
     'from app.utils.ontology_parser import parse_markdown_ontology'),
    
    # Combined import replacements
    (r'from app\.utils\.ontology_parser import (.*?)extract_markdown_to_json(.*?)', 
     r'from app.utils.ontology_parser import \1extract_markdown_to_json\2'),
    (r'from app\.utils\.ontology_parser import (.*?)parse_markdown_ontology(.*?)', 
     r'from app.utils.ontology_parser import \1parse_markdown_ontology\2'),
]

def update_file(file_path):
    """Update a single file, replacing old function names with new ones."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        print(f"Updating {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def find_and_update_files(root_dir):
    """Find and update all Python files in the project."""
    root_path = Path(root_dir)
    python_files = list(root_path.glob('**/*.py'))
    
    updated_count = 0
    for file_path in python_files:
        # Skip the ontology_parser.py file itself
        if file_path.name == 'ontology_parser.py':
            continue
            
        if update_file(file_path):
            updated_count += 1
    
    return updated_count

def main():
    """Main function to run the migration."""
    # Get the project root directory
    project_root = os.path.abspath(os.path.dirname(__file__))
    
    print(f"Scanning Python files in {project_root}")
    updated_count = find_and_update_files(project_root)
    
    print(f"Updated {updated_count} files with new function names")
    print("Migration complete.")

if __name__ == '__main__':
    main()
