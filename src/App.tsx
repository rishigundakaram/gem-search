// src/App.tsx

import React from "react";
import SearchContainer from "./containers/SearchContainer";
import "./App.css";
const App: React.FC = () => {
  return (
    <div className ="body">
      <SearchContainer />
    </div>
  );
};

export default App;
