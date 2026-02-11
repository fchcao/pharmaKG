/**
 * GraphViewer.tsx - Main graph visualization component using Cytoscape.js
 * Optimized for rendering 1000+ nodes smoothly
 */

import React, { useRef, useEffect, useCallback, useMemo, forwardRef, useImperativeHandle } from 'react';
import cytoscape, { ElementDefinition } from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import {
  GraphData,
  GraphViewerProps,
  GraphViewerRef,
  ENTITY_STYLES,
  RELATION_STYLES,
  EntityType
} from './types';

// Register the layout
cytoscape.use(coseBilkent);

export const GraphViewer = forwardRef<GraphViewerRef, GraphViewerProps>(({
  data,
  onNodeClick,
  onEdgeClick,
  onBackgroundClick,
  height = '600px',
  width = '100%',
  selectable = true,
  zoomEnabled = true,
  panEnabled = true
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  // Convert graph data to Cytoscape elements
  const elements = useMemo(() => {
    const nodes: ElementDefinition[] = data.nodes.map(node => {
      const style = ENTITY_STYLES[node.type] || ENTITY_STYLES.Compound;

      return {
        data: {
          id: node.id,
          label: node.label,
          type: node.type,
          weight: node.weight,
          properties: node.properties,
          // Style properties embedded in data for quick access
          backgroundColor: style.backgroundColor,
          borderColor: style.borderColor,
          shape: style.shape,
          width: style.width,
          height: style.height,
          fontSize: style.fontSize,
          labelColor: style.labelColor
        },
        position: node.x && node.y ? { x: node.x, y: node.y } : undefined
      };
    });

    const edges: ElementDefinition[] = data.edges.map(edge => {
      const style = RELATION_STYLES[edge.type] || RELATION_STYLES.TARGETS;

      return {
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.label || edge.type,
          type: edge.type,
          weight: edge.weight,
          properties: edge.properties,
          color: style.color,
          width: style.width,
          lineStyle: style.style
        }
      };
    });

    return [...nodes, ...edges];
  }, [data]);

  // Generate stylesheet from entity and relation styles
  const stylesheet = useMemo(() => {
    const styles: any[] = [];

    // Node styles by type
    Object.entries(ENTITY_STYLES).forEach(([type, style]) => {
      styles.push({
        selector: `node[type="${type}"]`,
        style: {
          'background-color': style.backgroundColor,
          'border-color': style.borderColor || style.backgroundColor,
          'border-width': 2,
          'shape': style.shape,
          'width': style.width,
          'height': style.height,
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-size': style.fontSize,
          'color': style.labelColor || '#FFFFFF',
          'text-outline-color': style.borderColor,
          'text-outline-width': 2,
          'text-wrap': 'wrap',
          'text-max-width': `${style.width * 0.8}px`,
          'text-justification': 'center'
        }
      });
    });

    // Edge styles by type
    Object.entries(RELATION_STYLES).forEach(([type, style]) => {
      styles.push({
        selector: `edge[type="${type}"]`,
        style: {
          'line-color': style.color,
          'target-arrow-color': style.color,
          'width': style.width,
          'line-style': style.style as any,
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'font-size': 9,
          'text-rotation': 'autorotate',
          'text-margin-y': -10,
          'color': style.color,
          'text-background-color': '#FFFFFF',
          'text-background-opacity': 0.8,
          'text-background-padding': '2px'
        }
      });
    });

    // Highlight styles for selected nodes
    styles.push({
      selector: 'node:selected',
      style: {
        'border-width': 4,
        'border-color': '#FFD700',
        'box-shadow': '0 0 20px #FFD700'
      }
    });

    // Highlight styles for selected edges
    styles.push({
      selector: 'edge:selected',
      style: {
        'width': 4,
        'line-color': '#FFD700',
        'target-arrow-color': '#FFD700'
      }
    });

    // Highlight neighbors of selected node
    styles.push({
      selector: 'node.highlighted',
      style: {
        'border-width': 3,
        'border-color': '#FFD700',
        'background-color': '#FFF59D'
      }
    });

    styles.push({
      selector: 'edge.highlighted',
      style: {
        'width': 3,
        'line-color': '#FFD700'
      }
    });

    // Fade out unselected elements
    styles.push({
      selector: '.faded',
      style: {
        'opacity': 0.3
      }
    });

    return styles;
  }, []);

  // Layout configuration
  const layout = useMemo(() => ({
    name: 'cose-bilkent',
    quality: 'proof',
    animate: true,
    animationDuration: 500,
    animationEasing: 'ease-out',
    fit: true,
    padding: 30,
    nodeRepulsion: 4500,
    idealEdgeLength: 100,
    edgeElasticity: 0.45,
    nestingFactor: 0.1,
    nodeDimensionsIncludeLabels: true,
    randomize: true,
    tilingPaddingVertical: 10,
    tilingPaddingHorizontal: 10
  }), []);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current) return;

    const startTime = performance.now();

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: [],
      style: stylesheet,
      layout: undefined, // We'll run layout separately
      minZoom: 0.1,
      maxZoom: 5,
      wheelSensitivity: 0.2,
      selectionType: 'single'
    });

    const endTime = performance.now();
    console.log(`Cytoscape initialization: ${(endTime - startTime).toFixed(2)}ms`);

    // Setup event handlers
    const cy = cyRef.current;

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();

      if (onNodeClick) {
        onNodeClick({
          id: nodeData.id,
          label: nodeData.label,
          type: nodeData.type,
          properties: nodeData.properties,
          weight: nodeData.weight
        });
      }
    });

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      const edgeData = edge.data();

      if (onEdgeClick) {
        onEdgeClick({
          id: edgeData.id,
          source: edgeData.source,
          target: edgeData.target,
          label: edgeData.label,
          type: edgeData.type,
          properties: edgeData.properties,
          weight: edgeData.weight
        });
      }
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        if (onBackgroundClick) {
          onBackgroundClick();
        }
      }
    });

    // Setup resize observer
    resizeObserverRef.current = new ResizeObserver(() => {
      if (cyRef.current) {
        cyRef.current.fit(undefined, 30);
      }
    });
    resizeObserverRef.current.observe(containerRef.current);

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
      cy.destroy();
    };
  }, [stylesheet, onNodeClick, onEdgeClick, onBackgroundClick]);

  // Update elements when data changes
  useEffect(() => {
    if (!cyRef.current) return;

    const startTime = performance.now();

    // Batch add elements for better performance
    cyRef.current.elements().remove();
    cyRef.current.add(elements);

    // Run layout
    cyRef.current.layout(layout).run();

    const endTime = performance.now();
    const renderTime = (endTime - startTime).toFixed(2);
    console.log(`Graph render (${data.nodes.length} nodes, ${data.edges.length} edges): ${renderTime}ms`);

    // Send performance metrics
    if (window.performance) {
      const metrics = {
        nodeCount: data.nodes.length,
        edgeCount: data.edges.length,
        renderTime: parseFloat(renderTime),
        timestamp: new Date().toISOString()
      };
      console.log('GraphViewer Performance Metrics:', metrics);
    }
  }, [elements, layout, data.nodes.length, data.edges.length]);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    cy: cyRef.current,
    fit: (padding = 30) => {
      if (cyRef.current) {
        cyRef.current.fit(undefined, padding);
      }
    },
    center: () => {
      if (cyRef.current) {
        cyRef.current.center();
      }
    },
    zoom: (level) => {
      if (cyRef.current) {
        cyRef.current.zoom(level);
      }
    },
    exportAs: (format) => {
      if (cyRef.current) {
        if (format === 'png') {
          return cyRef.current.png({ full: true, scale: 2 });
        } else if (format === 'jpg') {
          return cyRef.current.jpg({ full: true, scale: 2 });
        } else if (format === 'json') {
          return JSON.stringify(cyRef.current.json());
        }
      }
    },
    getSelectedElements: () => {
      if (cyRef.current) {
        return cyRef.current.elements(':selected').map(el => el.data());
      }
      return [];
    },
    clearSelection: () => {
      if (cyRef.current) {
        cyRef.current.elements().unselect();
      }
    }
  }), []);

  return (
    <div
      ref={containerRef}
      style={{
        width,
        height,
        border: '1px solid #d9d9d9',
        borderRadius: '6px',
        backgroundColor: '#fafafa',
        position: 'relative'
      }}
    />
  );
});

GraphViewer.displayName = 'GraphViewer';

export default GraphViewer;
