import { Navigate, useLocation } from "react-router-dom";

import type { AppRole } from "./menu";
import { useAuthStore } from "../stores/authStore";
import { useUserStore } from "../stores/userStore";

interface GuardProps {
  children: JSX.Element;
}

interface RoleGuardProps extends GuardProps {
  roles: AppRole[];
}

export function ProtectedRoute({ children }: GuardProps) {
  const token = useAuthStore((state) => state.token);
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}

export function RoleGuard({ children, roles }: RoleGuardProps) {
  const user = useUserStore((state) => state.user);
  const isLoading = useUserStore((state) => state.isLoading);

  if (isLoading) {
    return <div className="page-loading">加载权限中...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const hasRole = user.roles.some((role) => roles.includes(role));

  if (!hasRole) {
    return <Navigate to="/403" replace />;
  }

  return children;
}
