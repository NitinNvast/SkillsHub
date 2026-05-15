"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Skill {
  id: string;
  skill_id: string;
  name: string;
  category: string;
  proficiency: "novice" | "intermediate" | "expert";
  years: number | null;
  source: "extracted" | "inferred" | "manual";
  confidence: number | null;
  evidence: string | null;
}

export interface Project {
  id: string;
  name: string;
  role: string | null;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  technologies: string[];
}

export interface EmployeeListItem {
  id: string;
  name: string;
  email: string;
  title: string | null;
  location: string | null;
  total_years_exp: number | null;
  availability: string;
  top_skills: string[];
}

export interface EmployeeDetail extends EmployeeListItem {
  summary: string | null;
  current_project: string | null;
  last_project_end_date: string | null;
  skills: Skill[];
  projects: Project[];
  certifications: { id: string; name: string; issuer: string | null; year: number | null }[];
}

export interface SearchResult {
  employee_id: string;
  name: string;
  title: string | null;
  location: string | null;
  availability: string;
  total_years_exp: number | null;
  match_score: number;
  reasoning: string;
  strengths: string[];
  gaps: string[];
  top_skills: Skill[];
  similarity: number;
}

export interface SearchResponse {
  query: string;
  parsed_query: {
    semantic_text: string;
    required_skills: string[];
    min_years_per_skill: Record<string, number>;
    location: string | null;
    availability: string[];
    seniority_hint: string | null;
  };
  results: SearchResult[];
  total_candidates_retrieved: number;
}

export interface ReviewQueueItem {
  upload_id: string;
  employee_id: string | null;
  candidate_name: string;
  source: string;
  status: string;
  created_at: string;
  skill_count: number;
  inferred_count: number;
}

export interface ReviewDetail {
  upload_id: string;
  employee_id: string | null;
  source: string;
  status: string;
  created_at: string;
  raw_text_preview: string | null;
  current_profile: EmployeeDetail | null;
  extracted_payload: Record<string, unknown> | null;
  inferred_skills: Skill[];
  error: string | null;
}

export interface UploadResponse {
  upload_id: string;
  employee_id: string | null;
  status: string;
  message: string;
}

// ─── Employees ────────────────────────────────────────────────────────────────

export function useEmployees(q?: string) {
  return useQuery<EmployeeListItem[]>({
    queryKey: ["employees", q],
    queryFn: () => api<EmployeeListItem[]>(`/employees${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  });
}

export function useEmployee(id: string | null) {
  return useQuery<EmployeeDetail>({
    queryKey: ["employee", id],
    queryFn: () => api<EmployeeDetail>(`/employees/${id}`),
    enabled: !!id,
  });
}

export function useMyEmployee() {
  return useQuery<EmployeeDetail>({
    queryKey: ["employee-me"],
    queryFn: () => api<EmployeeDetail>("/employees/me"),
  });
}

// ─── Search ───────────────────────────────────────────────────────────────────

export function useSearch() {
  return useMutation<SearchResponse, Error, { query: string; limit?: number }>({
    mutationFn: (payload) =>
      api<SearchResponse>("/search", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  });
}

// ─── Review Queue ─────────────────────────────────────────────────────────────

export function useReviewQueue() {
  return useQuery<ReviewQueueItem[]>({
    queryKey: ["review-queue"],
    queryFn: () => api<ReviewQueueItem[]>("/review-queue"),
    refetchInterval: 15_000, // poll every 15s so new uploads appear
  });
}

export function useReviewDetail(id: string | null) {
  return useQuery<ReviewDetail>({
    queryKey: ["review-detail", id],
    queryFn: () => api<ReviewDetail>(`/review-queue/${id}`),
    enabled: !!id,
  });
}

export function useApprove() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, string>({
    mutationFn: (uploadId) =>
      api(`/review-queue/${uploadId}/approve`, { method: "POST", body: JSON.stringify({}) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["review-queue"] });
      qc.invalidateQueries({ queryKey: ["employees"] });
    },
  });
}

export function useReject() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, { uploadId: string; reason?: string }>({
    mutationFn: ({ uploadId, reason }) =>
      api(`/review-queue/${uploadId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["review-queue"] }),
  });
}

// ─── Upload ───────────────────────────────────────────────────────────────────

export function useUploadResume() {
  return useMutation<UploadResponse, Error, FormData>({
    mutationFn: (formData) =>
      api<UploadResponse>("/uploads/resume", { method: "POST", body: formData }),
  });
}

export function useUploadText() {
  return useMutation<UploadResponse, Error, { text: string }>({
    mutationFn: (payload) =>
      api<UploadResponse>("/uploads/text", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  });
}

// ─── Skills catalog ───────────────────────────────────────────────────────────

export function useSkillsCatalog() {
  return useQuery<{ id: string; name: string; category: string }[]>({
    queryKey: ["skills-catalog"],
    queryFn: () => api("/skills/catalog"),
    staleTime: Infinity,
  });
}

// ─── Skill gap analysis ───────────────────────────────────────────────────────

export interface SkillGapItem {
  name: string;
  category: string;
  employee_count: number;
  expert_count: number;
  gap_severity: "critical" | "warning" | "healthy";
}

export function useSkillGaps() {
  return useQuery<SkillGapItem[]>({
    queryKey: ["skill-gaps"],
    queryFn: () => api<SkillGapItem[]>("/skills/gaps"),
    staleTime: 60_000,
  });
}
