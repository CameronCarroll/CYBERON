# Cyberon Project Guide

## Test Commands
- Run all tests: `pytest`
- Run specific test file: `pytest app/tests/test_api.py`
- Run tests with marker: `pytest -m api` (markers: api, upload, visualization, data_loading)
- Run single test: `pytest app/tests/test_api.py::TestAPIEndpoints::test_get_entity`
- Run with verbose output: `pytest -v`

## Code Style Guidelines
- **Imports:** Standard library first, then third-party, then local imports
- **Type Hints:** Use typing module annotations (Dict, List, Set, Tuple, etc.)
- **Functions:** Document with docstrings including Args and Returns
- **Error Handling:** Use try/except blocks with specific exception types
- **Naming:**
  - snake_case for variables, functions, methods
  - PascalCase for classes
  - ALL_CAPS for constants
- **API Endpoints:** Follow RESTful conventions with proper error handling
- **JSON Responses:** Always use jsonify() for Flask API responses