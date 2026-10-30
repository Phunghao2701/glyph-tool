import { createContext, useContext, type ReactNode } from "react";

type FlushCallback = (() => Promise<void>) | null;
type RegisterFlush = (flush: FlushCallback) => void;
const EditorFlushContext = createContext<RegisterFlush | null>(null);

export function EditorFlushProvider({ register, children }: { register: RegisterFlush; children: ReactNode }) {
  return <EditorFlushContext.Provider value={register}>{children}</EditorFlushContext.Provider>;
}

export function useRegisterEditorFlush() {
  const register = useContext(EditorFlushContext);
  if (!register) throw new Error("useRegisterEditorFlush must be used inside EditorFlushProvider.");
  return register;
}

