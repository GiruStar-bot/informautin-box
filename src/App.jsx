import { useState } from "react";
import DataSourceCredits from "./components/DataSourceCredits";

const LAYERS = ["gdelt", "natural", "economic"];

export default function App() {
  const [activeLayer, setActiveLayer] = useState("gdelt");

  return (
    <div style={{ fontFamily: "sans-serif", padding: "1rem" }}>
      <h1>informautin-box</h1>

      <nav style={{ marginBottom: "1rem" }}>
        {LAYERS.map((layer) => (
          <button
            key={layer}
            onClick={() => setActiveLayer(layer)}
            style={{
              marginRight: "0.5rem",
              padding: "0.4rem 0.8rem",
              fontWeight: activeLayer === layer ? "bold" : "normal",
              background: activeLayer === layer ? "#0366d6" : "#f6f8fa",
              color: activeLayer === layer ? "#fff" : "#24292e",
              border: "1px solid #d1d5da",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            {layer}
          </button>
        ))}
      </nav>

      <DataSourceCredits activeLayer={activeLayer} />
    </div>
  );
}
