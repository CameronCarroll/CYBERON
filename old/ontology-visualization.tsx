import React, { useState, useEffect, useRef } from 'react';
import { ForceGraph2D } from 'react-force-graph';
import _ from 'lodash';

const CyberneticsOntologyGraph = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [filterType, setFilterType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const fgRef = useRef();

  useEffect(() => {
    // Fetch or load graph data - for this example, we'll use sample data
    const sampleData = {
      nodes: [
        { id: 'cybernetics', label: 'Cybernetics', type: 'domain', desc: 'Study of control and communication in systems' },
        { id: 'wiener', label: 'Norbert Wiener', type: 'person', desc: 'Mathematician who coined the term cybernetics' },
        { id: 'feedback_loops', label: 'Feedback Loops', type: 'concept', desc: 'Circular processes where outputs affect inputs' },
        { id: 'homeostasis', label: 'Homeostasis', type: 'concept', desc: 'Self-regulation to maintain stable conditions' },
        { id: 'information_theory', label: 'Information Theory', type: 'domain', desc: 'Study of quantification and transmission of information' },
        { id: 'shannon', label: 'Claude Shannon', type: 'person', desc: 'Founder of information theory' },
        { id: 'entropy', label: 'Entropy', type: 'concept', desc: 'Measure of uncertainty or randomness' },
        { id: 'ai', label: 'Artificial Intelligence', type: 'domain', desc: 'Field creating intelligent machines' },
        { id: 'neural_networks', label: 'Neural Networks', type: 'concept', desc: 'Computing systems inspired by biological brains' },
        { id: 'transformers', label: 'Transformers', type: 'concept', desc: 'Neural architecture using self-attention mechanisms' },
        { id: 'llms', label: 'Large Language Models', type: 'concept', desc: 'AI systems trained on vast text corpora' },
        { id: 'cognitive', label: 'Cognitive Cybernetics', type: 'domain', desc: 'Study of cognition through cybernetic lens' },
        { id: 'predictive_processing', label: 'Predictive Processing', type: 'concept', desc: 'Brain as prediction machine' },
      ],
      links: [
        { source: 'wiener', target: 'cybernetics', label: 'founded' },
        { source: 'cybernetics', target: 'feedback_loops', label: 'includes' },
        { source: 'cybernetics', target: 'homeostasis', label: 'includes' },
        { source: 'shannon', target: 'information_theory', label: 'founded' },
        { source: 'information_theory', target: 'entropy', label: 'defines' },
        { source: 'cybernetics', target: 'information_theory', label: 'relates_to' },
        { source: 'cybernetics', target: 'ai', label: 'influences' },
        { source: 'cybernetics', target: 'neural_networks', label: 'inspires' },
        { source: 'neural_networks', target: 'transformers', label: 'evolves_to' },
        { source: 'transformers', target: 'llms', label: 'enables' },
        { source: 'cybernetics', target: 'cognitive', label: 'specializes_into' },
        { source: 'cognitive', target: 'predictive_processing', label: 'includes' },
      ]
    };

    // Set graph data in the format expected by react-force-graph
    setGraphData({
      nodes: sampleData.nodes,
      links: sampleData.links.map(link => ({
        source: link.source,
        target: link.target,
        label: link.label
      }))
    });
  }, []);

  // Node colors by type
  const getNodeColor = (node) => {
    const colors = {
      person: '#ff6347',    // tomato
      concept: '#4682b4',   // steelblue
      domain: '#2e8b57',    // seagreen
      default: '#999999'    // gray
    };
    return colors[node.type] || colors.default;
  };

  // Handle node click
  const handleNodeClick = node => {
    // Center the view on the clicked node
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(2.5, 1000);
    }
    
    setSelectedNode(node);
    
    // Highlight connected nodes and links
    const connectedNodes = new Set();
    const connectedLinks = new Set();
    
    graphData.links.forEach(link => {
      if (link.source.id === node.id || link.target.id === node.id) {
        connectedNodes.add(link.source.id);
        connectedNodes.add(link.target.id);
        connectedLinks.add(link);
      }
    });
    
    setHighlightNodes(connectedNodes);
    setHighlightLinks(connectedLinks);
  };

  // Reset highlights when clicking away
  const handleBackgroundClick = () => {
    setSelectedNode(null);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
  };

  // Filter nodes based on type
  const filteredData = React.useMemo(() => {
    let nodes = [...graphData.nodes];
    let links = [...graphData.links];
    
    // Apply type filter
    if (filterType !== 'all') {
      nodes = nodes.filter(node => node.type === filterType);
      
      // Keep only links where both source and target are in filtered nodes
      const nodeIds = new Set(nodes.map(n => n.id));
      links = links.filter(link => 
        nodeIds.has(typeof link.source === 'object' ? link.source.id : link.source) && 
        nodeIds.has(typeof link.target === 'object' ? link.target.id : link.target)
      );
    }
    
    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      nodes = nodes.filter(node => 
        node.label.toLowerCase().includes(term) || 
        (node.desc && node.desc.toLowerCase().includes(term))
      );
      
      // Keep only links where both source and target are in filtered nodes
      const nodeIds = new Set(nodes.map(n => n.id));
      links = links.filter(link => 
        nodeIds.has(typeof link.source === 'object' ? link.source.id : link.source) && 
        nodeIds.has(typeof link.target === 'object' ? link.target.id : link.target)
      );
    }
    
    return { nodes, links };
  }, [graphData, filterType, searchTerm]);

  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 bg-slate-100 border-b">
        <h1 className="text-2xl font-bold mb-2">Cybernetics Digital Garden</h1>
        <div className="flex flex-wrap gap-4">
          <div>
            <select 
              className="p-2 border rounded"
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
            >
              <option value="all">All Types</option>
              <option value="person">People</option>
              <option value="concept">Concepts</option>
              <option value="domain">Domains</option>
            </select>
          </div>
          <div className="flex-grow">
            <input
              type="text"
              placeholder="Search nodes..."
              className="p-2 border rounded w-full"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>
      
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative">
          <ForceGraph2D
            ref={fgRef}
            graphData={filteredData}
            nodeColor={node => getNodeColor(node)}
            nodeLabel={node => `${node.label}: ${node.desc || ''}`}
            linkLabel={link => link.label}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.25}
            onNodeClick={handleNodeClick}
            onBackgroundClick={handleBackgroundClick}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.label;
              const fontSize = 12/globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              
              // Node circle
              ctx.beginPath();
              const size = 5;
              ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
              ctx.fillStyle = highlightNodes.has(node.id) ? '#ffff00' : getNodeColor(node);
              ctx.fill();
              
              // Text background for readability
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.5);
              
              ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
              ctx.fillRect(
                node.x - bckgDimensions[0] / 2,
                node.y + size + 2,
                bckgDimensions[0],
                bckgDimensions[1]
              );
              
              // Text label
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = '#000';
              ctx.fillText(
                label,
                node.x,
                node.y + size + 2 + bckgDimensions[1]/2
              );
            }}
            linkWidth={link => highlightLinks.has(link) ? 3 : 1}
            linkColor={link => highlightLinks.has(link) ? '#ff9900' : '#cccccc'}
            cooldownTicks={100}
          />
        </div>
        
        {selectedNode && (
          <div className="w-64 border-l p-4 bg-white overflow-y-auto">
            <h2 className="text-xl font-bold mb-2">{selectedNode.label}</h2>
            <div className="mb-2">
              <span className="px-2 py-1 rounded text-xs font-medium bg-gray-200">
                {selectedNode.type}
              </span>
            </div>
            <p className="text-sm mb-4">{selectedNode.desc}</p>
            
            <h3 className="font-bold mb-1">Connections:</h3>
            <ul className="text-sm">
              {Array.from(highlightLinks).map((link, i) => (
                <li key={i} className="mb-1 ml-2">
                  {link.source.id === selectedNode.id ? (
                    <span>→ <b>{link.target.label}</b> ({link.label})</span>
                  ) : (
                    <span>← <b>{link.source.label}</b> ({link.label})</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default CyberneticsOntologyGraph;