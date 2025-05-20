// src/components/SearchResults.tsx

import React from "react";
import { SearchResult } from "../api/SearchAPI";

interface SearchResultsProps {
  results: SearchResult[];
}

const SearchResults: React.FC<SearchResultsProps> = ({ results }) => {
  if (results.length === 0) {
    return null;
  }

  return (
    <div style={{ marginTop: '15px' }}>
      {results.map((result, index) => (
        <div 
          key={index} 
          style={{ 
            marginBottom: '10px',
            paddingLeft: '20px',
            position: 'relative'
          }}
        >
          <div style={{ position: 'absolute', left: '5px' }}>•</div>
          <a 
            href={result.url} 
            style={{
              color: '#0000EE',
              fontWeight: 'bold',
              textDecoration: 'none'
            }}
            target="_blank" 
            rel="noopener noreferrer"
          >
            {result.title}
          </a>
          <div style={{ 
            color: '#006400', 
            fontSize: '12px' 
          }}>
            {result.url}
          </div>
        </div>
      ))}
    </div>
  );
};

export default SearchResults;
