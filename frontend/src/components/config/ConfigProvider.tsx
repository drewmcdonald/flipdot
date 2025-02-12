import { ReactNode, Suspense } from "react";
import { ConfigContext } from "./ConfigContext";
import { api } from "../../api";
import { Loading } from "../Loading";

interface ConfigProviderProps {
  children: ReactNode;
}

export function ConfigProvider({ children }: ConfigProviderProps) {
  const { data } = api.useSuspenseQuery("get", "/config", {
    cache: "force-cache",
  });

  return (
    <Suspense fallback={<Loading />}>
      <ConfigContext.Provider value={data}>{children}</ConfigContext.Provider>
    </Suspense>
  );
}
