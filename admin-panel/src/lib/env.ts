import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1, "DATABASE_URL is required"),
  AUTH_SECRET: z.string().min(1, "AUTH_SECRET is required"),
  AUTH_URL: z.string().url().optional(),
  ADMIN_USERNAME: z.string().min(3, "ADMIN_USERNAME is required"),
  ADMIN_PASSWORD: z.string().min(12, "ADMIN_PASSWORD is required"),
  APP_NAME: z.string().default("CHERE Admin"),
  SESSION_TIMEOUT_MINUTES: z.coerce.number().default(30),
  REMEMBER_ME_DAYS: z.coerce.number().default(30),
});

const parsedEnv = envSchema.safeParse({
  NODE_ENV: process.env.NODE_ENV,
  DATABASE_URL: process.env.DATABASE_URL,
  AUTH_SECRET: process.env.AUTH_SECRET,
  AUTH_URL: process.env.AUTH_URL,
  ADMIN_USERNAME: process.env.ADMIN_USERNAME,
  ADMIN_PASSWORD: process.env.ADMIN_PASSWORD,
  APP_NAME: process.env.APP_NAME,
  SESSION_TIMEOUT_MINUTES: process.env.SESSION_TIMEOUT_MINUTES,
  REMEMBER_ME_DAYS: process.env.REMEMBER_ME_DAYS,
});

if (!parsedEnv.success) {
  console.error("Invalid environment variables", parsedEnv.error.flatten().fieldErrors);
  throw new Error("Environment validation failed");
}

export const env = parsedEnv.data;
