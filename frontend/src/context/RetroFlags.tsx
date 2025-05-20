// src/context/RetroFlags.tsx

import React, { createContext, useContext, ReactNode, useState } from 'react';

interface RetroFlagsContextType {
  easterEggs: boolean;
  toggleEasterEggs: () => void;
}

const RetroFlagsContext = createContext<RetroFlagsContextType | undefined>(undefined);

export const useRetroFlags = (): RetroFlagsContextType => {
  const context = useContext(RetroFlagsContext);
  if (!context) {
    throw new Error('useRetroFlags must be used within a RetroFlagsProvider');
  }
  return context;
};

interface RetroFlagsProviderProps {
  children: ReactNode;
}

export const RetroFlagsProvider: React.FC<RetroFlagsProviderProps> = ({ children }) => {
  const [easterEggs, setEasterEggs] = useState<boolean>(false);

  const toggleEasterEggs = () => {
    setEasterEggs(prev => !prev);
  };

  return (
    <RetroFlagsContext.Provider value={{ easterEggs, toggleEasterEggs }}>
      {children}
    </RetroFlagsContext.Provider>
  );
};

export default RetroFlagsContext;