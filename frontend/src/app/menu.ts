import type { ComponentType } from "react";
import {
  BookOutlined,
  DollarOutlined,
  FileTextOutlined,
  HomeOutlined,
  RobotOutlined,
  SafetyOutlined,
  UserOutlined
} from "@ant-design/icons";

export type AppRole = "admin" | "department_admin" | "user" | "finance";

export interface AppMenuItem {
  key: string;
  label: string;
  path: string;
  icon: ComponentType;
  roles?: AppRole[];
}

export const appMenu: AppMenuItem[] = [
  {
    key: "home",
    label: "首页",
    path: "/",
    icon: HomeOutlined
  },
  {
    key: "knowledge-base",
    label: "知识库",
    path: "/knowledge-base",
    icon: BookOutlined
  },
  {
    key: "chat",
    label: "知识问答",
    path: "/chat",
    icon: FileTextOutlined
  },
  {
    key: "personal-space",
    label: "个人空间",
    path: "/personal-space",
    icon: UserOutlined
  },
  {
    key: "agents",
    label: "智能体中心",
    path: "/agents",
    icon: RobotOutlined
  },
  {
    key: "expense",
    label: "报销助手",
    path: "/expense",
    icon: DollarOutlined,
    roles: ["admin", "department_admin", "user", "finance"]
  },
  {
    key: "finance",
    label: "财务审批",
    path: "/finance",
    icon: SafetyOutlined,
    roles: ["admin", "finance"]
  },
  {
    key: "admin",
    label: "管理",
    path: "/admin",
    icon: SafetyOutlined,
    roles: ["admin", "department_admin"]
  }
];
