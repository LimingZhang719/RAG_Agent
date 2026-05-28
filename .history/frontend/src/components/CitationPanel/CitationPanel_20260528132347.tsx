import { Card, Tag, Typography } from "antd";

const { Text } = Typography;

interface CitationItem {
  title: string;
  snippet: string;
  source?: string;
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
        <div key={`${item.title}-${index}`} className="citation-item">
          <Tag color="blue">引用 {index + 1}</Tag>
          <div>
            <Text strong>{item.title}</Text>
            <Text className="citation-snippet">{item.snippet}</Text>
            {item.source && <Text type="secondary">{item.source}</Text>}
          </div>
        </div>
      ))}
    </Card>
  );
}
