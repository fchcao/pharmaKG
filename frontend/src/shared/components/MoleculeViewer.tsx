import React, { useState, useEffect } from 'react';
import { Image, Alert, Spin, Button } from 'antd';
import {
  DownloadOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  ReloadOutlined,
} from '@ant-design/icons';

interface MoleculeViewerProps {
  smiles: string;
  name?: string;
  width?: number;
  height?: number;
  showControls?: boolean;
  onImageLoad?: () => void;
  onError?: (error: Error) => void;
}

/**
 * MoleculeViewer Component
 *
 * Renders a 2D molecular structure from SMILES notation using external services.
 * Falls back gracefully if the service is unavailable.
 *
 * Features:
 * - Uses NIH Cactus Chemical Identifier Service for rendering
 * - Automatic fallback SVG generation on error
 * - Zoom and refresh controls
 * - Download capability
 */
export const MoleculeViewer: React.FC<MoleculeViewerProps> = ({
  smiles,
  name = 'Compound',
  width = 300,
  height = 300,
  showControls = true,
  onImageLoad,
  onError,
}) => {
  const [imageUrl, setImageUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    if (!smiles) {
      setError('No SMILES string provided');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    // Use NIH Cactus Chemical Identifier Service
    // This service is free, reliable, and doesn't require authentication
    const url = `https://cactus.nci.nih.gov/chemical/structure/${encodeURIComponent(smiles)}/image?format=png&w=${width}&h=${height}`;
    setImageUrl(url);
  }, [smiles, width, height]);

  const handleImageLoad = () => {
    setLoading(false);
    onImageLoad?.();
  };

  const handleImageError = () => {
    setLoading(false);
    const errorMsg = 'Failed to load molecular structure';
    setError(errorMsg);
    onError?.(new Error(errorMsg));
  };

  const handleDownload = () => {
    if (!imageUrl) return;

    // Create a temporary link to download the image
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `${name.replace(/[^a-z0-9]/gi, '_')}_structure.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleRefresh = () => {
    // Force reload by adding a timestamp
    const timestamp = Date.now();
    const url = `${imageUrl}&t=${timestamp}`;
    setImageUrl(url);
    setLoading(true);
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  if (!smiles) {
    return (
      <Alert
        message="No structure data"
        description="SMILES notation not available for this compound"
        type="info"
        showIcon
      />
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 12,
      }}
    >
      <div
        style={{
          position: 'relative',
          overflow: 'hidden',
          border: '1px solid #d9d9d9',
          borderRadius: '8px',
          backgroundColor: '#ffffff',
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: height,
        }}
      >
        {loading && (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
            }}
          >
            <Spin tip="Loading structure..." />
          </div>
        )}

        {!error && (
          <Image
            src={imageUrl}
            alt={`${name} structure`}
            style={{
              width: '100%',
              height: 'auto',
              maxWidth: `${width * scale}px`,
              maxHeight: `${height * scale}px`,
              objectFit: 'contain',
              display: loading ? 'none' : 'block',
            }}
            onLoad={handleImageLoad}
            onError={handleImageError}
            preview={{
              scaleStep: 0.2,
              minScale: 0.5,
              maxScale: 3,
            }}
          />
        )}

        {error && (
          <div
            style={{
              padding: '40px',
              textAlign: 'center',
              color: '#8c8c8c',
            }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="120"
              height="120"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M6 9l6 6 6-6" />
              <circle cx="12" cy="12" r="10" />
              <text
                x="50%"
                y="50%"
                dominantBaseline="middle"
                textAnchor="middle"
                fontSize="10"
                fontFamily="Arial"
                fill="#999"
              >
                Structure unavailable
              </text>
            </svg>
            <div style={{ marginTop: 12, fontSize: 12 }}>{error}</div>
          </div>
        )}
      </div>

      {showControls && (
        <div
          style={{
            display: 'flex',
            gap: 8,
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          <Button
            size="small"
            icon={<ZoomOutOutlined />}
            onClick={handleZoomOut}
            disabled={scale <= 0.5}
          >
            Zoom Out
          </Button>
          <Button
            size="small"
            icon={<ZoomInOutlined />}
            onClick={handleZoomIn}
            disabled={scale >= 3}
          >
            Zoom In
          </Button>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={handleDownload}
            disabled={!!error}
          >
            Download
          </Button>
        </div>
      )}

      <div style={{ fontSize: 11, color: '#8c8c8c', textAlign: 'center' }}>
        Powered by{' '}
        <a
          href="https://cactus.nci.nih.gov/chemical/structure"
          target="_blank"
          rel="noopener noreferrer"
        >
          NIH Cactus
        </a>
      </div>
    </div>
  );
};

export default MoleculeViewer;
