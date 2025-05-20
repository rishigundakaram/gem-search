// src/containers/SearchContainer.tsx

import React, { useState } from "react";
import { searchDocuments, SearchResult } from "../api/SearchAPI";
import SearchBar from "../components/SearchBar";
import SearchResults from "../components/SearchResults";

const SearchContainer: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    setError(null);
    
    try {
      const searchResults = await searchDocuments(query);
      setResults(searchResults);
    } catch (err) {
      setError("Failed to fetch search results");
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <>
      <div style={{ textAlign: 'center', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <img src="/diamond.png" alt="Gem" height={50} style={{ marginRight: '10px' }} />
          <h1 style={{ 
            fontSize: '48px', 
            margin: '0',
            textTransform: 'lowercase',
            fontWeight: 'normal'
          }}>
            gem search
          </h1>
        </div>
      </div>
      
      <SearchBar
        query={query}
        setQuery={setQuery}
        handleSearch={handleSearch}
      />
      
      {isSearching && (
        <div style={{ textAlign: 'center' }}>
          <b>Searching...</b>
        </div>
      )}
      
      {error && (
        <div style={{ textAlign: 'center', color: 'red' }}>
          <b>{error}</b>
        </div>
      )}
      
      {!isSearching && <SearchResults results={results} />}
    </>
  );
};

export default SearchContainer;
