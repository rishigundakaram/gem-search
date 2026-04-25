// src/components/SearchBar.tsx

import React from "react";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import ClearIcon from "@mui/icons-material/Clear";

interface SearchBarProps {
  query: string;
  setQuery: (query: string) => void;
  handleSearch: () => void;
  loading: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({
  query,
  setQuery,
  handleSearch,
  loading,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) {
      handleSearch();
    }
  };

  const handleClear = () => {
    setQuery("");
  };

  const showClear = query.length > 0 && !loading;

  return (
    <Box display="flex" justifyContent="center" alignItems="center" mt={2}>
      <TextField
        variant="outlined"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        label="Search"
        disabled={loading}
        style={{ marginRight: "10px", width: "300px" }}
        InputProps={{
          endAdornment: showClear ? (
            <InputAdornment position="end">
              <IconButton
                aria-label="clear search"
                onClick={handleClear}
                edge="end"
                size="small"
              >
                <ClearIcon fontSize="small" />
              </IconButton>
            </InputAdornment>
          ) : null,
        }}
      />
      <Button
        variant="contained"
        color="primary"
        onClick={handleSearch}
        disabled={loading || query.trim().length === 0}
        startIcon={
          loading ? <CircularProgress size={16} color="inherit" /> : null
        }
      >
        {loading ? "Searching" : "Search"}
      </Button>
    </Box>
  );
};
export default SearchBar;
