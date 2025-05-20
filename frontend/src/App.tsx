// src/App.tsx

import React, { useState } from "react";
import NavBar from "./components/NavBar";
import SearchContainer from "./containers/SearchContainer";
import About from "./components/About";

const App: React.FC = () => {
  const [showAbout, setShowAbout] = useState(false);

  const containerStyle = {
    maxWidth: '780px',
    margin: '0 auto',
    fontFamily: 'Arial, sans-serif',
    padding: '10px'
  };

  const handleAboutClick = () => {
    setShowAbout(true);
  };

  const handleHomeClick = () => {
    setShowAbout(false);
  };

  return (
    <div style={containerStyle}>
      <NavBar onAboutClick={handleAboutClick} />
      
      {showAbout ? (
        <>
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <a 
              href="#" 
              onClick={(e) => {
                e.preventDefault();
                handleHomeClick();
              }}
              style={{ color: '#0000EE', fontSize: '20px' }}
            >
              ← Back to Search
            </a>
          </div>
          <About />
        </>
      ) : (
        <SearchContainer />
      )}
    </div>
  );
};

export default App;
