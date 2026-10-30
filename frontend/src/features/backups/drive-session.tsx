import { createContext, useContext, useEffect, useMemo, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import type { GoogleDriveConnection, PickedDriveFolder } from "./google-drive-picker";

type DriveSessionValue = {
  connection: GoogleDriveConnection | null;
  setConnection: Dispatch<SetStateAction<GoogleDriveConnection | null>>;
  folder: PickedDriveFolder | null;
  setFolder: Dispatch<SetStateAction<PickedDriveFolder | null>>;
};

const DriveSessionContext = createContext<DriveSessionValue | null>(null);

export function DriveSessionProvider({ children }: { children: ReactNode }) {
  const [connection, setConnection] = useState<GoogleDriveConnection | null>(null);
  const [folder, setFolder] = useState<PickedDriveFolder | null>(null);

  useEffect(() => {
    if (!connection) return;
    const timeout = window.setTimeout(() => {
      setConnection(null);
      setFolder(null);
    }, Math.max(0, connection.expiresAt - Date.now()));
    return () => window.clearTimeout(timeout);
  }, [connection]);

  const value = useMemo(() => ({ connection, setConnection, folder, setFolder }), [connection, folder]);
  return <DriveSessionContext.Provider value={value}>{children}</DriveSessionContext.Provider>;
}

export function useDriveSession() {
  const value = useContext(DriveSessionContext);
  if (!value) throw new Error("useDriveSession must be used inside DriveSessionProvider.");
  return value;
}
