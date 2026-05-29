import { Select, Tag, Typography } from "antd";

import type { KnowledgeBaseItem } from "../../api/kb";

const { Text } = Typography;

interface KnowledgeBaseSelectorProps {
  items: KnowledgeBaseItem[];
  value: string[];
  onChange: (value: string[]) => void;
}

const scopeLabelMap: Record<string, string> = {
  company: "公司级",
  department: "部门级",
  personal: "个人级"
};

export function KnowledgeBaseSelector({
  items,
  value,
  onChange
}: KnowledgeBaseSelectorProps) {
  return (
    <div className="kb-selector">
      <Text type="secondary">知识库</Text>
      <Select
        mode="multiple"
        allowClear
        placeholder="选择一个或多个知识库"
        value={value}
        onChange={onChange}
        options={items.map((item) => ({
          value: item.id,
          label: item.name
        }))}
        optionRender={(option) => {
          const kb = items.find((item) => item.id === option.value);
          if (!kb) {
            return option.label;
          }
          return (
            <div className="kb-option">
              <span>{kb.name}</span>
              <Tag color="blue">{scopeLabelMap[kb.visibility_scope]}</Tag>
            </div>
          );
        }}
      />
    </div>
  );
}
