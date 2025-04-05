import networkx as nx
import json
import datetime
from datetime import timezone # Use timezone instead of UTC for clarity
import uuid
import re
from typing import List, Dict, Any, Optional, Tuple, Union # Added Union

class CyberneticsQueryEngine:
    """
    A refactored query engine for exploring and analyzing the cybernetics ontology,
    incorporating improvements for efficiency, redundancy, and relationship handling.
    """
    def __init__(self, data_source: Union[str, Dict]):
        """
        Initialize the query engine with a data source.

        Args:
            data_source: Path to the JSON file with ontology data,
                         or a dictionary containing the data.
        """
        self.data_source = data_source
        self.graph: Optional[nx.DiGraph] = None # Initialize as None
        self.structured_ontology: Dict = {}
        self.relationship_index: Dict[str, Tuple[str, str]] = {} # relationship_id -> (source, target)
        self.load_data(data_source)

    # --- Helper Methods ---

    def _ensure_graph_loaded(self) -> None:
        """Raises RuntimeError if the graph hasn't been loaded."""
        if self.graph is None:
            # This should ideally not happen if load_data succeeds in __init__
            raise RuntimeError("Graph data has not been loaded successfully.")

    def _node_exists(self, node_id: str) -> bool:
        """Checks if a node exists in the graph."""
        self._ensure_graph_loaded()
        return node_id in self.graph

    def _get_node_attributes(self, node_id: str) -> Dict[str, Any]:
        """Gets all attributes for a given node."""
        self._ensure_graph_loaded()
        # Ensure node exists before accessing attributes
        if not self._node_exists(node_id):
            # This case should ideally be handled by calling functions
            # but provides an extra layer of safety.
             raise ValueError(f"Node '{node_id}' not found when retrieving attributes.")
        return self.graph.nodes[node_id]

    def _get_node_info(self, node_id: str) -> Dict[str, Any]:
        """Returns basic info (id, label, type) for a node."""
        if not self._node_exists(node_id):
            return {"id": node_id, "label": node_id, "type": "unknown", "error": "Node not found"}
        attrs = self._get_node_attributes(node_id)
        return {
            "id": node_id,
            "label": attrs.get("label", node_id),
            "type": attrs.get("type", "unknown")
        }

    def _format_node_output(self, node_id: str) -> Dict[str, Any]:
        """Formats the full output for a single entity query."""
        if not self._node_exists(node_id):
            return {"error": f"Entity '{node_id}' not found"}

        attributes = self._get_node_attributes(node_id)
        incoming = []
        # Ensure graph is not None before accessing edges
        self._ensure_graph_loaded()
        for source, _, data in self.graph.in_edges(node_id, data=True):
            source_info = self._get_node_info(source)
            incoming.append({
                "id": source,
                "label": source_info["label"],
                "relationship": data.get("label", "connected to")
            })

        outgoing = []
        for _, target, data in self.graph.out_edges(node_id, data=True):
            target_info = self._get_node_info(target)
            outgoing.append({
                "id": target,
                "label": target_info["label"],
                "relationship": data.get("label", "connected to")
            })

        return {
            "id": node_id,
            "attributes": attributes,
            "incoming": incoming,
            "outgoing": outgoing
        }

    def _set_entity_attributes(self, node_id: str, data: Dict[str, Any], is_new: bool = False) -> Dict[str, Any]:
        """
        Helper to set or update entity attributes and timestamps.

        Args:
            node_id: The ID of the node to update/create.
            data: Dictionary containing new attribute data.
            is_new: Flag indicating if this is a new entity creation.

        Returns:
            The dictionary of attributes set on the node.
        """
        self._ensure_graph_loaded()
        current_time_iso = datetime.datetime.now(timezone.utc).isoformat() + "Z"

        if is_new:
            # Initialize attributes for a new node
            node_attrs = {
                "label": data.get('label', node_id),
                "type": data.get('type', 'unknown'),
                "created_at": current_time_iso
            }
        else:
            # Get existing attributes for update
            if not self._node_exists(node_id):
                 raise ValueError(f"Cannot update non-existent entity '{node_id}'")
            node_attrs = dict(self.graph.nodes[node_id]) # Get a mutable copy

        # Update common attributes if present in data
        if 'label' in data:
            node_attrs['label'] = data['label']
        if 'type' in data:
            node_attrs['type'] = data['type']
        if 'description' in data:
            node_attrs['description'] = data['description']
        elif 'description' not in node_attrs and not is_new: # Handle removing description
             node_attrs.pop('description', None)
        if 'external_url' in data:
            node_attrs['external_url'] = data['external_url']
        elif 'external_url' not in node_attrs and not is_new: # Handle removing url
             node_attrs.pop('external_url', None)

        # Merge custom attributes from 'attributes' sub-dictionary
        reserved_keys = {'id', 'label', 'type', 'description', 'external_url', 'created_at', 'updated_at'}
        if 'attributes' in data and isinstance(data['attributes'], dict):
            for key, value in data['attributes'].items():
                if key not in reserved_keys:
                    node_attrs[key] = value

        # Set updated timestamp for updates
        if not is_new:
            node_attrs['updated_at'] = current_time_iso
        # Ensure created_at is not overwritten on update
        elif 'created_at' not in node_attrs:
             node_attrs['created_at'] = current_time_iso


        # Apply attributes to the graph node
        if is_new:
             self.graph.add_node(node_id, **node_attrs)
        else:
            # Update existing node data
            self.graph.nodes[node_id].update(node_attrs)
            # Remove keys that might have been nulled out in the update
            # Note: This requires iterating over a potentially changed dict, safer to update directly
            # A simpler approach is to ensure the update call handles all keys correctly
            # nx updates node attributes in place, so the graph.nodes access is correct.


        # Return the final set attributes from the graph itself for confirmation
        return dict(self.graph.nodes[node_id])


    def _build_relationship_index(self) -> None:
        """Builds the index mapping relationship IDs to (source, target) tuples."""
        self._ensure_graph_loaded()
        self.relationship_index = {}
        for u, v, data in self.graph.edges(data=True):
            rel_id = data.get('id')
            if rel_id:
                if rel_id in self.relationship_index:
                     # Handle potential duplicate relationship IDs if necessary
                     # For now, we'll overwrite, assuming IDs should be unique
                     print(f"Warning: Duplicate relationship ID '{rel_id}' found between ({u}, {v}) and {self.relationship_index[rel_id]}. Overwriting index.")
                self.relationship_index[rel_id] = (u, v)


    # --- Core Methods ---

    def load_data(self, data_source: Union[str, Dict]) -> None:
        """Load ontology data from JSON file or dictionary."""
        try:
            if isinstance(data_source, str):
                with open(data_source, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            elif isinstance(data_source, dict):
                 self.data = data_source
            else:
                raise TypeError("data_source must be a file path (str) or a dictionary")

            graph_data = self.data.get("knowledge_graph", {})
            
            # Create a new directed graph
            self.graph = nx.DiGraph()
            
            # Add nodes with their attributes
            for node in graph_data.get("nodes", []):
                # Create a copy of the node data to avoid modifying the original
                node_data = dict(node)
                node_id = node_data.pop("id")
                self.graph.add_node(node_id, **node_data)
                
            # Add edges with their attributes
            for edge in graph_data.get("edges", []):
                # Create a copy of the edge data to avoid modifying the original
                edge_data = dict(edge)
                source = edge_data.pop("source")
                target = edge_data.pop("target")
                self.graph.add_edge(source, target, **edge_data)

            self.structured_ontology = self.data.get("structured_ontology", {})

            # Build the relationship index after loading the graph
            self._build_relationship_index()

        except FileNotFoundError:
             print(f"Error: Data source file not found at '{data_source}'")
             # Initialize empty graph on file error
             self.graph = nx.DiGraph()
             self.data = {
                "knowledge_graph": {
                    "directed": True,
                    "multigraph": False,
                    "graph": {},
                    "nodes": [],
                    "edges": []
                }, 
                "structured_ontology": {}
             }
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{data_source}'")
            self.graph = nx.DiGraph()
            self.data = {
                "knowledge_graph": {
                    "directed": True,
                    "multigraph": False,
                    "graph": {},
                    "nodes": [],
                    "edges": []
                }, 
                "structured_ontology": {}
             }
        except Exception as e:
            print(f"An unexpected error occurred during data loading: {e}")
            self.graph = nx.DiGraph()
            self.data = {
                "knowledge_graph": {
                    "directed": True,
                    "multigraph": False,
                    "graph": {},
                    "nodes": [],
                    "edges": []
                }, 
                "structured_ontology": {}
             }


    def query_entity(self, entity_id: str) -> Dict:
        """
        Get detailed information about an entity.
        Uses helper methods for checking existence and formatting.
        """
        return self._format_node_output(entity_id) # Handles non-existence internally

    def find_paths(self, source_id: str, target_id: str, max_length: int = 3) -> List[List[Dict]]:
        """
        Find paths between two entities.
        Uses helper method _get_node_info.
        """
        if not self._node_exists(source_id) or not self._node_exists(target_id):
            # Return empty list if source or target doesn't exist
            # Consider logging a warning or returning an error indicator
            return []

        self._ensure_graph_loaded() # Ensure graph is available
        try:
            # Find all simple paths up to max_length
            paths_gen = nx.all_simple_paths(
                self.graph, source_id, target_id, cutoff=max_length
            )

            # Convert paths to a more detailed format using _get_node_info
            detailed_paths = []
            for path in paths_gen:
                detailed_path = []
                for i, node_id in enumerate(path):
                    node_info = self._get_node_info(node_id) # Use helper

                    # Add relationship to next node if not the last node
                    if i < len(path) - 1:
                        next_node_id = path[i + 1]
                        # Check if edge exists (should always be true for paths)
                        if self.graph.has_edge(node_id, next_node_id):
                            edge_data = self.graph.get_edge_data(node_id, next_node_id)
                            relationship = edge_data.get("label", "connected to")
                            node_info["relationship_to_next"] = relationship
                        else:
                            # This case indicates an issue with the path finding or graph state
                            node_info["relationship_to_next"] = "error: edge not found"


                    detailed_path.append(node_info)

                detailed_paths.append(detailed_path)

            return detailed_paths

        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound: # Should be caught by initial _node_exists check, but good safety
             return []


    def find_connections(self, entity_id: str, max_distance: int = 2) -> Dict:
        """
        Find all entities connected to the given entity within a certain distance.
        Uses nx.single_source_shortest_path_length for efficiency.
        """
        if not self._node_exists(entity_id):
            return {"error": f"Entity '{entity_id}' not found"}

        self._ensure_graph_loaded()
        connections = {dist: [] for dist in range(1, max_distance + 1)}

        try:
            # Calculate shortest path lengths from entity_id up to max_distance
            # This returns a dict {node: distance}
            reachable_nodes = nx.single_source_shortest_path_length(
                self.graph, entity_id, cutoff=max_distance
            )

            # Process the results
            for node_id, distance in reachable_nodes.items():
                if node_id == entity_id:
                    continue # Skip the source node itself

                if 1 <= distance <= max_distance:
                    node_info = self._get_node_info(node_id) # Use helper
                    # Remove error field if present from _get_node_info
                    node_info.pop("error", None)
                    connections[distance].append(node_info)

        except nx.NodeNotFound:
             # This should be caught by the initial check, but handle defensively
             return {"error": f"Entity '{entity_id}' not found during path calculation"}

        return connections

    def search_entities(self, query: str, entity_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for entities matching the query string.
        Uses helper method _get_node_info.
        """
        self._ensure_graph_loaded()
        results = []
        query_lower = query.lower()

        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get("type", "unknown")

            # Filter by type first if specified
            if entity_types and node_type not in entity_types:
                continue

            label = attrs.get("label", node_id).lower()
            description = attrs.get("description", "").lower()

            # Check label and description for matches
            match_score = 0.0
            match_found = False

            if query_lower in label:
                match_found = True
                # Higher score for exact or near-exact label match
                match_score = 1.0 if label == query_lower else 0.7 + (len(query_lower) / len(label) * 0.2)
            elif query_lower in description:
                match_found = True
                match_score = 0.3 # Lower score for description matches

            if match_found:
                # Use _get_node_info and add score
                node_info = self._get_node_info(node_id)
                node_info["match_score"] = match_score
                results.append(node_info)

        # Sort by match score (descending)
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results

    def get_central_entities(self, top_n: int = 10) -> List[Dict]:
        """
        Get the most central entities based on degree centrality.
        Uses helper method _get_node_info.
        """
        self._ensure_graph_loaded()
        if self.graph.number_of_nodes() == 0:
             return []

        try:
             # Calculate degree centrality (considers both in and out degrees for DiGraph)
             centrality = nx.degree_centrality(self.graph)

             # Sort nodes by centrality
             # Use list comprehension for potentially better performance than items() then sort
             central_nodes_ids = sorted(centrality, key=centrality.get, reverse=True)[:top_n]

             # Format results using _get_node_info
             results = []
             for node_id in central_nodes_ids:
                node_info = self._get_node_info(node_id)
                node_info["centrality"] = centrality[node_id]
                node_info["connections"] = self.graph.degree(node_id) # Total degree
                results.append(node_info)

             return results
        except Exception as e:
             print(f"Error calculating centrality: {e}")
             return [] # Return empty list on error


    def find_communities(self) -> Dict[int, List[str]]:
        """
        Detect communities using Louvain algorithm (if available) or connected components.
        """
        self._ensure_graph_loaded()
        if self.graph.number_of_nodes() == 0:
            return {}

        try:
            # Ensure the import path matches where the module would be mocked or installed
            import community_louvain

            # Convert directed graph to undirected for community detection
            # Important: Louvain typically works best on undirected graphs.
            # Consider if analyzing communities on the directed structure makes sense.
            # If so, other algorithms might be more appropriate.
            if self.graph.is_directed():
                undirected_graph = self.graph.to_undirected(as_view=True) # Use view for efficiency
            else:
                 undirected_graph = self.graph


            # Detect communities using Louvain
            # Handle empty graph case for partition
            if undirected_graph.number_of_nodes() > 0:
                 partition = community_louvain.best_partition(undirected_graph)
            else:
                 partition = {}


            # Group nodes by community
            communities: Dict[int, List[str]] = {}
            for node, community_id in partition.items():
                communities.setdefault(community_id, []).append(node)

            return communities

        except ImportError:
            print("community_louvain module not found. Falling back to connected components.")
            # Fallback to connected components if community module not available
            # Requires an undirected view of the graph
            if self.graph.is_directed():
                 undirected_graph_view = self.graph.to_undirected(as_view=True)
            else:
                 undirected_graph_view = self.graph

            components_gen = nx.connected_components(undirected_graph_view)
            communities = {i: list(component) for i, component in enumerate(components_gen)}
            return communities
        except Exception as e:
            # Catch potential errors from community_louvain itself
            print(f"Error during community detection: {e}")
            return {}


    def get_entity_types(self) -> Dict[str, int]:
        """Get a count of entities by type."""
        self._ensure_graph_loaded()
        type_counts: Dict[str, int] = {}
        for _, attrs in self.graph.nodes(data=True):
            entity_type = attrs.get("type", "unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts

    # Methods related to structured_ontology remain largely unchanged as they don't interact with the graph directly
    # ... (get_subsection_content, find_section_by_topic) ...
    def get_subsection_content(self, section_num: int, subsection_name: str) -> List[str]:
        """Get the content of a specific subsection."""
        section_key = str(section_num) # JSON keys are strings
        section = self.structured_ontology.get(section_key, {})
        subsections = section.get("subsections", {})

        # Try case-insensitive match first for robustness
        subsection_name_lower = subsection_name.lower()
        for name, content in subsections.items():
            if name.lower() == subsection_name_lower:
                return content

        # Fallback for exact match (if case matters) - less likely useful if already checked lower
        # if subsection_name in subsections:
        #    return subsections[subsection_name]

        return [] # Not found

    def find_section_by_topic(self, topic: str) -> List[Dict]:
        """Find sections that mention a specific topic."""
        results = []
        topic_lower = topic.lower()

        for section_num, section_data in self.structured_ontology.items():
            section_title = section_data.get("title", "").lower()
            title_match = topic_lower in section_title
            subsection_matches = []

            for subsection_name, items in section_data.get("subsections", {}).items():
                subsection_title_lower = subsection_name.lower()
                # Check subsection name
                if topic_lower in subsection_title_lower:
                    subsection_matches.append({
                        "name": subsection_name,
                        "type": "subsection_title"
                    })

                # Check items within subsection
                for item in items:
                     if isinstance(item, str) and topic_lower in item.lower(): # Ensure item is string
                         subsection_matches.append({
                            "name": subsection_name,
                            "item": item,
                            "type": "item"
                        })

            if title_match or subsection_matches:
                results.append({
                    "section_num": section_num,
                    "title": section_data.get("title", ""),
                    "title_match": title_match,
                    "subsection_matches": subsection_matches
                })
        return results


    def analyze_concept_hierarchy(self) -> Dict:
        """
        Analyze the hierarchy of concepts.
        Uses helper method _get_node_info.
        """
        self._ensure_graph_loaded()
        if self.graph.number_of_nodes() == 0:
            return {"root_nodes": [], "hierarchies": {}}

        root_nodes_ids = [
            node for node in self.graph.nodes()
            if self.graph.in_degree(node) == 0 and self.graph.out_degree(node) > 0
        ]

        max_depths = {}
        hierarchies = {}

        for root_id in root_nodes_ids:
            # Use BFS to find depths from each root
            # visited stores {node: depth}
            visited = {root_id: 0}
            queue = [(root_id, 0)] # (node, depth)
            current_max_depth = 0

            while queue:
                node_id, depth = queue.pop(0)
                current_max_depth = max(current_max_depth, depth)

                # Iterate over successors (targets of outgoing edges)
                for _, target_id in self.graph.out_edges(node_id):
                    if target_id not in visited:
                        new_depth = depth + 1
                        visited[target_id] = new_depth
                        queue.append((target_id, new_depth))

            max_depths[root_id] = current_max_depth

            # Build hierarchy structure grouped by depth
            hierarchy: Dict[str, List[Dict]] = {}
            for node_id, depth in visited.items():
                depth_str = str(depth) # JSON keys must be strings
                node_info = self._get_node_info(node_id)
                hierarchy.setdefault(depth_str, []).append(node_info)

            hierarchies[root_id] = hierarchy

        # Format root node information
        formatted_root_nodes = []
        for root_id in root_nodes_ids:
            root_info = self._get_node_info(root_id)
            root_info["max_depth"] = max_depths.get(root_id, 0)
            formatted_root_nodes.append(root_info)


        return {
            "root_nodes": formatted_root_nodes,
            "hierarchies": hierarchies
        }

    def _trace_evolution_chain(self, start_node_id: str, visited_in_chain: set) -> List[Dict]:
        """Helper method to trace an evolution chain, avoiding cycles within a single trace."""
        chain = []
        current_id = start_node_id

        while current_id is not None and current_id not in visited_in_chain:
            if not self._node_exists(current_id):
                # Handle case where chain points to a non-existent node
                print(f"Warning: Evolution chain broken at non-existent node '{current_id}'")
                break

            chain.append(self._get_node_info(current_id))
            visited_in_chain.add(current_id) # Mark as visited for this specific chain traversal

            found_next = None
            self._ensure_graph_loaded()
            for _, target_id, data in self.graph.out_edges(current_id, data=True):
                relationship = data.get("label", "").lower()
                # More flexible check for evolution relationships
                if "evolved" in relationship or relationship == "derived_from": # Added common alternative
                    # Ensure we don't step into a node already in this chain's traversal path
                    if target_id not in visited_in_chain:
                        found_next = target_id
                        break # Assume only one primary evolution path from a node
                    else:
                         # Cycle detected within this chain, stop tracing here
                         print(f"Warning: Evolution cycle detected involving node '{target_id}'. Stopping chain trace.")
                         found_next = None # Treat as end of chain
                         break


            current_id = found_next # Move to the next node or stop if None/cycle

        return chain


    def get_concept_evolution(self) -> List[List[Dict]]:
        """
        Trace the evolution of concepts based on 'evolved_into' or similar relationships.
        Uses helper _get_node_info and _trace_evolution_chain. Avoids simple cycles.
        """
        self._ensure_graph_loaded()
        evolution_chains = []
        # Keep track of nodes already included as a *starting point* of a chain
        # to avoid redundant chains starting mid-way through another.
        started_nodes = set()

        # Iterate through all nodes to find potential starting points of chains
        for node_id in list(self.graph.nodes()): # Use list to avoid issues if graph modified
            if node_id in started_nodes:
                continue # Skip if already part of a traced chain

            # Check if this node *starts* an evolution chain
            # A starting node might have incoming evolution edges but we trace forward from it.
            # Or it might have no incoming evolution edges.
            is_potential_start = False
            has_outgoing_evolution = False

            # Check for outgoing evolution edges
            for _, _, data in self.graph.out_edges(node_id, data=True):
                 relationship = data.get("label", "").lower()
                 if "evolved" in relationship or relationship == "derived_from":
                     has_outgoing_evolution = True
                     break

            # Simple heuristic: if it has outgoing evolution, consider it a potential start.
            # More complex: check if it has *incoming* evolution. If not, it's a definite start.
            has_incoming_evolution = False
            for _, _, data in self.graph.in_edges(node_id, data=True):
                 relationship = data.get("label", "").lower()
                 if "evolved" in relationship or relationship == "derived_from":
                      has_incoming_evolution = True
                      break

            # We trace from any node that *can* evolve, but prioritize true start points
            if has_outgoing_evolution: # Trace a chain if it goes somewhere
                # Use a set for visited nodes *within the current chain traversal* to detect cycles
                chain_visited_nodes = set()
                chain = self._trace_evolution_chain(node_id, chain_visited_nodes)
                if chain:
                    evolution_chains.append(chain)
                    # Mark all nodes in this successfully traced chain as 'started'
                    # to prevent starting new chains from them later.
                    for node_info in chain:
                        started_nodes.add(node_info["id"])

        # Filter out sub-chains if needed (e.g., if B->C is found after A->B->C) - current logic avoids this
        return evolution_chains


    def get_related_concepts(self, concept_id: str, relationship_types: Optional[List[str]] = None) -> Dict:
        """
        Get concepts related to the given concept, optionally filtered by relationship types.
        Uses helper method _get_node_info.
        """
        if not self._node_exists(concept_id):
            return {"error": f"Concept '{concept_id}' not found"}

        related: Dict[str, List[Dict]] = {}
        relationship_types_lower = set(t.lower() for t in relationship_types) if relationship_types else None

        self._ensure_graph_loaded()
        # Outgoing relationships
        for _, target_id, data in self.graph.out_edges(concept_id, data=True):
            relationship = data.get("label", "related")
            if relationship_types_lower and relationship.lower() not in relationship_types_lower:
                continue

            target_info = self._get_node_info(target_id)
            target_info["direction"] = "outgoing"
            related.setdefault(relationship, []).append(target_info)

        # Incoming relationships
        for source_id, _, data in self.graph.in_edges(concept_id, data=True):
            relationship = data.get("label", "related")
            if relationship_types_lower and relationship.lower() not in relationship_types_lower:
                continue

            source_info = self._get_node_info(source_id)
            source_info["direction"] = "incoming"
            
            # Create an inverse relationship name
            inverse_relationship = f"inverse_{relationship}"
            related.setdefault(inverse_relationship, []).append(source_info)


        return related

    def get_relationship_types(self) -> Dict[str, int]:
        """Get a count of edges by relationship type."""
        self._ensure_graph_loaded()
        relationship_counts: Dict[str, int] = {}
        for _, _, data in self.graph.edges(data=True):
            relationship = data.get("label", "unknown") # Use 'unknown' for edges without label
            relationship_counts[relationship] = relationship_counts.get(relationship, 0) + 1
        return relationship_counts

    def generate_ontology_summary(self) -> Dict:
        """Generate a summary of the ontology."""
        self._ensure_graph_loaded()
        num_subsections = 0
        for section_data in self.structured_ontology.values():
            num_subsections += len(section_data.get("subsections", {}))

        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "entity_types": self.get_entity_types(),
            "relationship_types": self.get_relationship_types(),
            # Get top 5 central entities, ensure result is list
            "central_entities": self.get_central_entities(5) or [],
            "sections": len(self.structured_ontology),
            "subsections": num_subsections
        }

    # --- CRUD Operations ---

    def create_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity in the graph. Uses _set_entity_attributes helper.

        Args:
            entity_data: Dictionary with entity data (label, type, description?, attributes?).
                         'id' is optional; will be generated if missing.

        Returns:
            Dictionary with created entity data, including generated ID and attributes.

        Raises:
            ValueError: If entity creation fails (e.g., ID conflict, invalid data).
        """
        self._ensure_graph_loaded()
        entity_id = entity_data.get('id')

        # --- ID Generation Logic ---
        if not entity_id:
            if 'label' in entity_data:
                # Generate a base ID from the label
                base_id = re.sub(r'\s+', '_', entity_data['label'].lower()) # Replace spaces with underscore
                base_id = re.sub(r'[^a-z0-9_]', '', base_id).strip('_') # Keep only alphanum and underscore

                if not base_id: # Handle empty label or label with only special chars
                     entity_id = str(uuid.uuid4())
                else:
                     entity_id = base_id
                     # Ensure uniqueness if base_id from label already exists
                     if self._node_exists(entity_id):
                         entity_id = f"{base_id}_{uuid.uuid4().hex[:8]}" # Append short UUID hex

            else:
                # Generate a fully random UUID if no label provided
                entity_id = str(uuid.uuid4())
        elif self._node_exists(entity_id):
             # If ID was provided but already exists
             raise ValueError(f"Entity with explicitly provided ID '{entity_id}' already exists.")
        # --- End ID Generation ---

        # Use helper to set attributes and add node
        try:
            final_attributes = self._set_entity_attributes(entity_id, entity_data, is_new=True)
        except Exception as e:
             # Catch potential errors during attribute setting or node addition
             raise ValueError(f"Failed to create entity '{entity_id}': {e}") from e


        # Format the response based on the node added to the graph
        # No incoming/outgoing yet for a new node
        return {
            "id": entity_id,
            "attributes": final_attributes,
            "incoming": [],
            "outgoing": []
        }


    def update_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing entity. Uses _set_entity_attributes helper.

        Args:
            entity_id: ID of the entity to update.
            entity_data: Dictionary with fields to update.

        Returns:
            Dictionary with updated entity data, or None if entity not found.

        Raises:
            ValueError: If update data is invalid or update fails.
        """
        if not self._node_exists(entity_id):
            return None # Entity not found

        # Use helper to update attributes
        try:
            final_attributes = self._set_entity_attributes(entity_id, entity_data, is_new=False)
        except Exception as e:
            # Catch potential errors during attribute setting
            raise ValueError(f"Failed to update entity '{entity_id}': {e}") from e


        # Format the response
        # Note: query_entity format includes connections, update response typically just includes attributes
        return {
            "id": entity_id,
            "attributes": final_attributes
        }

    def delete_entity(self, entity_id: str, cascade: bool = False) -> Dict[str, Any]:
        """
        Delete an entity and optionally its relationships.
        Updates relationship_index if cascade is True.
        """
        if not self._node_exists(entity_id):
            return {"success": False, "message": f"Entity '{entity_id}' not found.", "not_found": True}

        self._ensure_graph_loaded()
        # Check for relationships *before* deciding based on cascade flag
        in_degree = self.graph.in_degree(entity_id)
        out_degree = self.graph.out_degree(entity_id)
        has_relationships = (in_degree > 0) or (out_degree > 0)

        if has_relationships and not cascade:
            return {
                "success": False,
                "message": f"Entity '{entity_id}' has {in_degree} incoming and {out_degree} outgoing relationships. Use cascade=true to delete them along with the entity."
            }

        relationships_removed_count = 0
        if cascade:
            # Store IDs of relationships to remove from the index *after* edge removal
            rels_to_unindex = []

            # Remove incoming edges and collect their IDs
            for source, target, data in list(self.graph.in_edges(entity_id, data=True)): # Use list for safe iteration
                rel_id = data.get('id')
                if rel_id:
                    rels_to_unindex.append(rel_id)
                self.graph.remove_edge(source, target)
                relationships_removed_count += 1

            # Remove outgoing edges and collect their IDs
            for source, target, data in list(self.graph.out_edges(entity_id, data=True)): # Use list for safe iteration
                rel_id = data.get('id')
                if rel_id:
                     # Avoid double-counting if self-loop and already added
                     if rel_id not in rels_to_unindex:
                          rels_to_unindex.append(rel_id)
                self.graph.remove_edge(source, target)
                relationships_removed_count += 1 # Count outgoing separately

             # Update the relationship index
            for rel_id in rels_to_unindex:
                self.relationship_index.pop(rel_id, None) # Remove safely

        # Delete the entity node itself
        self.graph.remove_node(entity_id)

        return {
            "success": True,
            "message": f"Entity '{entity_id}' deleted successfully.",
            "relationships_removed": relationships_removed_count if cascade else 0
        }

    def create_relationship(self, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new relationship between entities. Updates relationship_index.

        Args:
            relationship_data: Dict with 'source_id', 'target_id', 'relationship_type' (maps to 'label'),
                               and optional 'attributes' dict. 'id' can be provided, otherwise generated.

        Returns:
            Dictionary with created relationship data.

        Raises:
            ValueError: If creation fails (missing nodes, existing relationship of same type?).
                        Consider policy on multiple edges between same nodes.
        """
        source_id = relationship_data.get('source_id')
        target_id = relationship_data.get('target_id')
        rel_type = relationship_data.get('relationship_type') # This will be the 'label'

        if not source_id or not target_id or not rel_type:
             raise ValueError("Missing required fields: 'source_id', 'target_id', 'relationship_type'")

        if not self._node_exists(source_id):
            raise ValueError(f"Source entity '{source_id}' not found")
        if not self._node_exists(target_id):
            raise ValueError(f"Target entity '{target_id}' not found")

        # NetworkX DiGraph allows multiple edges if using MultiDiGraph, but default DiGraph does not.
        # If using DiGraph, adding an edge overwrites existing attributes if edge exists.
        # Check if edge exists - policy needed: error, update, or allow (if MultiDiGraph)?
        # Assuming DiGraph: Check if edge exists. If so, maybe update is intended? Or error?
        # Let's error if an edge *with the same label* already exists.
        if self.graph.has_edge(source_id, target_id):
             # Get existing edge data to check label if needed (DiGraph stores one edge)
             # If using MultiDiGraph, you'd iterate over edges between source/target.
             existing_data = self.graph.get_edge_data(source_id, target_id)
             if existing_data.get('label') == rel_type:
                  # Keep the error message simple to match the test
                  raise ValueError(f"Relationship of type '{rel_type}' already exists")
             # If edge exists but different type, adding might overwrite - be cautious.
             # For DiGraph, let's proceed to add/overwrite but log a warning.
             print(f"Warning: Edge exists between '{source_id}' and '{target_id}' but with different type. Adding new relationship '{rel_type}' will overwrite existing edge attributes.")


        # Generate relationship ID if not provided
        relationship_id = relationship_data.get('id', str(uuid.uuid4()))

        # Check if generated/provided ID is already in use in the index
        if relationship_id in self.relationship_index:
             # Handle ID collision - either error or regenerate
             raise ValueError(f"Relationship ID '{relationship_id}' already exists. Provide a unique ID or allow regeneration.")


        # Create edge attributes
        current_time_iso = datetime.datetime.now(timezone.utc).isoformat() + "Z"
        edge_attrs = {
            "id": relationship_id,
            "label": rel_type, # Map relationship_type to label attribute
            "created_at": current_time_iso
        }

        # Add custom attributes
        custom_attributes = relationship_data.get('attributes', {})
        if isinstance(custom_attributes, dict):
            reserved_keys = {'id', 'label', 'created_at', 'updated_at'}
            for key, value in custom_attributes.items():
                if key not in reserved_keys:
                    edge_attrs[key] = value

        # Add the edge to the graph
        self._ensure_graph_loaded()
        self.graph.add_edge(source_id, target_id, **edge_attrs)

        # Update the relationship index
        self.relationship_index[relationship_id] = (source_id, target_id)

        # Format the response
        source_info = self._get_node_info(source_id)
        target_info = self._get_node_info(target_id)

        # Retrieve attributes directly from the added edge for confirmation
        final_edge_attrs = self.graph.get_edge_data(source_id, target_id)

        return {
            "id": relationship_id,
            "source_id": source_id,
            "source_label": source_info["label"],
            "target_id": target_id,
            "target_label": target_info["label"],
            "relationship_type": final_edge_attrs.get('label'), # Use label from graph
            # Exclude standard keys from custom attributes dict
            "attributes": {k: v for k, v in final_edge_attrs.items() if k not in ('id', 'label', 'created_at', 'updated_at')},
            "created_at": final_edge_attrs.get('created_at')
        }


    def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a relationship by ID using the index for efficiency.

        Args:
            relationship_id: ID of the relationship to get.

        Returns:
            Dictionary with relationship data, or None if not found.
        """
        if relationship_id not in self.relationship_index:
            return None # Not found in index

        source_id, target_id = self.relationship_index[relationship_id]

        # Verify the edge still exists in the graph (consistency check)
        self._ensure_graph_loaded()
        if not self.graph.has_edge(source_id, target_id):
             # Index inconsistency - relationship was likely deleted without index update
             print(f"Warning: Relationship ID '{relationship_id}' found in index but edge ({source_id}, {target_id}) missing in graph. Cleaning index.")
             self.relationship_index.pop(relationship_id, None)
             return None


        edge_data = self.graph.get_edge_data(source_id, target_id)

        # Verify the ID in the edge data matches (extra safety check)
        if edge_data.get('id') != relationship_id:
             print(f"Warning: Index points to edge ({source_id}, {target_id}) but its ID ('{edge_data.get('id')}') doesn't match requested ID '{relationship_id}'. Possible index corruption.")
             # Decide how to handle: return None, or return the data found at edge?
             # Returning None is safer if ID matching is strict.
             return None


        # Format the response
        source_info = self._get_node_info(source_id)
        target_info = self._get_node_info(target_id)

        return {
            "id": relationship_id,
            "source_id": source_id,
            "source_label": source_info.get("label", source_id),
            "source_type": source_info.get("type", "unknown"),
            "target_id": target_id,
            "target_label": target_info.get("label", target_id),
            "target_type": target_info.get("type", "unknown"),
            "relationship_type": edge_data.get('label', 'related_to'), # Use 'label'
            "attributes": {k: v for k, v in edge_data.items() if k not in ('id', 'label', 'created_at', 'updated_at')},
            "created_at": edge_data.get('created_at'),
            "updated_at": edge_data.get('updated_at')
        }


    def update_relationship(self, relationship_id: str, relationship_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing relationship using the index.

        Args:
            relationship_id: ID of the relationship to update.
            relationship_data: Dict with fields to update ('relationship_type', 'attributes').

        Returns:
            Dictionary with updated relationship data, or None if not found.
        """
        if relationship_id not in self.relationship_index:
            return None # Not found in index

        source_id, target_id = self.relationship_index[relationship_id]

        # Verify the edge still exists
        self._ensure_graph_loaded()
        if not self.graph.has_edge(source_id, target_id):
             print(f"Warning: Attempt to update relationship ID '{relationship_id}' but edge ({source_id}, {target_id}) missing. Cleaning index.")
             self.relationship_index.pop(relationship_id, None)
             return None

        # Get mutable reference to edge data
        edge_data = self.graph[source_id][target_id]

        # Verify ID match
        if edge_data.get('id') != relationship_id:
             print(f"Warning: Index points to edge ({source_id}, {target_id}) but its ID ('{edge_data.get('id')}') doesn't match update ID '{relationship_id}'. Update aborted.")
             return None


        # Update relationship type (label) if provided
        if 'relationship_type' in relationship_data:
            edge_data['label'] = relationship_data['relationship_type']

        # Update custom attributes if provided
        custom_attributes = relationship_data.get('attributes')
        if isinstance(custom_attributes, dict):
            reserved_keys = {'id', 'label', 'created_at', 'updated_at'}
            for key, value in custom_attributes.items():
                if key not in reserved_keys:
                    edge_data[key] = value
            # Consider removing attributes not present in the update dict? Policy needed.
            # For now, only adds/updates provided attributes.

        # Add/update the 'updated_at' timestamp
        edge_data['updated_at'] = datetime.datetime.now(timezone.utc).isoformat() + "Z"

        # Format the response using the updated data
        # No need to call _get_node_info again unless labels could change
        source_label = self._get_node_info(source_id).get('label', source_id)
        target_label = self._get_node_info(target_id).get('label', target_id)


        return {
            "id": relationship_id,
            "source_id": source_id,
            "source_label": source_label, # Include labels in response
            "target_id": target_id,
            "target_label": target_label, # Include labels in response
            "relationship_type": edge_data.get('label'),
            "attributes": {k: v for k, v in edge_data.items() if k not in ('id', 'label', 'created_at', 'updated_at')},
            "created_at": edge_data.get('created_at'), # Keep original created_at
            "updated_at": edge_data.get('updated_at')
        }


    def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship using the index. Updates relationship_index.

        Args:
            relationship_id: ID of the relationship to delete.

        Returns:
            Boolean indicating success (True if deleted, False if not found).
        """
        if relationship_id not in self.relationship_index:
            return False # Not found

        source_id, target_id = self.relationship_index[relationship_id]

        # Verify edge exists before attempting removal
        self._ensure_graph_loaded()
        if not self.graph.has_edge(source_id, target_id):
            print(f"Warning: Attempt to delete relationship ID '{relationship_id}' but edge ({source_id}, {target_id}) already missing. Cleaning index.")
            self.relationship_index.pop(relationship_id, None) # Clean index entry
            return False # Indicate relationship wasn't actively deleted now

        # Verify the ID on the edge matches before deleting (optional, but safer)
        edge_data = self.graph.get_edge_data(source_id, target_id)
        if edge_data.get('id') != relationship_id:
             print(f"Warning: Index points to edge ({source_id}, {target_id}) but its ID ('{edge_data.get('id')}') doesn't match delete ID '{relationship_id}'. Deletion aborted for safety.")
             # Don't remove from index here if IDs mismatch, indicates bigger issue
             return False


        # Remove the edge from the graph
        try:
             self.graph.remove_edge(source_id, target_id)
             # Remove from the index *after* successful graph removal
             self.relationship_index.pop(relationship_id, None)
             return True
        except Exception as e:
             # Should not happen if has_edge passed, but catch defensively
             print(f"Error removing edge ({source_id}, {target_id}) from graph: {e}")
             return False


    # --- Listing/Pagination Methods ---
    # Note: Sorting the full list before pagination remains potentially inefficient
    # for very large graphs with the current NetworkX-based implementation.
    # True optimization requires different data structures or external indexing.

    def list_entities(self, entity_type: Optional[str] = None, query: Optional[str] = None,
                      limit: int = 50, offset: int = 0, sort: str = 'created_at',
                      order: str = 'desc') -> Dict[str, Any]:
        """
        List entities with filtering, sorting, and pagination.
        Acknowledgement: Sorting performance depends on the size of the filtered list.
        """
        self._ensure_graph_loaded()
        filtered_entities = []
        query_lower = query.lower() if query else None

        # Iterate and filter
        for node_id, attrs in self.graph.nodes(data=True):
            # Type filter
            current_type = attrs.get('type', 'unknown')
            if entity_type and current_type != entity_type:
                continue

            # Query filter (label or description)
            if query_lower:
                label = attrs.get('label', '').lower()
                description = attrs.get('description', '').lower()
                if query_lower not in label and query_lower not in description:
                    continue

            # Add essential data for sorting and final output
            filtered_entities.append({
                "id": node_id,
                "label": attrs.get('label', node_id),
                "type": current_type,
                "description": attrs.get('description', ''),
                # Use ISO format string directly for sorting
                "created_at": attrs.get('created_at', ''),
                "updated_at": attrs.get('updated_at', '')
            })

        # Sort the filtered list
        reverse = order.lower() == 'desc'
        sort_key = sort if sort in ('label', 'type', 'created_at', 'updated_at', 'id') else 'created_at'

        try:
            # Handle potentially missing sort keys gracefully using .get with a default
             default_sort_value = '' # Default for string-based sorts
             if sort_key in ['created_at', 'updated_at']:
                 # Use a very early date string as default for time sorts if missing
                 default_sort_value = '0001-01-01T00:00:00Z'


             filtered_entities.sort(key=lambda e: e.get(sort_key, default_sort_value) or default_sort_value, reverse=reverse)
        except TypeError as e:
             print(f"Warning: TypeError during sorting entities by '{sort_key}'. Check data consistency. Error: {e}")
             # Potentially fallback to sorting by ID or skip sorting
             filtered_entities.sort(key=lambda e: e['id'], reverse=reverse)


        # Apply pagination
        total = len(filtered_entities)
        paginated_entities = filtered_entities[offset:offset + limit]

        return {
            "entities": paginated_entities,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def list_relationships(self, source_id: Optional[str] = None, target_id: Optional[str] = None,
                           entity_id: Optional[str] = None, relationship_type: Optional[str] = None,
                           limit: int = 50, offset: int = 0, sort: str = 'created_at',
                           order: str = 'desc') -> Dict[str, Any]:
        """
        List relationships with filtering, sorting, and pagination.
        Acknowledgement: Sorting performance depends on the size of the filtered list.
        """
        self._ensure_graph_loaded()
        filtered_relationships = []

        # Iterate through edges and filter
        for u, v, data in self.graph.edges(data=True):
            # Filter by source, target, or either node (entity_id)
            if source_id and u != source_id: continue
            if target_id and v != target_id: continue
            if entity_id and u != entity_id and v != entity_id: continue

            # Filter by relationship type (label)
            rel_type = data.get('label', 'unknown')
            if relationship_type and rel_type != relationship_type: continue

            # Fetch node labels efficiently using helper (only if needed for sorting/output)
            # Defer label fetching until after sorting if possible and not sorting by label
            source_label = None
            target_label = None
            # Fetch labels if sorting by them or for output prep
            if sort in ['source_label', 'target_label'] or True: # Always fetch for output
                 source_info = self._get_node_info(u)
                 target_info = self._get_node_info(v)
                 source_label = source_info.get('label', u)
                 target_label = target_info.get('label', v)


            filtered_relationships.append({
                "id": data.get('id', f"{u}_to_{v}"), # Use actual ID if available
                "source_id": u,
                "source_label": source_label, # Store for sorting/output
                "target_id": v,
                "target_label": target_label, # Store for sorting/output
                "relationship_type": rel_type,
                "created_at": data.get('created_at', ''),
                "updated_at": data.get('updated_at', '')
            })

        # Sort the filtered list
        reverse = order.lower() == 'desc'
        sort_key = sort if sort in ('relationship_type', 'source_label', 'target_label', 'created_at', 'updated_at', 'id') else 'created_at'

        try:
             # Handle potentially missing sort keys gracefully
             default_sort_value = ''
             if sort_key in ['created_at', 'updated_at']:
                 default_sort_value = '0001-01-01T00:00:00Z'
             elif sort_key in ['source_label', 'target_label']:
                  # Handle cases where labels might be None (if node info failed)
                  filtered_relationships.sort(key=lambda r: (r.get(sort_key) or default_sort_value).lower() if r.get(sort_key) else default_sort_value, reverse=reverse)
             else:
                  filtered_relationships.sort(key=lambda r: r.get(sort_key, default_sort_value) or default_sort_value, reverse=reverse)

        except TypeError as e:
             print(f"Warning: TypeError during sorting relationships by '{sort_key}'. Check data consistency. Error: {e}")
             filtered_relationships.sort(key=lambda r: r['id'], reverse=reverse) # Fallback sort

        # Apply pagination
        total = len(filtered_relationships)
        paginated_relationships = filtered_relationships[offset:offset + limit]

        # Ensure labels are present in the final paginated output if not fetched earlier
        # (They are fetched above in current logic)


        return {
            "relationships": paginated_relationships,
            "total": total,
            "limit": limit,
            "offset": offset
        }


    # --- Persistence ---

    def save_changes(self) -> bool:
        """
        Save changes to the knowledge graph back to the original data source file
        (if it was a file path) using node-link format.
        Overwrites the original file.

        Returns:
            Boolean indicating success.
        """
        if not isinstance(self.data_source, str):
            print("Warning: Cannot save changes. Initial data source was not a file path.")
            return False

        if self.graph is None:
             print("Error: Graph is not loaded. Cannot save.")
             return False


        try:
            # Generate node-link data from the current graph state
            # Create a node-link format that matches the expected structure in tests
            graph_data_dict = {
                "directed": self.graph.is_directed(),
                "multigraph": self.graph.is_multigraph(),
                "graph": {},
                "nodes": [],
                "edges": []
            }
            
            # Add nodes with their attributes
            for node_id, attrs in self.graph.nodes(data=True):
                node_data = {"id": node_id}
                node_data.update(attrs)
                graph_data_dict["nodes"].append(node_data)
            
            # Add edges with their attributes
            for source, target, attrs in self.graph.edges(data=True):
                edge_data = {"source": source, "target": target}
                edge_data.update(attrs)
                graph_data_dict["edges"].append(edge_data)

            # Update the 'knowledge_graph' part of the main data structure
            self.data['knowledge_graph'] = graph_data_dict
            # The structured_ontology part remains as it was unless modified elsewhere

            # Save the entire updated data structure back to the original file
            with open(self.data_source, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False) # Use indent for readability

            return True
        except Exception as e:
            print(f"Error saving changes to '{self.data_source}': {e}")
            return False