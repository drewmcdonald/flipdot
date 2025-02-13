import type { components } from "../api/schema";
import { useConfig } from "./config/useConfig";

export function Picker() {
  const config = useConfig();
  return (
    <div>
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
    <div>
      <pre>{JSON.stringify(mode, undefined, 2)}</pre>
    </div>
  );
}
