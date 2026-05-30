import { Alert, Button, Empty, Space, Spin, Typography } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState } from "react";

import {
  fetchDocumentSource,
  type DocumentItem
} from "../../api/documents";

const { Text } = Typography;

interface DocumentPreviewProps {
  document: DocumentItem | null;
}

function formatFileSize(size: number) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function isTextPreviewType(fileType: string) {
  return (
    fileType.startsWith("text/") ||
    fileType === "application/json" ||
    fileType === "application/xml"
  );
}

export function DocumentPreview({ document }: DocumentPreviewProps) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileType = document?.file_type || "application/octet-stream";
  const canPreview = useMemo(
    () =>
      fileType === "application/pdf" ||
      fileType.startsWith("image/") ||
      isTextPreviewType(fileType),
    [fileType]
  );

  useEffect(() => {
    if (!document) {
      setObjectUrl(null);
      setTextContent(null);
      setError(null);
      return;
    }

    let currentUrl: string | null = null;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setTextContent(null);
    setObjectUrl(null);

    fetchDocumentSource(document.id)
      .then(async (blob) => {
        if (cancelled) {
          return;
        }
        currentUrl = URL.createObjectURL(blob);
        setObjectUrl(currentUrl);
        if (isTextPreviewType(fileType)) {
          setTextContent(await blob.text());
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("源文件加载失败");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl);
      }
    };
  }, [document, fileType]);

  if (!document) {
    return <Empty description="请选择文档" />;
  }

  const downloadButton = objectUrl ? (
    <Button icon={<DownloadOutlined />} href={objectUrl} download={document.file_name}>
      下载源文件
    </Button>
  ) : null;

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      <Space wrap>
        <Text strong>{document.file_name}</Text>
        <Text type="secondary">{fileType}</Text>
        <Text type="secondary">{formatFileSize(document.size)}</Text>
        {downloadButton}
      </Space>

      {loading ? <Spin /> : null}
      {error ? <Alert type="error" message={error} showIcon /> : null}

      {!loading && !error && !canPreview ? (
        <Alert
          type="info"
          message="该文件类型暂不支持在线预览，请下载源文件查看。"
          showIcon
        />
      ) : null}

      {!loading && !error && objectUrl && fileType === "application/pdf" ? (
        <iframe
          title={document.file_name}
          src={objectUrl}
          style={{
            width: "100%",
            height: 640,
            border: "1px solid #f0f0f0",
            borderRadius: 6
          }}
        />
      ) : null}

      {!loading && !error && objectUrl && fileType.startsWith("image/") ? (
        <img
          src={objectUrl}
          alt={document.file_name}
          style={{
            maxWidth: "100%",
            maxHeight: 640,
            objectFit: "contain",
            border: "1px solid #f0f0f0",
            borderRadius: 6
          }}
        />
      ) : null}

      {!loading && !error && textContent !== null ? (
        <pre
          style={{
            maxHeight: 640,
            overflow: "auto",
            padding: 12,
            border: "1px solid #f0f0f0",
            borderRadius: 6,
            background: "#fafafa",
            whiteSpace: "pre-wrap"
          }}
        >
          {textContent}
        </pre>
      ) : null}
    </Space>
  );
}
