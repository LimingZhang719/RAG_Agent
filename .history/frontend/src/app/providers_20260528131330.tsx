import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo } from "react";

import { getMe } from "../api/auth";
import { useAuthStore } from "../stores/authStore";
import { useUserStore } from "../stores/userStore";

interface AppProvidersProps {
  children: React.ReactNode;
}

function AuthBootstrap({ children }: AppProvidersProps) {
  const token = useAuthStore((state) => state.token);
  const clearToken = useAuthStore((state) => state.clearToken);
  const setUser = useUserStore((state) => state.setUser);
  const clearUser = useUserStore((state) => state.clearUser);
  const setLoading = useUserStore((state) => state.setLoading);

  const { data, isError, isFetching } = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    enabled: Boolean(token),
    retry: false
  });

  useEffect(() => {
    setLoading(Boolean(token) && isFetching);
  }, [isFetching, setLoading, token]);

  useEffect(() => {
    if (data) {
      setUser(data);
    }
  }, [data, setUser]);

  useEffect(() => {
    if (isError) {
      clearToken();
      clearUser();
    }
  }, [clearToken, clearUser, isError]);

  useEffect(() => {
    if (!token) {
      clearUser();
      setLoading(false);
    }
  }, [clearUser, setLoading, token]);

  return <>{children}</>;
}

export function AppProviders({ children }: AppProvidersProps) {
  const queryClient = useMemo(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            staleTime: 60_000
          }
        }
      }),
    []
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <AuthBootstrap>{children}</AuthBootstrap>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
