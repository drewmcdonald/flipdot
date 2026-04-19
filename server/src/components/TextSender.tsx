import { useState } from "react";
import { useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";

interface TextSenderProps {
  displayName?: string;
}

export function TextSender({ displayName = "main" }: TextSenderProps) {
  const sendText = useMutation(api.content.adhoc.sendText);
  const [text, setText] = useState("");
  const [font, setFont] = useState("axion_6x7");
  const [scroll, setScroll] = useState(false);
  const [asOverride, setAsOverride] = useState(true);
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setSending(true);
    try {
      await sendText({
        text: text.trim(),
        font,
        display_name: displayName,
        as_override: asOverride,
        scroll,
      });
      setText("");
    } finally {
      setSending(false);
    }
  };

  return (
    <section className="panel">
      <h2>Send Message</h2>
      <form onSubmit={handleSubmit} className="text-sender-form">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text..."
          maxLength={100}
          className="input-text"
        />
        <div className="form-row">
          <select
            value={font}
            onChange={(e) => setFont(e.target.value)}
            className="input-sm"
          >
            <option value="axion_6x7">Axion 6x7</option>
            <option value="cg_pixel_4x5">CG Pixel 4x5</option>
          </select>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={scroll}
              onChange={(e) => setScroll(e.target.checked)}
            />
            Scroll
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={asOverride}
              onChange={(e) => setAsOverride(e.target.checked)}
            />
            Override
          </label>
          <button
            type="submit"
            className="btn-sm btn-primary"
            disabled={sending || !text.trim()}
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </section>
  );
}
