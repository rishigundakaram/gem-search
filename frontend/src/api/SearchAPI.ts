export interface SearchQuery {
  query: string;
}

export interface SearchResult {
  title: string;
  url: string;
}

export async function searchDocuments(query: string): Promise<SearchResult[]> {
  const response = await fetch("http://localhost:8000/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": process.env.REACT_APP_API_KEY || "gem-search-dev-key-12345",
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error("Network response was not ok");
  }

  const results: SearchResult[] = await response.json();
  return results;
}
