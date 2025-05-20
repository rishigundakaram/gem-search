// src/components/SearchBox.tsx

import React from 'react';

interface SearchBoxProps {
  query: string;
  setQuery: (query: string) => void;
  handleSearch: () => void;
}

const SearchBox: React.FC<SearchBoxProps> = ({ 
  query, 
  setQuery, 
  handleSearch 
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="vspace-lg">
      <input
        type="text"
        className="retro-input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        style={{ width: '400px' }}
      />
      <input 
        type="submit" 
        className="retro-btn" 
        value="Search" 
      />
    </form>
  );
};

export default SearchBox;