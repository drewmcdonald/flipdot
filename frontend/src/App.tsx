import { Picker } from "./components/Picker";

function App() {
  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-3xl font-bold">Flippy</h1>
      <div className="flex gap-4 h-full">
        <Picker />
      </div>
    </div>
  );
}

export default App;
