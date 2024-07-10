// src/components/SearchResults.tsx

import React from "react";
import { SearchResult } from "../api/SearchAPI";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";

interface SearchResultsProps {
  results: SearchResult[];
}

const SearchResults: React.FC<SearchResultsProps> = ({ results }) => {
  return (
    <Box mt={4} display="flex" justifyContent="center" alignItems="center">
      <List style={{ width: "600px" }}>
        {results.map((result) => (
          <ListItem alignItems="flex-start">
            <ListItemText
              primary={<Typography variant="h6">{result.title}</Typography>}
              secondary={
                <Typography variant="body2">
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {result.url}
                  </a>
                </Typography>
              }
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default SearchResults;
