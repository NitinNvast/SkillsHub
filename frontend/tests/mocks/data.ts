import type {
  EmployeeListItem,
  EmployeeDetail,
  SearchResult,
  SearchResponse,
  ReviewQueueItem,
  ReviewDetail,
  UploadResponse,
  TeamBuilderResponse,
  BulkUploadResponse,
  SkillGapResponse,
  Skill,
  Project,
} from "@/lib/api/hooks";
import type { SessionUser } from "@/lib/auth/session";

export const mockHRUser: SessionUser = {
  id: "hr-1",
  email: "hr@demo.com",
  name: "HR User",
  role: "hr",
};

export const mockEmployeeUser: SessionUser = {
  id: "emp-1",
  email: "emp@demo.com",
  name: "Employee User",
  role: "employee",
};

export const mockSkill: Skill = {
  id: "skill-1",
  skill_id: "react-1",
  name: "React",
  category: "framework",
  proficiency: "expert",
  years: 5,
  source: "extracted",
  confidence: 0.95,
  evidence: "Led React development for 5 years",
};

export const mockInferredSkill: Skill = {
  id: "skill-2",
  skill_id: "js-1",
  name: "JavaScript",
  category: "language",
  proficiency: "expert",
  years: 7,
  source: "inferred",
  confidence: 0.9,
  evidence: null,
};

export const mockGithubSkill: Skill = {
  id: "skill-3",
  skill_id: "ts-1",
  name: "TypeScript",
  category: "language",
  proficiency: "intermediate",
  years: 3,
  source: "github",
  confidence: 0.85,
  evidence: null,
};

export const mockProject: Project = {
  id: "proj-1",
  name: "E-Commerce Platform",
  role: "Tech Lead",
  description: "Led development of large-scale e-commerce platform",
  start_date: "2022-01-01",
  end_date: "2023-06-30",
  technologies: ["React", "Node.js", "PostgreSQL"],
};

export const mockEmployeeListItem: EmployeeListItem = {
  id: "emp-123",
  name: "Jane Smith",
  email: "jane@company.com",
  title: "Senior Software Engineer",
  location: "San Francisco, CA",
  total_years_exp: 7,
  availability: "available",
  top_skills: ["React", "TypeScript", "Node.js"],
};

export const mockPartialEmployee: EmployeeListItem = {
  id: "emp-456",
  name: "Bob Jones",
  email: "bob@company.com",
  title: "Frontend Developer",
  location: "New York, NY",
  total_years_exp: 3,
  availability: "partial",
  top_skills: ["Vue", "CSS"],
};

export const mockAllocatedEmployee: EmployeeListItem = {
  id: "emp-789",
  name: "Carol Chen",
  email: "carol@company.com",
  title: "Backend Engineer",
  location: null,
  total_years_exp: null,
  availability: "allocated",
  top_skills: ["Java", "Spring Boot"],
};

export const mockEmployeeDetail: EmployeeDetail = {
  ...mockEmployeeListItem,
  summary:
    "Senior software engineer with 7 years of experience in full-stack development.",
  current_project: null,
  last_project_end_date: "2023-06-30",
  skills: [mockSkill, mockInferredSkill, mockGithubSkill],
  projects: [mockProject],
  certifications: [
    { id: "cert-1", name: "AWS Solutions Architect", issuer: "Amazon", year: 2022 },
  ],
};

export const mockSearchResult: SearchResult = {
  employee_id: "emp-123",
  name: "Jane Smith",
  title: "Senior Software Engineer",
  location: "San Francisco, CA",
  availability: "available",
  total_years_exp: 7,
  match_score: 92,
  reasoning:
    "Strong React experience matches the requirements. Led multiple web projects.",
  strengths: ["5 years React experience", "TypeScript proficiency"],
  gaps: ["No WebSocket experience"],
  top_skills: [mockSkill],
  similarity: 0.87,
};

export const mockLowScoreResult: SearchResult = {
  ...mockSearchResult,
  employee_id: "emp-456",
  name: "Bob Jones",
  match_score: 55,
  strengths: [],
  gaps: ["Limited React experience"],
};

