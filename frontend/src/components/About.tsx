// src/components/About.tsx

import React, { useState, useEffect } from 'react';

const About: React.FC = () => {
  const [markdown, setMarkdown] = useState<string>('');

  useEffect(() => {
    fetch('/about.md')
      .then(response => response.text())
      .then(text => {
        setMarkdown(text);
      })
      .catch(error => {
        console.error('Error fetching about.md:', error);
      });
  }, []);

  // Simple markdown to HTML conversion for headers and paragraphs
  const markdownToHtml = (md: string) => {
    const html = md
      .replace(/# (.*)/g, '<h1>$1</h1>')
      .replace(/## (.*)/g, '<h2>$1</h2>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    return `<p>${html}</p>`;
  };

  return (
    <div style={{ 
      maxWidth: '600px', 
      margin: '20px auto',
      lineHeight: '1.5'
    }}>
      <div dangerouslySetInnerHTML={{ __html: markdownToHtml(markdown) }} />
    </div>
  );
};

export default About;