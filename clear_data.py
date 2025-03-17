#!/usr/bin/env python
"""
Simple script to clear data files for testing purposes.
"""
from app.utils import clear_data_files

if __name__ == "__main__":
    print("Clearing data files...")
    clear_data_files()
    print("Done!")