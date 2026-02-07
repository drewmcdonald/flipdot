import { VirtualDisplay } from "./components/VirtualDisplay";
import "./App.css";

function App() {
  return (
    <div className="app">
      <h1>FlipDot Virtual Display</h1>
      <VirtualDisplay displayName="main" />
    </div>
  );
}

export default App;
