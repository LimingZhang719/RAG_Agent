import { Layout, Menu, Space, Typography, Dropdown, Button } from "antd";
import { LogoutOutlined, UserOutlined } from "@ant-design/icons";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { appMenu } from "../../app/menu";
import { useAuthStore } from "../../stores/authStore";
import { useUserStore } from "../../stores/userStore";

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const clearToken = useAuthStore((state) => state.clearToken);
  const clearUser = useUserStore((state) => state.clearUser);
  const user = useUserStore((state) => state.user);

  const availableMenu = appMenu.filter((item) => {
    if (!item.roles) {
      return true;
    }
    if (!user) {
      return false;
    }
    return user.roles.some((role) => item.roles?.includes(role));
  });

  const menuItems = availableMenu.map((item) => ({
    key: item.key,
    icon: <item.icon />,
    label: item.label
  }));

  const pathToKey = availableMenu.reduce<Record<string, string>>((acc, item) => {
    acc[item.path] = item.key;
    return acc;
  }, {});

  const selectedKey = pathToKey[location.pathname] || "home";

  function handleMenuClick({ key }: { key: string }) {
    const target = availableMenu.find((item) => item.key === key);
    if (target) {
      navigate(target.path);
    }
  }

  function handleLogout() {
    clearToken();
    clearUser();
    navigate("/login");
  }

  const userMenu = [
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      onClick: handleLogout
    }
  ];

  return (
    <Layout className="app-shell">
      <Sider className="app-sider" width={240} collapsedWidth={72}>
        <div className="brand">
          <div className="brand-mark">AR</div>
          <div className="brand-name">Agentic RAG</div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
          className="app-menu"
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Space size={16}>
            <Text className="header-title">智能 Agentic-RAG 平台</Text>
            <Text className="header-subtitle">v0 前端基础框架</Text>
          </Space>
          <Dropdown menu={{ items: userMenu }} placement="bottomRight">
            <Button type="text" className="user-chip" icon={<UserOutlined />}>
              {user?.full_name || user?.username || "未登录"}
            </Button>
          </Dropdown>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
