// src/components/Logo.tsx

import React from 'react';

const Logo: React.FC = () => {
  return (
    <div className="logo-container vspace-sm">
      <img src="/img/gem.png" alt="gem search" />
      <h1>gem search</h1>
    </div>
  );
};

export default Logo;