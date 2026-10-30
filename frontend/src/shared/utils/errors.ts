import { ApiError } from "../lib/api";

export function getError(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : error instanceof Error
      ? error.message
      : "Có lỗi không xác định.";
}

