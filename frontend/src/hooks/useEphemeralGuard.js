import { useEffect } from "react";

export function useEphemeralGuard(mode, hasResults) {
  useEffect(() => {
    if (mode !== "ephemeral" || !hasResults) return;
    const handler = (e) => {
      e.preventDefault();
      e.returnValue = "You are in No-Save Mode. All unsaved results will be permanently lost.";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [mode, hasResults]);
}
