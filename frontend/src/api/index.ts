import axios from "axios";
import { message } from "antd";

import { useAuthStore } from "../stores/authStore";
import { useUserStore } from "../stores/userStore";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 15_000
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`
    };
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status as number | undefined;

    if (status === 401) {
      useAuthStore.getState().clearToken();
      useUserStore.getState().clearUser();
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
      return Promise.reject(error);
    }

    if (status === 403) {
      message.error("没有权限访问该资源。");
    } else if (status && status >= 500) {
      message.error("服务暂时不可用，请稍后再试。");
    }

    return Promise.reject(error);
  }
);

export default apiClient;
