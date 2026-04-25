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
  const [loading, setLoading] = useState<boolean>(false);

  const handleSearch = async () => {
    const trimmed = query.trim();
    if (trimmed.length === 0) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const searchResults = await searchDocuments(trimmed);
      setResults(searchResults);
    } catch (err) {
      setError("Failed to fetch search results");
      setResults([]);
    } finally {
      setLoading(false);
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
        loading={loading}
      />
      {error && <Typography color="error">{error}</Typography>}
      <SearchResults results={results} />
    </Container>
  );
};

export default SearchContainer;
