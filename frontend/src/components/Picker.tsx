import { Suspense } from "react";
import { api } from "../api";
import type { components } from "../api/schema";
import { Loading } from "./Loading";

export function Picker() {
  const { data } = api.useSuspenseQuery("get", "/modes");
  console.log(data.display_modes);
  return (
    <div className="flex flex-col gap-4 h-1/2">
      <Suspense fallback={<Loading />}>
        {Object.entries(data.display_modes).map(([name, mode]) => (
          <PickerPanel key={name} mode={mode} />
        ))}
      </Suspense>
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
