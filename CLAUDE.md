# Cyberon Project Guide

When working with Crystal code (.cr files, for the client application), refer to CLAUDE_CRYSTAL.md for coding practices.

## Test Commands
- Run all tests: `pytest`
- Run specific test file: `pytest app/tests/test_api.py`
- Run tests with marker: `pytest -m api` (markers: api, upload, visualization, data_loading, integration)
- Run single test: `pytest app/tests/test_api.py::TestAPIEndpoints::test_get_entity`
- Run with verbose output: `pytest -v`
- Run integration tests: `./run_integration_tests.sh`
- Run specific integration test: `./run_integration_tests.sh test_api_integration.py`

## Testing Strategy
- **Unit Tests:** Test individual components with mocked dependencies
- **API Tests:** Test API endpoints with mocked backend services
- **Integration Tests:** Test full API functionality with real backend

The integration tests verify end-to-end functionality without mocks, ensuring:
1. Data persistence
2. API endpoints work with actual data
3. Relationships between entities are correctly managed
4. Filtering and search functionality works correctly
5. Constraints like cascade deletion are enforced

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

## API Structure
- **Entity Endpoints:** CRUD operations for entities (nodes)
- **Relationship Endpoints:** CRUD operations for relationships (edges)
- **Graph Endpoints:** Operations on the graph structure (paths, centrality, etc.)
- **Response Format:** Consistent JSON structure with success/error indicators
- **HTTP Status Codes:** Follow REST conventions (200 OK, 201 Created, 400 Bad Request, 404 Not Found, etc.)