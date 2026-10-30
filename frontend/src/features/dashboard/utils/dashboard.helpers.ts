import { ApiError, type Project } from "../../../shared/lib/api";

export function errorText(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : "Có lỗi không xác định.";
}

export function projectNeedsReview(project: Project) {
  return project.variants.some(variant => !!variant.currentRevision && !variant.currentRevision.approved);
}

