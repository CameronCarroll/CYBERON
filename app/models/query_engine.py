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
            "type": attrs.get("type", "unknown"),
            "description": attrs.get("description", "")
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

        # Create a response that matches the new graph-based structure
        # Direct access to attributes instead of nested under attributes object
        return {
            "id": node_id,
            "label": attributes.get("label", node_id),
            "type": attributes.get("type", "unknown"),
            "description": attributes.get("description", ""),
            "category": attributes.get("category", ""),
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
            
            # Start with existing attributes
            node_attrs = dict(self._get_node_attributes(node_id))
            # Update the last_modified timestamp
            node_attrs["last_modified"] = current_time_iso

        # Update with new data, preserving any fields not in the update
        for key, value in data.items():
            if key not in ('id', 'created_at'): # Don't overwrite these
                node_attrs[key] = value

        # Set the attributes on the node
        nx.set_node_attributes(self.graph, {node_id: node_attrs})
        return node_attrs

    def _build_relationship_index(self) -> None:
        """Build an index of relationships for faster lookup."""
        self._ensure_graph_loaded()
        self.relationship_index = {}
        
        for source, target, data in self.graph.edges(data=True):
            # Generate a unique ID for the relationship if not present
            rel_id = data.get("id", f"rel_{uuid.uuid4().hex[:8]}")
            self.relationship_index[rel_id] = (source, target)
            
            # Ensure the relationship has an ID in the graph
            if "id" not in data:
                self.graph[source][target]["id"] = rel_id

    # --- Data Loading and Management ---

    def load_data(self, data_source: Union[str, Dict]) -> None:
        """
        Load data from a file or dictionary.
        
        Args:
            data_source: Path to JSON file or dictionary with data.
        """
        try:
            # Handle both file paths and direct data dictionaries
            if isinstance(data_source, str):
                with open(data_source, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = data_source
                
            # Initialize a new directed graph
            self.graph = nx.DiGraph()
            
            # Extract graph data from the knowledge_graph section
            graph_data = self.data.get("knowledge_graph", {})
            
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
            # Handle case where description might be None
            description = attrs.get("description", "")
            description = description.lower() if description is not None else ""

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

        # If no match, return empty list
        return []

    def find_section_by_topic(self, topic: str) -> Dict[str, Dict]:
        """Find sections containing the given topic."""
        topic_lower = topic.lower()
        matching_sections = {}

        for section_num, section_data in self.structured_ontology.items():
            section_title = section_data.get("title", "").lower()
            
            # Check if topic is in section title
            if topic_lower in section_title:
                matching_sections[section_num] = section_data
                continue
                
            # Check subsections
            subsections = section_data.get("subsections", {})
            for subsection_name, items in subsections.items():
                if topic_lower in subsection_name.lower():
                    matching_sections[section_num] = section_data
                    break
                    
                # Check items in subsection
                for item in items:
                    if topic_lower in item.lower():
                        matching_sections[section_num] = section_data
                        break
                else:
                    continue
                break

        return matching_sections

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

        self._ensure_graph_loaded()
        
        # Get the concept's basic info
        concept_info = self._get_node_info(concept_id)
        
        # Get related concepts (outgoing relationships)
        related_out = []
        for _, target, data in self.graph.out_edges(concept_id, data=True):
            relationship = data.get("label", "connected to")
            
            # Filter by relationship type if specified
            if relationship_types and relationship not in relationship_types:
                continue
                
            target_info = self._get_node_info(target)
            related_out.append({
                "id": target,
                "label": target_info["label"],
                "type": target_info["type"],
                "relationship": relationship
            })
            
        # Get related concepts (incoming relationships)
        related_in = []
        for source, _, data in self.graph.in_edges(concept_id, data=True):
            relationship = data.get("label", "connected to")
            
            # Filter by relationship type if specified
            if relationship_types and relationship not in relationship_types:
                continue
                
            source_info = self._get_node_info(source)
            related_in.append({
                "id": source,
                "label": source_info["label"],
                "type": source_info["type"],
                "relationship": relationship
            })
            
        return {
            "concept": concept_info,
            "related_outgoing": related_out,
            "related_incoming": related_in
        }

    def analyze_concept_hierarchy(self) -> Dict:
        """
        Analyze the hierarchy of concepts based on 'contains' or similar relationships.
        Returns a structured representation of the hierarchy.
        """
        self._ensure_graph_loaded()
        
        # Find root nodes (no incoming 'contains' edges)
        root_nodes = []
        for node_id in self.graph.nodes():
            is_root = True
            for _, _, data in self.graph.in_edges(node_id, data=True):
                relationship = data.get("label", "").lower()
                if relationship in ("contains", "has_subcategory"):
                    is_root = False
                    break
            
            if is_root:
                node_info = self._get_node_info(node_id)
                if node_info.get("type") == "category":
                    root_nodes.append(node_id)
        
        # Format root nodes
        formatted_root_nodes = [self._get_node_info(node_id) for node_id in root_nodes]
        
        # Build hierarchies starting from root nodes
        hierarchies = {}
        for root_id in root_nodes:
            hierarchy = self._build_hierarchy(root_id)
            hierarchies[root_id] = hierarchy
        
        return {
            "root_nodes": formatted_root_nodes,
            "hierarchies": hierarchies
        }
        
    def _build_hierarchy(self, node_id: str, visited: Optional[set] = None) -> Dict:
        """Helper method to build a hierarchy tree from a node."""
        if visited is None:
            visited = set()
            
        if node_id in visited:
            return {"id": node_id, "label": "CYCLE DETECTED", "children": []}
            
        visited.add(node_id)
        
        node_info = self._get_node_info(node_id)
        children = []
        
        for _, target, data in self.graph.out_edges(node_id, data=True):
            relationship = data.get("label", "").lower()
            if relationship in ("contains", "has_subcategory"):
                child_hierarchy = self._build_hierarchy(target, visited.copy())
                children.append(child_hierarchy)
        
        result = {
            "id": node_id,
            "label": node_info["label"],
            "type": node_info["type"]
        }
        
        if children:
            result["children"] = children
            
        return result
