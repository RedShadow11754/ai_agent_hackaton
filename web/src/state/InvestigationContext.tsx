/**
 * Keeps investigation data alive across pages (investigate -> results -> review)
 * so the analyst does not re-run the agent when navigating.
 *
 * TODO: optionally persist to sessionStorage so a refresh keeps the result.
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type {
  AssessmentResponse,
  ClarificationResponse,
  InvestigateResponse,
} from "../types/api";

interface InvestigationContextValue {
  /** Message text the analyst pasted. */
  message: string;
  setMessage: (message: string) => void;
  /** Optional sender line shown to the analyst. */
  sender: string;
  setSender: (sender: string) => void;
  /** Raw API response, either a clarification or an assessment. */
  response: InvestigateResponse | null;
  setResponse: (response: InvestigateResponse | null) => void;
  /** Narrowed assessment, or null when the response is a clarification. */
  assessment: AssessmentResponse | null;
  /** Narrowed clarification, or null when the response is an assessment. */
  clarification: ClarificationResponse | null;
  /** Clear everything and start a new investigation. */
  reset: () => void;
}

const InvestigationContext = createContext<InvestigationContextValue | null>(null);

export function InvestigationProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState("");
  const [sender, setSender] = useState("");
  const [response, setResponse] = useState<InvestigateResponse | null>(null);

  const reset = useCallback(() => {
    setMessage("");
    setSender("");
    setResponse(null);
  }, []);

  const value = useMemo<InvestigationContextValue>(
    () => ({
      message,
      setMessage,
      sender,
      setSender,
      response,
      setResponse,
      assessment: response?.type === "assessment" ? response : null,
      clarification: response?.type === "clarification" ? response : null,
      reset,
    }),
    [message, sender, response, reset],
  );

  return (
    <InvestigationContext.Provider value={value}>{children}</InvestigationContext.Provider>
  );
}

/** Access the current investigation. Throws outside the provider. */
export function useInvestigation(): InvestigationContextValue {
  const context = useContext(InvestigationContext);
  if (!context) {
    throw new Error("useInvestigation must be used inside <InvestigationProvider>.");
  }
  return context;
}
