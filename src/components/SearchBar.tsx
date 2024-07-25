// src/components/SearchBar.tsx

import React from "react";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import "./SearchBar.css";

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
/*<div className = "button">
  <Button variant="contained" color="primary" onClick={handleSearch} >
    Search
  </Button>
</div>*/
  return (
    <div>
      <Box display="flex" justifyContent="center" alignItems="center" mt={2}>
        <TextField
          variant="outlined"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          label="Search"
          style={{ marginRight: "10px", width: "600px" , backgroundColor: "white", borderRadius: "7px"}}
        />
      </Box>

    </div>
  );
};
export default SearchBar;
