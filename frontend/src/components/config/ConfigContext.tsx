import { createContext } from "react";
import { Config } from "../../api/types";

export const ConfigContext = createContext<Config | undefined>(undefined);
