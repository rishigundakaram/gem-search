// src/components/SearchBar.tsx

import React from "react";

interface SearchBarProps {
  query: string;
  setQuery: (query: string) => void;
  handleSearch: () => void;
}

const SearchBar: React.FC<SearchBarProps> = ({
  query,
  setQuery,
  handleSearch,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  };

  return (
    <div style={{ 
      textAlign: 'center',
      marginTop: '20px',
      marginBottom: '20px'
    }}>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          style={{ 
            padding: '6px', 
            width: '450px',
            border: '1px solid #666',
            fontSize: '16px'
          }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <input 
          type="submit" 
          value="Search" 
          style={{ 
            marginLeft: '5px', 
            padding: '6px 12px',
            fontSize: '16px'
          }}
        />
      </form>
    </div>
  );
};
export default SearchBar;
