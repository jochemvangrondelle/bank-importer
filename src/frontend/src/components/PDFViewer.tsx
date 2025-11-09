import { useEffect, useRef, useState } from "react";
import { Spin, Alert } from "antd";

interface PDFViewerProps {
  fileUrl: string;
  width?: string | number;
  height?: string | number;
}

export const PDFViewer = ({
  fileUrl,
  width = "100%",
  height = 600,
}: PDFViewerProps) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
  }, [fileUrl]);

  const handleLoad = () => {
    setLoading(false);
  };

  const handleError = () => {
    setLoading(false);
    setError("Failed to load PDF. Please check if the file is valid.");
  };

  return (
    <div style={{ position: "relative", width, height }}>
      {loading && (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            zIndex: 1,
          }}
        >
          <Spin size="large" />
        </div>
      )}
      {error ? (
        <Alert message={error} type="error" />
      ) : (
        <iframe
          ref={iframeRef}
          src={fileUrl}
          width={width}
          height={height}
          style={{
            border: "1px solid #d9d9d9",
            borderRadius: 4,
          }}
          onLoad={handleLoad}
          onError={handleError}
          title="PDF Viewer"
        />
      )}
    </div>
  );
};
