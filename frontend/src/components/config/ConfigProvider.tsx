import { ReactNode } from "react";
import { ConfigContext } from "./ConfigContext";
import { api } from "../../api";
import { Alert, Button, Center, Flex, Spinner } from "@chakra-ui/react";

interface ConfigProviderProps {
  children: ReactNode;
}

export function ConfigProvider({ children }: ConfigProviderProps) {
  const res = api.useQuery("get", "/config", {
    cache: "force-cache",
  });

  if (res.status === "error") {
    return (
      <Center h="100vh">
        <Flex flexDirection="column" maxW={480} alignItems="center" gap={2}>
          <Alert.Root status="error">
            <Alert.Indicator />
            <Alert.Title>Unable to reach display</Alert.Title>
          </Alert.Root>
          <Button variant="outline" onClick={() => void res.refetch()}>
            Try again
          </Button>
        </Flex>
      </Center>
    );
  }

  if (res.status === "pending") {
    return (
      <Center h="100vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  return (
    <ConfigContext.Provider value={res.data}>{children}</ConfigContext.Provider>
  );
}
