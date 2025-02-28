import { useConfig } from "./config/useConfig";
import { api } from "@/api";
import { Button, Box, Text } from "@chakra-ui/react";
import { useState } from "react";
import { DisplayModeConfig } from "@/api/types";

// Define types for JSON schema properties
interface SchemaProperty {
  type: string;
  title?: string;
  description?: string;
  default?: unknown;
  enum?: string[];
  format?: string;
}

interface JsonSchema {
  properties?: Record<string, SchemaProperty>;
}

export function DisplayModeForm() {
  const { mutate: mutateMode } = api.useMutation("patch", "/mode");
  const { modes, fonts } = useConfig();
  const [selectedMode, setSelectedMode] = useState<string | null>(null);
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});

  const handleModeClick = (modeName: string) => {
    setSelectedMode(selectedMode === modeName ? null : modeName);
    // Initialize form values with default values from the schema if available
    if (selectedMode !== modeName) {
      const mode = modes.find((m) => m.mode_name === modeName);
      if (mode?.opts) {
        const initialValues: Record<string, unknown> = {};
        // If opts has properties, initialize form values with defaults
        const schemaOpts = mode.opts as JsonSchema;
        if (schemaOpts.properties) {
          Object.entries(schemaOpts.properties).forEach(([key, prop]) => {
            initialValues[key] = prop.default !== undefined ? prop.default : "";
          });
        }
        setFormValues(initialValues);
      }
    }
  };

  const handleInputChange = (name: string, value: unknown) => {
    setFormValues((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (modeName: string) => {
    mutateMode({
      body: {
        mode_name: modeName,
        opts: formValues,
      },
    });
    setSelectedMode(null);
  };

  // Function to render form fields based on JSON schema
  const renderFormFields = (mode: DisplayModeConfig) => {
    const schemaOpts = mode.opts as JsonSchema;
    if (!schemaOpts.properties) {
      return <Text>No configurable options available</Text>;
    }

    return Object.entries(schemaOpts.properties).map(
      ([propName, propSchema]) => {
        const type = propSchema.type;
        const title = propSchema.title || propName;
        const description = propSchema.description;

        return (
          <div key={propName} style={{ marginBottom: "1rem" }}>
            <label
              style={{
                display: "block",
                fontWeight: "bold",
                marginBottom: "0.25rem",
              }}
            >
              {title}
            </label>
            {renderInputByType(propName, type, propSchema)}
            {description && (
              <Text fontSize="sm" color="gray.500" mt={1}>
                {description}
              </Text>
            )}
          </div>
        );
      }
    );
  };

  // Function to render the appropriate input based on the property type
  const renderInputByType = (
    propName: string,
    type: string,
    propSchema: SchemaProperty
  ) => {
    const value =
      formValues[propName] !== undefined ? formValues[propName] : "";

    switch (type) {
      case "string":
        if (propSchema.enum) {
          return (
            <select
              style={{
                width: "100%",
                padding: "0.5rem",
                borderWidth: "1px",
                borderRadius: "0.375rem",
                borderColor: "#E2E8F0",
              }}
              value={value as string}
              onChange={(e) => {
                handleInputChange(propName, e.target.value);
              }}
            >
              {propSchema.enum.map((option: string) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          );
        }
        if (propSchema.format === "textarea") {
          return (
            <textarea
              style={{
                width: "100%",
                padding: "0.5rem",
                borderWidth: "1px",
                borderRadius: "0.375rem",
                borderColor: "#E2E8F0",
              }}
              value={value as string}
              onChange={(e) => {
                handleInputChange(propName, e.target.value);
              }}
            />
          );
        }
        if (propSchema.title === "Font") {
          return (
            <select
              style={{
                width: "100%",
                padding: "0.5rem",
                borderWidth: "1px",
                borderRadius: "0.375rem",
                borderColor: "#E2E8F0",
              }}
              value={value as string}
              onChange={(e) => {
                handleInputChange(propName, e.target.value);
              }}
            >
              {Object.keys(fonts.fonts).map((fontName) => (
                <option key={fontName} value={fontName}>
                  {fontName}
                </option>
              ))}
            </select>
          );
        }
        return (
          <input
            type="text"
            style={{
              width: "100%",
              padding: "0.5rem",
              borderWidth: "1px",
              borderRadius: "0.375rem",
              borderColor: "#E2E8F0",
            }}
            value={value as string}
            onChange={(e) => {
              handleInputChange(propName, e.target.value);
            }}
          />
        );

      case "number":
      case "integer":
        return (
          <input
            type="number"
            style={{
              width: "100%",
              padding: "0.5rem",
              borderWidth: "1px",
              borderRadius: "0.375rem",
              borderColor: "#E2E8F0",
            }}
            value={value as number}
            onChange={(e) => {
              handleInputChange(propName, Number(e.target.value));
            }}
          />
        );

      case "boolean":
        return (
          <div style={{ display: "flex", alignItems: "center" }}>
            <input
              type="checkbox"
              style={{ marginRight: "0.5rem" }}
              checked={Boolean(value)}
              onChange={(e) => {
                handleInputChange(propName, e.target.checked);
              }}
            />
            <span style={{ fontSize: "0.875rem" }}>Enable</span>
          </div>
        );

      default:
        return (
          <input
            type="text"
            style={{
              width: "100%",
              padding: "0.5rem",
              borderWidth: "1px",
              borderRadius: "0.375rem",
              borderColor: "#E2E8F0",
            }}
            value={value as string}
            onChange={(e) => {
              handleInputChange(propName, e.target.value);
            }}
          />
        );
    }
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
                  {renderFormFields(mode)}
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
