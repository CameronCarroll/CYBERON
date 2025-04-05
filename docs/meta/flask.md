# CYBERON Flask Application Structure

## Core Flask Components
- Application Factory: Creates and configures the Flask application
- Blueprints: Modular components for different application features
- Routes: URL handlers for web interface and API endpoints
- Templates: Jinja2 templates for rendering HTML pages
- Static Files: CSS, JavaScript, and other static assets

## Blueprint Organization
- Main Blueprint: Core routes and query engine initialization
- API Blueprint: RESTful API endpoints for data access
- Visualization Blueprint: Graph visualization routes
- Entities Blueprint: CRUD operations for ontology entities
- Relationships Blueprint: CRUD operations for entity relationships
- Graph Blueprint: Graph-specific API endpoints

## Route Handlers
- Index Route: Entry point to the application
- Upload Route: Handles ontology file uploads
- Search Route: Provides entity search functionality
- Entity Route: Displays entity details
- Graph Data Route: Provides graph data for visualization
- Path Finding Route: Finds paths between entities
- Central Concepts Route: Identifies central concepts in the ontology

## Middleware Components
- Rate Limiter: Controls request frequency
- Error Handlers: Manages application errors
- Request Preprocessing: Prepares requests for handling
- Response Formatting: Standardizes API responses

## Flask Extensions
- Flask-Limiter: Rate limiting functionality
- Jinja2: Template engine for HTML rendering
- Werkzeug: WSGI utilities for request handling
