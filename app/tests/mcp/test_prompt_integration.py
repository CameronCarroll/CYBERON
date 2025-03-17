"""
Tests for the MCP prompt functionality.

This module contains tests for the MCP prompt handlers.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

# Import handlers
from app.mcp.handlers.prompts import (
    set_query_engine,
    list_prompts_handler,
    get_prompt_handler,
    register_default_prompts,
    process_prompt_template,
    entity_analysis_prompt_handler,
    concept_comparison_prompt_handler,
    ontology_exploration_prompt_handler,
    hierarchy_analysis_prompt_handler,
    central_concepts_prompt_handler
)

class TestPromptHandlers:
    """Tests for the MCP prompt handlers."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the test environment."""
        # Register the default prompts
        register_default_prompts()
        
        # Create a mock query engine
        self.mock_query_engine = MagicMock()
        set_query_engine(self.mock_query_engine)
        
        # Configure mock for entity query returns different values based on entity_id
        def mock_query_entity(entity_id):
            if entity_id == "entity1":
                return {
                    "id": "entity1",
                    "attributes": {
                        "label": "Entity 1",
                        "type": "concept",
                        "description": "Test entity description"
                    },
                    "incoming": [
                        {"id": "entity2", "label": "Entity 2", "relationship": "influences"}
                    ],
                    "outgoing": [
                        {"id": "entity3", "label": "Entity 3", "relationship": "part_of"}
                    ]
                }
            elif entity_id == "entity2":
                return {
                    "id": "entity2",
                    "attributes": {
                        "label": "Entity 2",
                        "type": "concept",
                        "description": "Test entity 2 description"
                    },
                    "incoming": [],
                    "outgoing": []
                }
            else:
                return {
                    "id": entity_id,
                    "attributes": {
                        "label": entity_id.capitalize(),
                        "type": "concept"
                    },
                    "incoming": [],
                    "outgoing": []
                }
        
        self.mock_query_engine.query_entity.side_effect = mock_query_entity
        
        # Configure mock for paths
        mock_paths = [
            [
                {"id": "entity1", "label": "Entity 1", "type": "concept"},
                {"id": "rel1", "type": "related_to"},
                {"id": "entity2", "label": "Entity 2", "type": "concept"}
            ]
        ]
        self.mock_query_engine.find_paths.return_value = mock_paths
        
        # Configure mock for search
        mock_search_results = [
            {"id": "entity1", "label": "Entity 1", "type": "concept", "match_score": 0.9},
            {"id": "entity2", "label": "Entity 2", "type": "concept", "match_score": 0.7}
        ]
        self.mock_query_engine.search_entities.return_value = mock_search_results
        
        # Configure mock for ontology summary
        mock_summary = {
            "node_count": 100,
            "edge_count": 150,
            "entity_types": {"concept": 50, "person": 30, "system": 20}
        }
        self.mock_query_engine.generate_ontology_summary.return_value = mock_summary
        
        # Configure mock for sections
        mock_sections = [
            {
                "section_num": 1,
                "title": "Test Section",
                "title_match": True,
                "subsection_matches": [
                    {"name": "Test Subsection", "type": "subsection_title"}
                ]
            }
        ]
        self.mock_query_engine.find_section_by_topic.return_value = mock_sections
        
        # Configure mock for concept hierarchy
        mock_hierarchy = {
            "root_nodes": [
                {"id": "root1", "label": "Root 1", "type": "concept", "max_depth": 3},
                {"id": "root2", "label": "Root 2", "type": "concept", "max_depth": 2}
            ],
            "hierarchies": {
                "root1": {
                    "0": [{"id": "root1", "label": "Root 1", "type": "concept"}],
                    "1": [{"id": "entity1", "label": "Entity 1", "type": "concept"}],
                    "2": [{"id": "entity2", "label": "Entity 2", "type": "concept"}],
                    "3": [{"id": "entity3", "label": "Entity 3", "type": "concept"}]
                },
                "root2": {
                    "0": [{"id": "root2", "label": "Root 2", "type": "concept"}],
                    "1": [{"id": "entity4", "label": "Entity 4", "type": "concept"}],
                    "2": [{"id": "entity5", "label": "Entity 5", "type": "concept"}]
                }
            }
        }
        self.mock_query_engine.analyze_concept_hierarchy.return_value = mock_hierarchy
        
        # Configure mock for central entities
        mock_central_entities = [
            {"id": "entity1", "label": "Entity 1", "centrality": 0.9, "type": "concept"},
            {"id": "entity2", "label": "Entity 2", "centrality": 0.8, "type": "person"},
            {"id": "entity3", "label": "Entity 3", "centrality": 0.7, "type": "concept"}
        ]
        self.mock_query_engine.get_central_entities.return_value = mock_central_entities
        
        # Set up a mock transport ID
        self.transport_id = "test-transport"
        
        yield
        
        # Clean up after test
        set_query_engine(None)
    
    def test_list_prompts_handler(self):
        """Test the list_prompts_handler function."""
        # Call the handler
        result = list_prompts_handler({}, self.transport_id)
        
        # Verify result
        assert "prompts" in result
        assert len(result["prompts"]) > 0
        
        # Verify prompt format
        for prompt in result["prompts"]:
            assert "name" in prompt
            assert "description" in prompt
            assert "parameter_schema" in prompt
            assert "usage_examples" in prompt
    
    def test_get_prompt_handler_entity_analysis(self):
        """Test the get_prompt_handler function for entity analysis."""
        # Call the handler
        result = get_prompt_handler({
            "name": "cyberon.prompts.entity_analysis",
            "params": {
                "entity_id": "entity1"
            }
        }, self.transport_id)
        
        # Verify result
        assert "name" in result
        assert "timestamp" in result
        assert "prompt" in result
        assert "context" in result
        assert "Entity 1" in result["prompt"]
        assert "entity" in result["context"]
        
        # Verify mock was called correctly
        self.mock_query_engine.query_entity.assert_called_with("entity1")
    
    def test_get_prompt_handler_concept_comparison(self):
        """Test the get_prompt_handler function for concept comparison."""
        # Call the handler
        result = get_prompt_handler({
            "name": "cyberon.prompts.concept_comparison",
            "params": {
                "concept1_id": "entity1",
                "concept2_id": "entity2"
            }
        }, self.transport_id)
        
        # Verify result
        assert "name" in result
        assert "timestamp" in result
        assert "prompt" in result
        assert "context" in result
        assert "concept1" in result["context"]
        assert "concept2" in result["context"]
        assert "connections" in result["context"]
        
        # Verify mocks were called correctly
        self.mock_query_engine.query_entity.assert_any_call("entity1")
        self.mock_query_engine.query_entity.assert_any_call("entity2")
        self.mock_query_engine.find_paths.assert_called_with("entity1", "entity2", 3)
    
    def test_get_prompt_handler_ontology_exploration(self):
        """Test the get_prompt_handler function for ontology exploration."""
        # Call the handler
        result = get_prompt_handler({
            "name": "cyberon.prompts.ontology_exploration",
            "params": {
                "topic": "test topic"
            }
        }, self.transport_id)
        
        # Verify result
        assert "name" in result
        assert "timestamp" in result
        assert "prompt" in result
        assert "context" in result
        assert "test topic" in result["prompt"]
        assert "search_results" in result["context"]
        assert "ontology_summary" in result["context"]
        assert "related_sections" in result["context"]
        
        # Verify mocks were called correctly
        self.mock_query_engine.search_entities.assert_called_with("test topic")
        self.mock_query_engine.generate_ontology_summary.assert_called_once()
        self.mock_query_engine.find_section_by_topic.assert_called_with("test topic")
    
    def test_get_prompt_handler_hierarchy_analysis(self):
        """Test the get_prompt_handler function for hierarchy analysis."""
        # Call the handler
        result = get_prompt_handler({
            "name": "cyberon.prompts.hierarchy_analysis",
            "params": {}
        }, self.transport_id)
        
        # Verify result
        assert "name" in result
        assert "timestamp" in result
        assert "prompt" in result
        assert "context" in result
        assert "root_nodes" in result["context"]
        assert "total_roots" in result["context"]
        assert "max_depth" in result["context"]
        
        # Call with specific root
        result = get_prompt_handler({
            "name": "cyberon.prompts.hierarchy_analysis",
            "params": {
                "root_concept_id": "root1"
            }
        }, self.transport_id)
        
        # Verify specific result
        assert "root_concept" in result["context"]
        assert "hierarchy" in result["context"]
        assert "max_depth" in result["context"]
        assert result["context"]["root_concept"]["id"] == "root1"
        
        # Verify mock was called correctly
        self.mock_query_engine.analyze_concept_hierarchy.assert_called()
    
    def test_get_prompt_handler_central_concepts(self):
        """Test the get_prompt_handler function for central concepts."""
        # Call the handler
        result = get_prompt_handler({
            "name": "cyberon.prompts.central_concepts",
            "params": {
                "limit": 5
            }
        }, self.transport_id)
        
        # Verify result
        assert "name" in result
        assert "timestamp" in result
        assert "prompt" in result
        assert "context" in result
        assert "central_entities" in result["context"]
        assert "entities_by_type" in result["context"]
        assert "total" in result["context"]
        
        # Call with entity type
        result = get_prompt_handler({
            "name": "cyberon.prompts.central_concepts",
            "params": {
                "limit": 5,
                "entity_type": "concept"
            }
        }, self.transport_id)
        
        # Verify entity type is included in prompt
        assert "concept" in result["prompt"]
        
        # Verify mock was called correctly
        self.mock_query_engine.get_central_entities.assert_called_with(5, "concept")
    
    def test_get_prompt_handler_not_found(self):
        """Test the get_prompt_handler function with non-existent prompt."""
        # Call the handler
        result = get_prompt_handler({
            "name": "non_existent_prompt",
            "params": {}
        }, self.transport_id)
        
        # Verify result
        assert "error" in result
    
    def test_process_prompt_template(self):
        """Test the process_prompt_template function."""
        # Simple template
        template = "Hello, {name}!"
        params = {"name": "World"}
        result = process_prompt_template(template, params)
        assert result == "Hello, World!"
        
        # Multiple parameters
        template = "Hello, {name}! You are {age} years old."
        params = {"name": "World", "age": 42}
        result = process_prompt_template(template, params)
        assert result == "Hello, World! You are 42 years old."
        
        # Missing parameter (should leave placeholder)
        template = "Hello, {name}! You are {age} years old."
        params = {"name": "World"}
        result = process_prompt_template(template, params)
        assert result == "Hello, World! You are {age} years old."
    
    def test_entity_analysis_prompt_handler(self):
        """Test the entity_analysis_prompt_handler function."""
        # Call the handler directly
        result = entity_analysis_prompt_handler({
            "entity_id": "entity1"
        }, self.transport_id)
        
        # Verify result
        assert "prompt" in result
        assert "context" in result
        assert "entity" in result["context"]
        assert "entity_summary" in result["context"]
        assert "relationships" in result["context"]
        
        # Verify prompt content
        assert "Entity 1" in result["prompt"]
        assert "concept" in result["prompt"]
        
        # Verify mock was called correctly
        self.mock_query_engine.query_entity.assert_called_with("entity1")
    
    def test_concept_comparison_prompt_handler(self):
        """Test the concept_comparison_prompt_handler function."""
        # Call the handler directly
        result = concept_comparison_prompt_handler({
            "concept1_id": "entity1",
            "concept2_id": "entity2"
        }, self.transport_id)
        
        # Verify result
        assert "prompt" in result
        assert "context" in result
        assert "concept1" in result["context"]
        assert "concept2" in result["context"]
        assert "connections" in result["context"]
        
        # Verify prompt content
        assert "Entity 1" in result["prompt"]
        assert "Entity 2" in result["prompt"]
        
        # Verify mocks were called correctly
        self.mock_query_engine.query_entity.assert_any_call("entity1")
        self.mock_query_engine.query_entity.assert_any_call("entity2")
        self.mock_query_engine.find_paths.assert_called_with("entity1", "entity2", 3)
    
    def test_ontology_exploration_prompt_handler(self):
        """Test the ontology_exploration_prompt_handler function."""
        # Call the handler directly
        result = ontology_exploration_prompt_handler({
            "topic": "test topic"
        }, self.transport_id)
        
        # Verify result
        assert "prompt" in result
        assert "context" in result
        assert "topic" in result["context"]
        assert "search_results" in result["context"]
        assert "ontology_summary" in result["context"]
        assert "related_sections" in result["context"]
        
        # Verify prompt content
        assert "test topic" in result["prompt"]
        
        # Verify mocks were called correctly
        self.mock_query_engine.search_entities.assert_called_with("test topic")
        self.mock_query_engine.generate_ontology_summary.assert_called_once()
        self.mock_query_engine.find_section_by_topic.assert_called_with("test topic")
    
    def test_hierarchy_analysis_prompt_handler(self):
        """Test the hierarchy_analysis_prompt_handler function."""
        # Call the handler directly
        result = hierarchy_analysis_prompt_handler({}, self.transport_id)
        
        # Verify result
        assert "prompt" in result
        assert "context" in result
        assert "root_nodes" in result["context"]
        assert "total_roots" in result["context"]
        assert "max_depth" in result["context"]
        
        # Call with specific root
        result = hierarchy_analysis_prompt_handler({
            "root_concept_id": "root1"
        }, self.transport_id)
        
        # Verify specific result
        assert "root_concept" in result["context"]
        assert "hierarchy" in result["context"]
        assert "max_depth" in result["context"]
        
        # Verify prompt content
        assert "Root 1" in result["prompt"]
        
        # Verify mock was called correctly
        self.mock_query_engine.analyze_concept_hierarchy.assert_called()
    
    def test_central_concepts_prompt_handler(self):
        """Test the central_concepts_prompt_handler function."""
        # Call the handler directly
        result = central_concepts_prompt_handler({
            "limit": 5
        }, self.transport_id)
        
        # Verify result
        assert "prompt" in result
        assert "context" in result
        assert "central_entities" in result["context"]
        assert "entities_by_type" in result["context"]
        assert "total" in result["context"]
        
        # Call with entity type
        result = central_concepts_prompt_handler({
            "limit": 5,
            "entity_type": "concept"
        }, self.transport_id)
        
        # Verify entity type is included in prompt
        assert "concept" in result["prompt"]
        
        # Verify mock was called correctly
        self.mock_query_engine.get_central_entities.assert_called_with(5, "concept")