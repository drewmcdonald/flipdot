import { ReactNode, Suspense } from "react";
import { ConfigContext } from "./ConfigContext";
import { api } from "../../api";
import { Spinner } from "@chakra-ui/react";

interface ConfigProviderProps {
  children: ReactNode;
}

export function ConfigProvider({ children }: ConfigProviderProps) {
  const { data } = api.useSuspenseQuery("get", "/config", {
    cache: "force-cache",
  });

  return (
    <Suspense fallback={<Spinner />}>
      <ConfigContext.Provider value={data}>{children}</ConfigContext.Provider>
    </Suspense>
  );
}
