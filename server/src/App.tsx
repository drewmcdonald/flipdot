import { VirtualDisplay } from "./components/VirtualDisplay";
import { ControlPanel } from "./components/ControlPanel";
import "./App.css";

function App() {
  return (
    <div className="app">
      <h1>FlipDot Virtual Display</h1>
      <VirtualDisplay displayName="main" />
      <ControlPanel displayName="main" />
    </div>
  );
}

export default App;
