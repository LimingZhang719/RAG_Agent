import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";

import { HomePage } from "../pages/Home/HomePage";

export function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <HomePage />
    </ConfigProvider>
  );
}
