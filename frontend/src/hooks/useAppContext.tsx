import React, { createContext, useContext, useEffect, useState } from "react";
import { setApiAuth } from "../api/client";
import type { Issue, UserRole } from "../types";

interface AppContextType {
  role: UserRole;
  setRole: (role: UserRole) => void;
  selectedSprintId: number;
  setSelectedSprintId: (id: number) => void;
  darkMode: boolean;
  setDarkMode: (dark: boolean) => void;
  selectedIssue: Issue | null;
  setSelectedIssue: (issue: Issue | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRoleState] = useState<UserRole>("manager");
  const [selectedSprintId, setSelectedSprintId] = useState<number>(2); // Default to active Sprint 24 (id: 2)
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);

  const setRole = (newRole: UserRole) => {
    setRoleState(newRole);
    setApiAuth(newRole);
  };

  useEffect(() => {
    setApiAuth(role);
  }, [role]);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <AppContext.Provider
      value={{
        role,
        setRole,
        selectedSprintId,
        setSelectedSprintId,
        darkMode,
        setDarkMode,
        selectedIssue,
        setSelectedIssue,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error("useApp must be used within an AppProvider");
  return context;
};
