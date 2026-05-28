import { Upload, Typography } from "antd";
import type { UploadProps } from "antd";

const { Text } = Typography;

interface FileUploaderProps {
  title?: string;
  props?: UploadProps;
}

export function FileUploader({ title = "上传文件", props }: FileUploaderProps) {
  return (
    <div className="uploader-card">
      <Text className="uploader-title">{title}</Text>
      <Upload.Dragger {...props} className="uploader-dragger">
        <p className="uploader-hint">将文件拖拽到此处，或点击上传</p>
      </Upload.Dragger>
    </div>
  );
}
