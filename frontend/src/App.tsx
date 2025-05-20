// src/App.tsx

import React, { useState } from "react";
import Logo from "./components/Logo";
import SearchBox from "./components/SearchBox";
import ResultItem from "./components/ResultItem";
import About from "./components/About";
import RetroEasterEggs from "./components/RetroEasterEggs";
import { SearchResult } from "./api/SearchAPI";
import { useRetroFlags } from "./context/RetroFlags";
import { searchDocuments } from "./api/SearchAPI";

const App: React.FC = () => {
  const [showAbout, setShowAbout] = useState(false);
  const [query, setQuery] = useState<string>("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const { easterEggs, toggleEasterEggs } = useRetroFlags();

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    
    try {
      const searchResults = await searchDocuments(query);
      setResults(searchResults);
    } catch (err) {
      console.error("Failed to fetch search results:", err);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAboutClick = () => {
    setShowAbout(true);
  };

  const handleHomeClick = () => {
    setShowAbout(false);
  };

  return (
    <div className="retro-container">
      {easterEggs && <RetroEasterEggs />}
      
      {showAbout ? (
        <>
          <div className="vspace-sm">
            <a 
              href="#" 
              onClick={(e) => {
                e.preventDefault();
                handleHomeClick();
              }}
            >
              ← Back to Search
            </a>
          </div>
          <div className="vspace-lg">
            <About />
          </div>
        </>
      ) : (
        <>
          <Logo />
          <SearchBox 
            query={query}
            setQuery={setQuery}
            handleSearch={handleSearch}
          />
          
          {isSearching ? (
            <div className="vspace-sm">Searching...</div>
          ) : results.length > 0 ? (
            <div className="vspace-lg">
              <ul className="results-list">
                {results.map((result, index) => (
                  <ResultItem key={index} result={result} />
                ))}
              </ul>
            </div>
          ) : null}
        </>
      )}

      <div className="vspace-lg">
        <hr className="retro-rule" />
        <small>© 2025 gem search</small>
      </div>

      <small className="nav">
        <a href="#" onClick={(e) => {
          e.preventDefault();
          handleAboutClick();
        }}>About</a> | <a href="#">Help</a> |{' '}
        <a href="#" onClick={(e) => {
          e.preventDefault();
          toggleEasterEggs();
        }}>Toggle 2003 Mode</a>
      </small>
    </div>
  );
};

export default App;
