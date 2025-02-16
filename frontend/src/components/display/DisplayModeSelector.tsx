import { StateObject } from "../../api/types";
import { useConfig } from "../config/useConfig";
import { api } from "@/api";
import { useCallback, useState } from "react";
import {
  NativeSelectField,
  NativeSelectRoot,
} from "@/components/ui/native-select";

export function DisplayModeSelector({
  initialState,
}: {
  initialState: StateObject;
}) {
  const [mode, setMode] = useState<string>(initialState.mode.mode_name);
  const { mutate: mutateMode } = api.useMutation("patch", "/mode");

  const handleModeChange = useCallback(
    (newMode: string) => {
      console.log("newMode", newMode);
      mutateMode(
        { body: { mode_name: newMode } },
        {
          onSuccess: (m) => {
            console.log("m", m);
            setMode(m.mode_name);
          },
        }
      );
    },
    [mutateMode]
  );

  return <ModeSelect mode={mode} setMode={handleModeChange} />;
}
function useModes() {
  const { modes } = useConfig();
  return modes.map((m) => m.mode_name);
}

interface ModeSelectProps {
  mode: string;
  setMode: (mode: string) => void;
}

function ModeSelect({ mode, setMode }: ModeSelectProps) {
  const availableModes = useModes();
  return (
    <NativeSelectRoot size="sm" width="240px">
      <NativeSelectField
        placeholder="Select option"
        value={mode}
        onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
          setMode(e.target.value);
        }}
      >
        {availableModes.map((m) => (
          <option value={m} key={m}>
            {m}
          </option>
        ))}
      </NativeSelectField>
    </NativeSelectRoot>
  );
}
