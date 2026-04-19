import { useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";

const TIMEZONES = [
  { value: "America/New_York", label: "Eastern" },
  { value: "America/Chicago", label: "Central" },
  { value: "America/Denver", label: "Mountain" },
  { value: "America/Los_Angeles", label: "Pacific" },
  { value: "UTC", label: "UTC" },
];

const FONTS = [
  { value: "axion_6x7", label: "Axion 6x7" },
  { value: "cg_pixel_4x5", label: "CG Pixel 4x5" },
];

interface ClockSettingsProps {
  config: {
    generator_settings?: {
      clock?: {
        timezone?: string;
        font?: string;
      };
    };
  } | null | undefined;
  displayName: string;
}

export function ClockSettings({ config, displayName }: ClockSettingsProps) {
  const updateSettings = useMutation(
    api.display_config.updateGeneratorSettings
  );

  const current = config?.generator_settings?.clock;
  const currentTimezone = current?.timezone ?? "America/New_York";
  const currentFont = current?.font ?? "axion_6x7";

  const handleChange = (field: "timezone" | "font", value: string) => {
    updateSettings({
      display_name: displayName,
      source_id: "clock",
      settings: {
        timezone: field === "timezone" ? value : currentTimezone,
        font: field === "font" ? value : currentFont,
      },
    });
  };

  return (
    <section className="panel">
      <h2>Clock Settings</h2>
      <div className="form-row">
        <label className="label">Timezone:</label>
        <select
          value={currentTimezone}
          onChange={(e) => handleChange("timezone", e.target.value)}
          className="input-sm"
        >
          {TIMEZONES.map((tz) => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
        <label className="label">Font:</label>
        <select
          value={currentFont}
          onChange={(e) => handleChange("font", e.target.value)}
          className="input-sm"
        >
          {FONTS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}
