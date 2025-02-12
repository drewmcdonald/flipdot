import type { components } from "../api/schema";
import { useConfig } from "./config/useConfig";

export function Picker() {
  const config = useConfig();
  return (
    <div className="flex flex-col gap-4 h-1/2">
      {Object.entries(config.modes.display_modes).map(([name, mode]) => (
        <PickerPanel key={name} mode={mode} />
      ))}
    </div>
  );
}

type DisplayModeRef =
  components["schemas"]["DisplayModeList"]["display_modes"][string];

function PickerPanel({ mode }: { mode: DisplayModeRef }) {
  return (
    <div className="flex flex-col gap-4 h-1/2">
      <pre>{JSON.stringify(mode, undefined, 2)}</pre>
    </div>
  );
}
