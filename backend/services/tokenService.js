import { randomBytes } from "crypto";

export const generateRefreshToken = () => randomBytes(64).toString("hex");
