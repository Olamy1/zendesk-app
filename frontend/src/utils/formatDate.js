import { TIMEZONE } from "../config";
export const fmtLocal = (d) =>
  new Date(d).toLocaleString("en-US", { timeZone: TIMEZONE, year: "numeric", month: "short", day: "numeric" });
