import { Box, VStack } from "@chakra-ui/react";
import { DisplayModeForm } from "./DisplayModeForm";

export function Display() {
  return (
    <Box p={4}>
      <VStack>
        <DisplayModeForm />
      </VStack>
    </Box>
  );
}
