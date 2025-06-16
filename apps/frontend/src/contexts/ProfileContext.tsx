import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface ProfileContextType {
  profileId: string | null;
  setProfileId: (id: string | null) => void;
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

export const ProfileProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [profileId, setProfileIdState] = useState<string | null>(() => {
    return localStorage.getItem('currentProfileId');
  });

  useEffect(() => {
    if (profileId) {
      localStorage.setItem('currentProfileId', profileId);
    } else {
      localStorage.removeItem('currentProfileId');
    }
  }, [profileId]);

  const setProfileId = (id: string | null) => {
    setProfileIdState(id);
  };

  return (
    <ProfileContext.Provider value={{ profileId, setProfileId }}>
      {children}
    </ProfileContext.Provider>
  );
};

export const useProfile = (): ProfileContextType => {
  const context = useContext(ProfileContext);
  if (context === undefined) {
    throw new Error('useProfile must be used within a ProfileProvider');
  }
  return context;
};
