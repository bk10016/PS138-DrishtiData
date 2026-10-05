import { createContext, useContext, useState, ReactNode } from "react";

type Ctx = { run: any; setRun: (r: any) => void; bench: any; setBench: (b: any) => void; scenario: any; setScenario: (s: any) => void };
const C = createContext<Ctx>(null as unknown as Ctx);

export function StateProvider({ children }: { children: ReactNode }) {
  const [run, setRun] = useState<any>(null);
  const [bench, setBench] = useState<any>(null);
  const [scenario, setScenario] = useState<any>(null);
  return <C.Provider value={{ run, setRun, bench, setBench, scenario, setScenario }}>{children}</C.Provider>;
}
export const useAppState = () => useContext(C);
