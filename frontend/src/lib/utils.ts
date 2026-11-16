import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScoreColor(score: number): string {
  if (score >= 70) return "text-red-500 bg-red-500/10 border-red-500/20";
  if (score >= 40) return "text-amber-500 bg-amber-500/10 border-amber-500/20";
  return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
}

export function formatSeverityBadge(severity: string): string {
  switch (severity?.toUpperCase()) {
    case "CRITICAL":
      return "bg-red-500/15 text-red-500 border-red-500/30";
    case "HIGH":
      return "bg-amber-500/15 text-amber-500 border-amber-500/30";
    case "MEDIUM":
      return "bg-yellow-500/15 text-yellow-500 border-yellow-500/30";
    default:
      return "bg-blue-500/15 text-blue-500 border-blue-500/30";
  }
}
