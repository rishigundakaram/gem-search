// src/pages/About.tsx
import Box from "@mui/material/Box";
import React from "react";
import ReactMarkdown from "react-markdown";

const markdownContent = `
I'm amazed you stumbled upon this...

Sometimes that happens on the internet. 99.999% of the internet is garbage. 
But every once in a while you stumble across a blog, article, review, or something 
else that inflects your life. 

When I reflect on the gems that I've stumbled upon during my internet browsing career, 
they follow some clear principles. 

They are derived from **Lived Experience**, these source for the writing is real life.
These sources are dense with experience. 

These spaces on the internet provide a **unique perspective** something that you're 
going to find on the first couple pages of google search.

As a direct corollory of the first two, these gems are always **human-generated** and 
deeply reflect the authors behind them. 


With gem-search I hope to introduce a new paradigm of search where we look for content 
written by real people. 
`;

const About: React.FC = () => {
  return (
    <Box
      sx={{
        width: "40%",
        margin: "0 auto",
        padding: 2,
      }}
    >
      <ReactMarkdown>{markdownContent}</ReactMarkdown>
    </Box>
  );
};

export default About;
