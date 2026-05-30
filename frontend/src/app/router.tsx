import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "../components/Layout/AppLayout";
import { ProtectedRoute, RoleGuard } from "./guards";
import { HomePage } from "../pages/Home/HomePage";
import { LoginPage } from "../pages/Login/LoginPage";
import { KnowledgeBasePage } from "../pages/KnowledgeBase/KnowledgeBasePage";
import { ChatPage } from "../pages/Chat/ChatPage";
import { PersonalSpacePage } from "../pages/PersonalSpace/PersonalSpacePage";
import { AgentsPage } from "../pages/Agents/AgentsPage";
import { ExpensePage } from "../pages/Expense/ExpensePage";
import { FinancePage } from "../pages/Finance/FinancePage";
import { AdminPage } from "../pages/Admin/AdminPage";
import { ForbiddenPage } from "../pages/Forbidden/ForbiddenPage";
import { NotFoundPage } from "../pages/NotFound/NotFoundPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />
  },
  {
    path: "/403",
    element: <ForbiddenPage />
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <HomePage />
      },
      {
        path: "knowledge-base",
        element: <KnowledgeBasePage />
      },
      {
        path: "chat",
        element: <ChatPage />
      },
      {
        path: "personal-space",
        element: <PersonalSpacePage />
      },
      {
        path: "agents",
        element: <AgentsPage />
      },
      {
        path: "expense",
        element: <ExpensePage />
      },
      {
        path: "finance",
        element: (
          <RoleGuard roles={["admin", "finance"]}>
            <FinancePage />
          </RoleGuard>
        )
      },
      {
        path: "admin",
        element: (
          <RoleGuard roles={["admin", "department_admin"]}>
            <AdminPage />
          </RoleGuard>
        )
      }
    ]
  },
  {
    path: "*",
    element: <NotFoundPage />
  }
]);
