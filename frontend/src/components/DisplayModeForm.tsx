import { useConfig } from "./config/useConfig";
import { api } from "@/api";
import { Button, Box, Text } from "@chakra-ui/react";
import { useState } from "react";

export function DisplayModeForm() {
  const { mutate: mutateMode } = api.useMutation("patch", "/mode");
  const { modes } = useConfig();
  const [selectedMode, setSelectedMode] = useState<string | null>(null);

  const handleModeClick = (modeName: string) => {
    setSelectedMode(selectedMode === modeName ? null : modeName);
  };

  const handleSubmit = (modeName: string) => {
    mutateMode({
      body: {
        mode_name: modeName,
        opts: {}, // TODO
      },
    });
    setSelectedMode(null);
  };

  return (
    <Box width="100%">
      <Box display="flex" flexDirection="column" gap={4}>
        {modes.map((mode) => (
          <Box
            key={mode.mode_name}
            borderWidth="1px"
            borderRadius="lg"
            p={4}
            cursor="pointer"
            boxShadow="sm"
          >
            <Box
              onClick={() => {
                handleModeClick(mode.mode_name);
              }}
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              mb={selectedMode === mode.mode_name ? 4 : 0}
            >
              <Text fontWeight="bold">{mode.mode_name}</Text>
            </Box>
            {selectedMode === mode.mode_name && (
              <Box>
                <Box display="flex" flexDirection="column" gap={4}>
                  <Button
                    onClick={() => {
                      handleSubmit(mode.mode_name);
                    }}
                  >
                    Apply Mode
                  </Button>
                </Box>
              </Box>
            )}
          </Box>
        ))}
      </Box>
    </Box>
  );
}
