import { Box, Flex, Spinner, VStack } from "@chakra-ui/react";
import { DisplayModeSelector } from "./DisplayModeSelector";
import { api } from "@/api";

export function Display() {
  const { data: state, isSuccess } = api.useQuery("get", "/state");

  if (!isSuccess) {
    return (
      <Flex justify="center" align="center" height="100%">
        <Spinner size="xl" />
      </Flex>
    );
  }

  return (
    <Box p={4}>
      <VStack>
        <DisplayModeSelector initialState={state} />
      </VStack>
    </Box>
  );
}
