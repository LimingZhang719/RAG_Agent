import { Card, Tag, Typography } from "antd";

const { Text } = Typography;

export interface CitationItem {
  document_name: string;
  snippet: string;
  page_no?: number | null;
}

interface CitationPanelProps {
  items?: CitationItem[];
}

export function CitationPanel({ items = [] }: CitationPanelProps) {
  if (items.length === 0) {
    return (
      <Card className="citation-panel">
        <Text type="secondary">暂无引用来源</Text>
      </Card>
    );
  }

  return (
    <Card className="citation-panel">
      {items.map((item, index) => (
        <div key={`${item.document_name}-${index}`} className="citation-item">
          <Tag color="blue">引用 {index + 1}</Tag>
          <div>
            <Text strong>{item.document_name}</Text>
            <Text className="citation-snippet">{item.snippet}</Text>
            {item.page_no ? (
              <Text type="secondary">第 {item.page_no} 页</Text>
            ) : null}
          </div>
        </div>
      ))}
    </Card>
  );
}
