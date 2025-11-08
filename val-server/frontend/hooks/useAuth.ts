import {
  useMutation,
  useQuery,
  useQueryClient,
} from "https://esm.sh/@tanstack/react-query@5.56.2?deps=react@18.2.0";
import { authApi } from "../services/api.ts";

export const useAuthCheck = () => {
  return useQuery({
    queryKey: ["auth"],
    queryFn: authApi.checkAuth,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useLogin = (onSuccess?: () => void) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: () => {
      queryClient.setQueryData(["auth"], true);
      onSuccess?.();
    },
  });
};

export const useLogout = (onSuccess?: () => void) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.setQueryData(["auth"], false);
      queryClient.clear(); // Clear all cached data on logout
      onSuccess?.();
    },
  });
};
