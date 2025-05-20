// src/components/RetroEasterEggs.tsx

import React from 'react';

// Simple Marquee component
export const Marquee: React.FC<{ text: string }> = ({ text }) => {
  return (
    <div style={{
      overflow: 'hidden',
      width: '100%',
      backgroundColor: '#FFFFCC',
      border: '1px solid #CCCCCC',
      padding: '2px 0',
      marginBottom: '10px'
    }}>
      <div style={{
        whiteSpace: 'nowrap',
        animation: 'marquee 20s linear infinite',
        paddingLeft: '100%'
      }}>
        {text}
      </div>
      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-100%); }
        }
      `}</style>
    </div>
  );
};

// Hit Counter component
export const HitCounter: React.FC = () => {
  return (
    <div style={{ margin: '20px 0', textAlign: 'center' }}>
      <div style={{ display: 'inline-block', border: '1px solid #CCCCCC', padding: '4px', backgroundColor: '#EEEEEE' }}>
        <div style={{ fontSize: '10px', color: '#666666', textAlign: 'center' }}>
          Visitors:
        </div>
        <div style={{ fontFamily: 'monospace', padding: '2px 0', fontWeight: 'bold' }}>
          00012879
        </div>
      </div>
    </div>
  );
};

// Combining all Easter eggs in one component
const RetroEasterEggs: React.FC = () => {
  return (
    <>
      <Marquee text="Welcome to Gem Search - Mining the Hidden Gems of the internet since 2003! - Use the search box below to find hidden gems across the web - Click About to learn more!" />
      <HitCounter />
    </>
  );
};

export default RetroEasterEggs;