export const mockSearchResponse: SearchResponse = {
  query: "React developer with TypeScript experience",
  parsed_query: {
    semantic_text: "Looking for a React developer with TypeScript skills",
    required_skills: ["React", "TypeScript"],
    min_years_per_skill: { React: 3 },
    location: null,
    availability: ["available"],
    seniority_hint: "senior",
  },
  results: [mockSearchResult],
  total_candidates_retrieved: 5,
};

export const mockEmptySearchResponse: SearchResponse = {
  query: "quantum computing expert",
  parsed_query: {
    semantic_text: "Quantum computing specialist",
    required_skills: ["Quantum Computing"],
    min_years_per_skill: {},
    location: null,
    availability: [],
    seniority_hint: null,
  },
  results: [],
  total_candidates_retrieved: 0,
};

export const mockReviewQueueItem: ReviewQueueItem = {
  upload_id: "upload-1",
  employee_id: "emp-123",
  candidate_name: "Jane Smith",
  source: "pdf",
  status: "pending_review",
  created_at: new Date().toISOString(),
  skill_count: 8,
  inferred_count: 3,
};

export const mockFailedReviewItem: ReviewQueueItem = {
  upload_id: "upload-2",
  employee_id: null,
  candidate_name: "Unknown Candidate",
  source: "pdf",
  status: "failed",
  created_at: new Date().toISOString(),
  skill_count: 0,
  inferred_count: 0,
};

export const mockReviewDetail: ReviewDetail = {
  upload_id: "upload-1",
  employee_id: "emp-123",
  source: "pdf",
  status: "pending_review",
  created_at: new Date().toISOString(),
  raw_text_preview:
    "Jane Smith - Senior Software Engineer\n5 years of React development...",
  current_profile: mockEmployeeDetail,
  extracted_payload: { name: "Jane Smith", skills: ["React", "TypeScript"] },
  inferred_skills: [mockInferredSkill],
  error: null,
};

export const mockUploadResponse: UploadResponse = {
  upload_id: "upload-abc123",
  employee_id: "emp-123",
  status: "pending_review",
  message: "Resume submitted for review",
};

export const mockTeamBuilderResponse: TeamBuilderResponse = {
  description: "E-Commerce Platform rebuild",
  proposal: {
    team: [
      {
        employee_id: "emp-123",
        name: "Jane Smith",
        title: "Senior Software Engineer",
        role_in_project: "Tech Lead",
        match_score: 92,
        rationale: "Strong React and TypeScript skills",
        top_skills: ["React", "TypeScript"],
      },
    ],
    team_rationale:
      "Well-balanced team with strong frontend and backend coverage",
    gaps: ["No dedicated DevOps engineer"],
    alternatives: [],
  },
  total_candidates_considered: 12,
};

export const mockSkillGapResponse: SkillGapResponse = {
  total_employees: 12,
  items: [
    {
      name: "Kubernetes",
      category: "platform",
      employee_count: 2,
      expert_count: 0,
      intermediate_count: 2,
      gap_severity: "critical",
      coverage_pct: 16.7,
    },
    {
      name: "Terraform",
      category: "tool",
      employee_count: 3,
      expert_count: 1,
      intermediate_count: 2,
      gap_severity: "warning",
      coverage_pct: 25,
    },
    {
      name: "React",
      category: "framework",
      employee_count: 10,
      expert_count: 5,
      intermediate_count: 5,
      gap_severity: "healthy",
      coverage_pct: 83.3,
    },
  ],
};

export const mockBulkUploadResponse: BulkUploadResponse = {
  total: 2,
  queued: 2,
  failed: 0,
  results: [
    {
      filename: "resume1.pdf",
      upload_id: "upload-1",
      employee_id: "emp-1",
      status: "queued",
      error: null,
    },
    {
      filename: "resume2.pdf",
      upload_id: "upload-2",
      employee_id: "emp-2",
      status: "queued",
      error: null,
    },
  ],
};
