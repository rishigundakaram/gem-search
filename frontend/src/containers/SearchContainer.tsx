// src/containers/SearchContainer.tsx

import React, { useState } from "react";
import { searchDocuments, SearchResult } from "../api/SearchAPI";
import SearchBar from "../components/SearchBar";
import SearchResults from "../components/SearchResults";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";

const SearchContainer: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    try {
      const searchResults = await searchDocuments(query);
      setResults(searchResults);
      setError(null);
    } catch (err) {
      setError("Failed to fetch search results");
      setResults([]);
    }
  };

  return (
    <Container>
      <Box mt={4} textAlign="center">
        <Typography variant="h4">Gem Search</Typography>
      </Box>
      <SearchBar
        query={query}
        setQuery={setQuery}
        handleSearch={handleSearch}
      />
      {error && <Typography color="error">{error}</Typography>}
      <SearchResults results={results} />
    </Container>
  );
};

export default SearchContainer;
