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
  const [searched, setSearched] = useState<string>("false");

  const handleSearch = async () => {
    try {
      const searchResults = await searchDocuments(query);
      setResults(searchResults);
      setError(null);
      setSearched("true")
    } catch (err) {
      setError("Failed to fetch search results");
      setResults([]);
      setSearched("false")
    }
  };
  return (
    <div>
      <img src="/diamond.png" alt = "logo" style = {{height: "100px", width: "100px", position: "absolute"}}></img>
      {searched === 'false' && (
        <Container>
          <Box mt={4} textAlign="center">
            <Typography color = 'white' fontFamily= 'myFont' variant="h1">Hidden Gems</Typography>
            <Typography color = 'white' fontFamily= 'myFont' variant="h5">Search for hidden gems in the web</Typography>
          </Box>
          <SearchBar
            query={query}
            setQuery={setQuery}
            handleSearch={handleSearch}
          />
          {error && <Typography color="error">{error}</Typography>}
          <SearchResults results={results} />
        </Container>
      )}
      {searched === 'true' && (
        <Container>
          <Box mt={4} textAlign="center">
            <Typography color = 'white' fontFamily= 'myFont' variant="h4">Hidden Gems</Typography>
          </Box>
          <SearchBar
            query={query}
            setQuery={setQuery}
            handleSearch={handleSearch}
            
          />
          
          {error && <Typography color="error">{error}</Typography>}
          <SearchResults results={results} />
        </Container>
        )}
    </div>
  );
};

export default SearchContainer;
