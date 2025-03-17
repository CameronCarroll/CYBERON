# Cyberon Testing Strategy

This document outlines the testing strategy for the Cyberon knowledge graph application.

## Test Types

The testing suite includes multiple types of tests:

1. **Unit Tests** - Testing individual components in isolation with mocked dependencies
2. **API Tests** - Testing API endpoints with mocked backend services
3. **Integration Tests** - Testing the full API request/response cycle with a real backend

## Test Markers

Tests are organized using pytest markers to allow running specific test categories:

- `api`: Tests for the RESTful API endpoints
- `upload`: Tests for file upload functionality
- `visualization`: Tests for visualization functionality
- `data_loading`: Tests for data loading functionality
- `integration`: End-to-end integration tests for the API

## Running Tests

### All Tests

```bash
pytest
```

### Running by Marker

Run all API tests:
```bash
pytest -m api
```

Run all integration tests:
```bash
pytest -m integration
```

### Running a Specific Test File

```bash
pytest app/tests/test_api_integration.py
```

### Running with Verbose Output

```bash
pytest -v
```

## Integration Test Strategy

The integration tests (`test_api_integration.py`) test the complete API functionality with a real database backend:

1. **Setup**: Creates a temporary data directory and initializes the application with a clean knowledge graph
2. **Entity CRUD**: Tests creating, reading, updating, and deleting entities
3. **Relationship CRUD**: Tests creating, reading, updating, and deleting relationships
4. **Constraints**: Tests relationship constraints like cascade deletion
5. **Graph Operations**: Tests path finding, entity relations, and graph statistics
6. **Data Persistence**: Tests that changes are properly persisted to disk and can be reloaded
7. **Error Handling**: Tests proper error responses for invalid operations

The integration tests do not use mocks, but instead test the entire stack from the API endpoint through to the data storage layer.

## Mocked API Tests

The mock-based API tests (`test_entity_api.py`, `test_relationship_api.py`, and `test_graph_api.py`) provide faster execution for testing API-level behavior:

1. **Setup**: Creates a test client with a mocked query engine
2. **Isolating Logic**: Tests the API endpoint logic without database interaction
3. **Input Validation**: Tests API input validation and error handling
4. **Response Formatting**: Tests consistent API response structure

These tests are faster and provide more focused coverage of the API layer.

## Writing New Tests

When adding new functionality:

1. Create unit tests for new components
2. Add API tests to verify endpoint behavior with mocked backends
3. Add integration tests to verify full system functionality

Always include tests for:
- Normal operation (happy path)
- Edge cases
- Input validation
- Error handling