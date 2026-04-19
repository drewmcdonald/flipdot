interface Source {
  source_id: string;
  content_id: string;
  frameCount: number;
  updatedAt: number;
}

interface SourcesListProps {
  sources: Source[] | undefined;
}

export function SourcesList({ sources }: SourcesListProps) {
  if (!sources) {
    return (
      <section className="panel">
        <h2>Content Sources</h2>
        <p className="label">Loading...</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Content Sources ({sources.length})</h2>
      <table className="sources-table">
        <thead>
          <tr>
            <th>Source</th>
            <th>Content ID</th>
            <th>Frames</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => (
            <tr key={s.source_id}>
              <td>{s.source_id}</td>
              <td className="mono">{s.content_id}</td>
              <td>{s.frameCount}</td>
              <td>{new Date(s.updatedAt).toLocaleTimeString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
