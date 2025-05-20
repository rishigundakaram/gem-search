// src/components/NavBar.tsx

import React from "react";

interface NavBarProps {
  onAboutClick: () => void;
}

const NavBar: React.FC<NavBarProps> = ({ onAboutClick }) => {
  const navBarStyle = {
    textAlign: 'center' as const,
    marginBottom: '15px'
  };

  const navItemStyle = {
    display: 'inline-block',
    textAlign: 'center' as const,
    margin: '0 10px',
    fontSize: '20px',
    color: '#0000EE',
    cursor: 'pointer',
    textDecoration: 'none'
  };

  return (
    <div style={navBarStyle}>
      <a 
        href="#about" 
        style={navItemStyle}
        onClick={(e) => {
          e.preventDefault();
          onAboutClick();
        }}
      >
        About
      </a>
    </div>
  );
};

export default NavBar;