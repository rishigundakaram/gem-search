// src/components/ResultItem.tsx

import React from 'react';
import { SearchResult } from '../api/SearchAPI';

interface ResultItemProps {
  result: SearchResult;
}

const ResultItem: React.FC<ResultItemProps> = ({ result }) => {
  return (
    <li>
      <a href={result.url} target="_blank" rel="noopener noreferrer">
        {result.title}
      </a>
      <div className="url vspace-sm">{result.url}</div>
    </li>
  );
};

export default ResultItem;