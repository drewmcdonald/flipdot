import { useQuery } from "convex/react";
import { useConvexAuth } from "@convex-dev/auth/react";
import { api } from "../../convex/_generated/api";
import { StatusPanel } from "./StatusPanel";
import { SourcesList } from "./SourcesList";
import { RotationEditor } from "./RotationEditor";
import { OverrideManager } from "./OverrideManager";
import { TextSender } from "./TextSender";
import { ClockSettings } from "./ClockSettings";
import { SignIn } from "./SignIn";
import "./ControlPanel.css";

interface ControlPanelProps {
  displayName?: string;
}

export function ControlPanel({ displayName = "main" }: ControlPanelProps) {
  const { isAuthenticated } = useConvexAuth();
  const sources = useQuery(api.content_sources.listSources);
  const config = useQuery(api.display_config.getConfigPublic, {
    display_name: displayName,
  });
  const display = useQuery(api.displays.getCurrentDisplay, {
    name: displayName,
  });

  return (
    <div className="control-panel">
      <StatusPanel display={display} config={config} sources={sources} />
      {isAuthenticated ? (
        <>
          <TextSender displayName={displayName} />
          <RotationEditor
            config={config}
            sources={sources}
            displayName={displayName}
          />
          <OverrideManager
            config={config}
            sources={sources}
            displayName={displayName}
          />
          <ClockSettings config={config} displayName={displayName} />
        </>
      ) : (
        <SignIn />
      )}
      <SourcesList sources={sources} />
    </div>
  );
}
