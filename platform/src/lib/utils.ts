import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format a timestamp to a relative time string (e.g., "5m", "2d")
 * @param dateString ISO date string
 * @returns Formatted relative time string
 */
export const formatTimeAgo = (dateString: string): string => {
  try {
    // Parse the ISO timestamp and handle it explicitly as UTC
    const date = new Date(dateString + 'Z');  // Ensure UTC parsing with 'Z'
    const now = new Date();

    // Use getTime() for direct millisecond comparison
    const dateMs = date.getTime();
    const nowMs = now.getTime();
    const diffMs = nowMs - dateMs; // Positive if date is in the past, negative if in the future

    const absDiffSecs = Math.floor(Math.abs(diffMs) / 1000);

    // Threshold for 'now' (e.g., less than 10 seconds)
    if (absDiffSecs < 10) {
      return 'now';
    }

    const absDiffMins = Math.floor(absDiffSecs / 60);
    const absDiffHours = Math.floor(absDiffMins / 60);
    const absDiffDays = Math.floor(absDiffHours / 24);
    const absDiffMonths = Math.floor(absDiffDays / 30); // Approximate months

    if (absDiffMonths > 0) {
      return `${absDiffMonths}mo`;
    } else if (absDiffDays > 0) {
      return `${absDiffDays}d`;
    } else if (absDiffHours > 0) {
      return `${absDiffHours}h`;
    } else if (absDiffMins > 0) {
      return `${absDiffMins}m`;
    } else {
      // Seconds difference (if > 10s threshold)
      return `${absDiffSecs}s`;
    }
  } catch (e) {
    console.error('Date parsing error:', e);
    return 'Invalid date';
  }
};
