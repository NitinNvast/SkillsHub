"""Seed 12 realistic demo employees with full skill profiles + embeddings.

Run after seed_demo.py (skills catalog must exist):
    docker compose exec backend uv run python -m app.seed.seed_employees

Idempotent: skips employees whose email already exists.
Designed so the four DEMO_QUERIES on the search page all return great results.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import Employee, EmployeeSkill
from app.db.repos.embeddings import render_profile_summary, upsert_employee_embedding
from app.db.repos.employees import upsert_from_extraction
from app.db.session import SessionLocal
from app.schemas.extraction import (
    ExtractedCertification,
    ExtractedProject,
    ExtractedSkill,
    StructuredProfile,
)

# ─── 12 demo profiles ─────────────────────────────────────────────────────────
# Designed to match the four search demo queries:
#  1. "Who can lead a React project that also needs WebSocket experience?"
#  2. "Find a backend dev in Pune with at least 3 years of Java and payment gateway integration."
#  3. "Senior frontend engineers who haven't been on a new project recently."
#  4. "Full-stack developers with cloud (AWS or GCP) and microservices experience."

DEMO_PROFILES = [
    # ── 1. Strong React + WebSocket lead (query 1 top hit) ───────────────────
    {
        "email": "priya.sharma@demo.com",
        "availability": "available",
        "current_project": None,
        "last_project_end_date": date(2024, 3, 1),
        "profile": StructuredProfile(
            name="Priya Sharma",
            email="priya.sharma@demo.com",
            location="Mumbai",
            title="Senior Frontend Engineer",
            total_years_exp=7.0,
            summary=(
                "Senior frontend engineer specializing in real-time React applications. "
                "Led a team of 4 on a live trading dashboard with WebSocket-driven UI updates. "
                "Deeply experienced in TypeScript, state management, and performance optimization."
            ),
            skills=[
                ExtractedSkill(
                    name="React",
                    proficiency="expert",
                    years=6.0,
                    evidence="Led 3 React projects",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="WebSocket",
                    proficiency="expert",
                    years=3.0,
                    evidence="Built trading dashboard with WS feeds",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="TypeScript",
                    proficiency="expert",
                    years=5.0,
                    evidence="All projects in TS",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="Next.js",
                    proficiency="expert",
                    years=3.0,
                    evidence="Next.js App Router, SSR",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="Redux",
                    proficiency="intermediate",
                    years=4.0,
                    evidence="Redux + RTK",
                    confidence=0.93,
                ),
                ExtractedSkill(
                    name="CSS",
                    proficiency="expert",
                    years=7.0,
                    evidence="Tailwind, CSS Modules",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="Node.js",
                    proficiency="intermediate",
                    years=2.0,
                    evidence="BFF APIs",
                    confidence=0.85,
                ),
                ExtractedSkill(
                    name="Jest",
                    proficiency="intermediate",
                    years=4.0,
                    evidence="Unit + integration tests",
                    confidence=0.88,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="RealTrade — Live Trading Dashboard",
                    role="Lead Frontend Engineer",
                    description=(
                        "Built a real-time equities trading dashboard for 50,000 daily active users. "
                        "Architected a WebSocket connection manager in React that consumed 200+ price feeds simultaneously. "
                        "Reduced render lag from 180ms to under 40ms using virtualization and memoization."
                    ),
                    start_date="2022-06",
                    end_date="2024-02",
                    technologies=["React", "WebSocket", "TypeScript", "Redux", "Recharts"],
                ),
                ExtractedProject(
                    name="ShopEasy — E-Commerce Platform Frontend",
                    role="Senior Frontend Engineer",
                    description=(
                        "Rebuilt the frontend of a high-traffic e-commerce platform in Next.js. "
                        "Improved Core Web Vitals scores from 52 to 91. Led a team of 3 frontend engineers."
                    ),
                    start_date="2021-01",
                    end_date="2022-05",
                    technologies=["Next.js", "TypeScript", "Tailwind CSS", "React Query"],
                ),
            ],
            certifications=[
                ExtractedCertification(
                    name="AWS Certified Developer – Associate", issuer="Amazon", year=2023
                ),
            ],
        ),
    },
    # ── 2. Java backend + payment gateways in Pune (query 2 top hit) ─────────
    {
        "email": "rahul.mehta@demo.com",
        "availability": "available",
        "current_project": None,
        "last_project_end_date": date(2024, 4, 1),
        "profile": StructuredProfile(
            name="Rahul Mehta",
            email="rahul.mehta@demo.com",
            location="Pune",
            title="Backend Engineer",
            total_years_exp=5.0,
            summary=(
                "Backend engineer with 5 years in Java and Spring Boot, specializing in payment systems. "
                "Integrated Razorpay, PayU, and NEFT/IMPS banking APIs for multiple fintech clients. "
                "Strong in distributed systems, REST API design, and high-throughput transaction processing."
            ),
            skills=[
                ExtractedSkill(
                    name="Java",
                    proficiency="expert",
                    years=5.0,
                    evidence="5 yrs Java backend dev",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="Spring Boot",
                    proficiency="expert",
                    years=4.0,
                    evidence="All backend projects in Spring",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="Payment Gateways",
                    proficiency="expert",
                    years=4.0,
                    evidence="Razorpay, PayU, NEFT/IMPS",
                    confidence=0.97,
                ),
                ExtractedSkill(
                    name="PostgreSQL",
                    proficiency="expert",
                    years=4.0,
                    evidence="Schema design + query optimization",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="Redis",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Caching + rate limiting",
                    confidence=0.90,
                ),
                ExtractedSkill(
                    name="Docker",
                    proficiency="intermediate",
                    years=2.5,
                    evidence="Dockerized all services",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="Kafka",
                    proficiency="intermediate",
                    years=2.0,
                    evidence="Order event streaming",
                    confidence=0.85,
                ),
                ExtractedSkill(
                    name="REST API",
                    proficiency="expert",
                    years=5.0,
                    evidence="Designed 15+ APIs",
                    confidence=0.95,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="PayFast — Payment Gateway Integration Platform",
                    role="Lead Backend Engineer",
                    description=(
                        "Built a unified payment gateway abstraction layer supporting Razorpay, PayU, and direct NEFT/IMPS banking. "
                        "Processed ₹50Cr+ in monthly transactions with 99.98% uptime. "
                        "Implemented idempotent payment APIs, refund workflows, and webhook retry logic."
                    ),
                    start_date="2022-03",
                    end_date="2024-03",
                    technologies=[
                        "Java",
                        "Spring Boot",
                        "PostgreSQL",
                        "Redis",
                        "Kafka",
                        "Razorpay SDK",
                    ],
                ),
                ExtractedProject(
                    name="BankBridge — Core Banking API Wrapper",
                    role="Backend Engineer",
                    description=(
                        "Developed REST API wrappers for ICICI and HDFC corporate banking APIs. "
                        "Built automated reconciliation engine that reduced manual reconciliation time by 80%."
                    ),
                    start_date="2020-06",
                    end_date="2022-02",
                    technologies=["Java", "Spring Boot", "PostgreSQL", "JUnit"],
                ),
            ],
            certifications=[
                ExtractedCertification(
                    name="Oracle Certified Professional Java SE 11", issuer="Oracle", year=2021
                ),
            ],
        ),
    },
    # ── 3. Senior frontend with stale availability (query 3 hit) ─────────────
    {
        "email": "ananya.krishnan@demo.com",
        "availability": "available",
        "current_project": None,
        "last_project_end_date": date(2023, 11, 1),
        "profile": StructuredProfile(
            name="Ananya Krishnan",
            email="ananya.krishnan@demo.com",
            location="Bangalore",
            title="Senior Frontend Engineer",
            total_years_exp=8.0,
            summary=(
                "Senior frontend engineer with 8 years of experience across React, Vue, and Angular ecosystems. "
                "Worked on design-system-first development, accessibility, and component libraries at scale. "
                "Currently available and looking for a challenging product frontend role."
            ),
            skills=[
                ExtractedSkill(
                    name="React",
                    proficiency="expert",
                    years=6.0,
                    evidence="Primary framework for 5 years",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="Vue.js",
                    proficiency="expert",
                    years=3.0,
                    evidence="Led Vue migration at previous job",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="TypeScript",
                    proficiency="expert",
                    years=5.0,
                    evidence="All recent projects in TS",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="CSS",
                    proficiency="expert",
                    years=8.0,
                    evidence="Design systems, animations",
                    confidence=0.97,
                ),
                ExtractedSkill(
                    name="Storybook",
                    proficiency="expert",
                    years=4.0,
                    evidence="Built and maintained component library",
                    confidence=0.93,
                ),
                ExtractedSkill(
                    name="GraphQL",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Apollo Client experience",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="Jest",
                    proficiency="expert",
                    years=5.0,
                    evidence="TDD practitioner",
                    confidence=0.92,
                ),
                ExtractedSkill(
                    name="Webpack",
                    proficiency="intermediate",
                    years=4.0,
                    evidence="Custom build configurations",
                    confidence=0.85,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="DesignOS — Enterprise Design System",
                    role="Frontend Architect",
                    description=(
                        "Architected and built a shared design system used by 8 product teams (200+ components). "
                        "Established component API standards, accessibility guidelines, and Storybook-based documentation. "
                        "Reduced per-team UI development time by 35%."
                    ),
                    start_date="2021-01",
                    end_date="2023-10",
                    technologies=["React", "TypeScript", "Storybook", "CSS Modules", "Jest"],
                ),
            ],
            certifications=[],
        ),
    },
    # ── 4. Full-stack + AWS + microservices (query 4 top hit) ────────────────
    {
        "email": "vikram.nair@demo.com",
        "availability": "available",
        "current_project": None,
        "last_project_end_date": date(2024, 2, 1),
        "profile": StructuredProfile(
            name="Vikram Nair",
            email="vikram.nair@demo.com",
            location="Hyderabad",
            title="Full-Stack Engineer",
            total_years_exp=6.0,
            summary=(
                "Full-stack engineer with strong cloud-native background. "
                "Designed and migrated a monolithic PHP app to 14 AWS microservices, cutting infra costs by 40%. "
                "Comfortable across the entire stack — React frontends to Kubernetes-orchestrated backends."
            ),
            skills=[
                ExtractedSkill(
                    name="AWS",
                    proficiency="expert",
                    years=4.0,
                    evidence="EC2, Lambda, SQS, ECS, RDS",
                    confidence=0.97,
                ),
                ExtractedSkill(
                    name="Microservices",
                    proficiency="expert",
                    years=3.0,
                    evidence="Led migration to 14 microservices",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="React",
                    proficiency="expert",
                    years=4.0,
                    evidence="React + hooks, Zustand",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="Node.js",
                    proficiency="expert",
                    years=5.0,
                    evidence="Express + NestJS APIs",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="Docker",
                    proficiency="expert",
                    years=3.5,
                    evidence="All services containerized",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="Kubernetes",
                    proficiency="intermediate",
                    years=2.0,
                    evidence="EKS deployments",
                    confidence=0.87,
                ),
                ExtractedSkill(
                    name="TypeScript",
                    proficiency="expert",
                    years=3.5,
                    evidence="Type-first on FE and BE",
                    confidence=0.94,
                ),
                ExtractedSkill(
                    name="PostgreSQL",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Schema design + RDS",
                    confidence=0.88,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="CloudCore — Monolith to Microservices Migration",
                    role="Lead Full-Stack Engineer",
                    description=(
                        "Led the 18-month migration of a 300k LOC PHP monolith to 14 Node.js microservices on AWS ECS. "
                        "Established service mesh, centralized logging with CloudWatch, and CI/CD pipelines in GitHub Actions. "
                        "Reduced deployment frequency from monthly to daily and cut cloud costs by 40%."
                    ),
                    start_date="2022-06",
                    end_date="2024-01",
                    technologies=[
                        "Node.js",
                        "AWS ECS",
                        "Docker",
                        "PostgreSQL",
                        "React",
                        "Kubernetes",
                    ],
                ),
            ],
            certifications=[
                ExtractedCertification(
                    name="AWS Solutions Architect – Associate", issuer="Amazon", year=2022
                ),
            ],
        ),
    },
    # ── 5. Cloud/DevOps specialist, allocated ─────────────────────────────────
    {
        "email": "deepa.iyer@demo.com",
        "availability": "allocated",
        "current_project": "CloudInfra Modernization — BFSI client",
        "last_project_end_date": None,
        "profile": StructuredProfile(
            name="Deepa Iyer",
            email="deepa.iyer@demo.com",
            location="Bangalore",
            title="DevOps / Cloud Engineer",
            total_years_exp=7.0,
            summary=(
                "DevOps engineer focused on multi-cloud infrastructure, Kubernetes platform engineering, and IaC. "
                "Managed AWS and GCP workloads for 200+ engineers across 3 product lines. "
                "Strong Terraform, Helm, and CI/CD pipeline expertise."
            ),
            skills=[
                ExtractedSkill(
                    name="AWS",
                    proficiency="expert",
                    years=5.0,
                    evidence="Production AWS at scale",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="GCP",
                    proficiency="expert",
                    years=3.0,
                    evidence="GKE, Cloud Run, BigQuery",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="Kubernetes",
                    proficiency="expert",
                    years=4.0,
                    evidence="Self-managed + EKS + GKE",
                    confidence=0.97,
                ),
                ExtractedSkill(
                    name="Terraform",
                    proficiency="expert",
                    years=4.0,
                    evidence="Full IaC for 3 environments",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="Docker",
                    proficiency="expert",
                    years=5.0,
                    evidence="All prod workloads containerized",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="Python",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Automation scripts and lambda functions",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="Helm",
                    proficiency="expert",
                    years=3.0,
                    evidence="50+ Helm charts authored",
                    confidence=0.93,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="MultiCloud Platform — GCP + AWS Hybrid",
                    role="Platform Engineer",
                    description=(
                        "Built a unified multi-cloud Kubernetes platform spanning AWS EKS and GCP GKE. "
                        "Standardized observability stack (Prometheus + Grafana + Loki) across all clusters. "
                        "Onboarded 8 engineering teams to the platform within 3 months."
                    ),
                    start_date="2022-01",
                    end_date="2023-12",
                    technologies=["Kubernetes", "Terraform", "GCP", "AWS", "Helm", "Prometheus"],
                ),
            ],
            certifications=[
                ExtractedCertification(
                    name="CKA — Certified Kubernetes Administrator", issuer="CNCF", year=2022
                ),
                ExtractedCertification(
                    name="GCP Professional Cloud Architect", issuer="Google", year=2023
                ),
            ],
        ),
    },
    # ── 6. Senior Java + microservices, partial (query 2 + 4 secondary) ───────
    {
        "email": "arjun.patel@demo.com",
        "availability": "partial",
        "current_project": "Payments Stability — 20% bandwidth",
        "last_project_end_date": None,
        "profile": StructuredProfile(
            name="Arjun Patel",
            email="arjun.patel@demo.com",
            location="Mumbai",
            title="Senior Backend Engineer",
            total_years_exp=8.0,
            summary=(
                "Senior backend engineer with deep Java and distributed systems experience. "
                "Designed event-driven microservices processing 2M+ events/day with Kafka and Spring. "
                "Partial bandwidth available — strongest in backend architecture and payment systems."
            ),
            skills=[
                ExtractedSkill(
                    name="Java",
                    proficiency="expert",
                    years=8.0,
                    evidence="Core language since 2016",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="Spring Boot",
                    proficiency="expert",
                    years=6.0,
                    evidence="All production services in Spring",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="Kafka",
                    proficiency="expert",
                    years=4.0,
                    evidence="Designed event streaming architecture",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="Microservices",
                    proficiency="expert",
                    years=5.0,
                    evidence="Owns 6 production microservices",
                    confidence=0.97,
                ),
                ExtractedSkill(
                    name="Payment Gateways",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Stripe + PayU integrations",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="Redis",
                    proficiency="expert",
                    years=4.0,
                    evidence="Distributed caching + pub-sub",
                    confidence=0.94,
                ),
                ExtractedSkill(
                    name="PostgreSQL",
                    proficiency="expert",
                    years=6.0,
                    evidence="Query tuning, partitioning",
                    confidence=0.96,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="OrderStream — Event-Driven Order Processing",
                    role="Backend Architect",
                    description=(
                        "Redesigned a synchronous order management system into an event-driven architecture using Kafka. "
                        "Processes 2M+ order events per day with guaranteed exactly-once delivery. "
                        "Reduced p99 order processing time from 800ms to 120ms."
                    ),
                    start_date="2021-03",
                    end_date="2024-01",
                    technologies=["Java", "Spring Boot", "Kafka", "PostgreSQL", "Redis", "Docker"],
                ),
            ],
            certifications=[
                ExtractedCertification(
                    name="Spring Professional Certification", issuer="VMware", year=2020
                ),
            ],
        ),
    },
    # ── 7. React + WebSocket (query 1 secondary hit) ──────────────────────────
    {
        "email": "sneha.gupta@demo.com",
        "availability": "available",
        "current_project": None,
        "last_project_end_date": date(2024, 4, 15),
        "profile": StructuredProfile(
            name="Sneha Gupta",
            email="sneha.gupta@demo.com",
            location="Delhi",
            title="Frontend Developer",
            total_years_exp=4.0,
            summary=(
                "Frontend developer with 4 years in React and real-time web applications. "
                "Built a production WebSocket-based collaboration tool used by 5,000 users. "
                "Strong in UI component architecture, TypeScript, and accessible UI development."
            ),
            skills=[
                ExtractedSkill(
                    name="React",
                    proficiency="intermediate",
                    years=3.5,
                    evidence="React primary framework",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="WebSocket",
                    proficiency="intermediate",
                    years=2.0,
                    evidence="Real-time chat + live updates",
                    confidence=0.90,
                ),
                ExtractedSkill(
                    name="TypeScript",
                    proficiency="intermediate",
                    years=2.5,
                    evidence="Typed React components",
                    confidence=0.90,
                ),
                ExtractedSkill(
                    name="Redux",
                    proficiency="intermediate",
                    years=2.0,
                    evidence="Redux Toolkit",
                    confidence=0.85,
                ),
                ExtractedSkill(
                    name="CSS",
                    proficiency="intermediate",
                    years=4.0,
                    evidence="Tailwind CSS",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="Node.js",
                    proficiency="novice",
                    years=1.0,
                    evidence="Simple Express APIs",
                    confidence=0.72,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="CollabSpace — Real-Time Collaboration Tool",
                    role="Frontend Developer",
                    description=(
                        "Built a Google Docs-style collaborative editing tool with real-time cursor presence and live document updates via WebSocket. "
                        "Implemented optimistic UI updates and conflict resolution on the client side."
                    ),
                    start_date="2022-09",
                    end_date="2024-03",
                    technologies=[
                        "React",
                        "WebSocket",
                        "TypeScript",
                        "Redux Toolkit",
                        "Tailwind CSS",
                    ],
                ),
            ],
            certifications=[],
        ),
    },
    # ── 8. Full-stack + GCP + microservices (query 4 secondary hit) ───────────
    {
        "email": "karthik.ramesh@demo.com",
        "availability": "available",
        "current_project": None,
        "last_project_end_date": date(2024, 3, 15),
        "profile": StructuredProfile(
            name="Karthik Ramesh",
            email="karthik.ramesh@demo.com",
            location="Bangalore",
            title="Full-Stack Engineer",
            total_years_exp=7.0,
            summary=(
                "Full-stack engineer with 7 years of experience building SaaS products on GCP. "
                "Designed microservices-first backends in Node.js and React frontends for B2B fintech. "
                "Enthusiastic about GraphQL, serverless, and developer experience tooling."
            ),
            skills=[
                ExtractedSkill(
                    name="Node.js",
                    proficiency="expert",
                    years=6.0,
                    evidence="Primary backend language",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="React",
                    proficiency="expert",
                    years=5.0,
                    evidence="Component libraries, performance",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="GCP",
                    proficiency="expert",
                    years=4.0,
                    evidence="Cloud Run, Firestore, BigQuery, GKE",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="Microservices",
                    proficiency="expert",
                    years=4.0,
                    evidence="Designed 12-service fintech platform",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="GraphQL",
                    proficiency="expert",
                    years=3.5,
                    evidence="Apollo Server + Client",
                    confidence=0.93,
                ),
                ExtractedSkill(
                    name="TypeScript",
                    proficiency="expert",
                    years=4.0,
                    evidence="Strict TypeScript everywhere",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="Docker",
                    proficiency="expert",
                    years=4.0,
                    evidence="Containerized all services",
                    confidence=0.94,
                ),
                ExtractedSkill(
                    name="PostgreSQL",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Cloud SQL schemas",
                    confidence=0.87,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="FintechOS — B2B SaaS Lending Platform",
                    role="Lead Full-Stack Engineer",
                    description=(
                        "Built a B2B lending SaaS on GCP with 12 microservices handling loan origination, credit scoring, and disbursement. "
                        "Served 40 enterprise clients processing ₹200Cr in annual loan volume. "
                        "Architected GraphQL federation layer unifying 5 downstream microservice APIs."
                    ),
                    start_date="2021-01",
                    end_date="2024-02",
                    technologies=[
                        "Node.js",
                        "React",
                        "GCP Cloud Run",
                        "GraphQL",
                        "TypeScript",
                        "PostgreSQL",
                    ],
                ),
            ],
            certifications=[
                ExtractedCertification(
                    name="GCP Associate Cloud Engineer", issuer="Google", year=2022
                ),
            ],
        ),
    },
    # ── 9. Data engineer, allocated ───────────────────────────────────────────
    {
        "email": "meera.banerjee@demo.com",
        "availability": "allocated",
        "current_project": "Data Platform Modernization — Retail client",
        "last_project_end_date": None,
        "profile": StructuredProfile(
            name="Meera Banerjee",
            email="meera.banerjee@demo.com",
            location="Pune",
            title="Data Engineer",
            total_years_exp=6.0,
            summary=(
                "Data engineer with 6 years building large-scale data pipelines and analytics platforms. "
                "Expert in Apache Spark, Airflow, and cloud data warehousing on GCP and AWS. "
                "Built data lakehouse architectures processing 5TB+ of daily event data."
            ),
            skills=[
                ExtractedSkill(
                    name="Python",
                    proficiency="expert",
                    years=6.0,
                    evidence="Primary scripting and pipeline language",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="Apache Spark",
                    proficiency="expert",
                    years=4.0,
                    evidence="PySpark ETL jobs in production",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="SQL",
                    proficiency="expert",
                    years=6.0,
                    evidence="Complex analytical queries",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="Apache Airflow",
                    proficiency="expert",
                    years=3.0,
                    evidence="200+ DAGs managed",
                    confidence=0.94,
                ),
                ExtractedSkill(
                    name="GCP",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="BigQuery, Dataflow, GCS",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="AWS",
                    proficiency="intermediate",
                    years=2.0,
                    evidence="S3, Glue, Redshift",
                    confidence=0.82,
                ),
                ExtractedSkill(
                    name="dbt",
                    proficiency="intermediate",
                    years=2.0,
                    evidence="Data transformation layer",
                    confidence=0.86,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="DataLake Pro — Enterprise Data Lakehouse",
                    role="Lead Data Engineer",
                    description=(
                        "Built a multi-zone data lakehouse on GCP ingesting 5TB+ of daily retail transaction data. "
                        "Replaced 3 legacy ETL tools with Airflow + Spark, cutting pipeline failure rates from 12% to 0.4%. "
                        "Enabled self-serve analytics for 80 business analysts via BigQuery."
                    ),
                    start_date="2021-06",
                    end_date="2024-04",
                    technologies=[
                        "Python",
                        "Apache Spark",
                        "Airflow",
                        "GCP BigQuery",
                        "dbt",
                        "SQL",
                    ],
                ),
            ],
            certifications=[
                ExtractedCertification(
                    name="GCP Professional Data Engineer", issuer="Google", year=2022
                ),
            ],
        ),
    },
    # ── 10. Mobile developer, partial ─────────────────────────────────────────
    {
        "email": "rohan.desai@demo.com",
        "availability": "partial",
        "current_project": "React Native App — E-commerce client (50% time)",
        "last_project_end_date": None,
        "profile": StructuredProfile(
            name="Rohan Desai",
            email="rohan.desai@demo.com",
            location="Mumbai",
            title="Mobile Developer",
            total_years_exp=5.0,
            summary=(
                "Mobile-first engineer with expertise in React Native and native iOS development. "
                "Published 4 apps with 100K+ downloads each on the App Store and Play Store. "
                "Available for 50% on a new project alongside current maintenance work."
            ),
            skills=[
                ExtractedSkill(
                    name="React Native",
                    proficiency="expert",
                    years=4.0,
                    evidence="4 production apps shipped",
                    confidence=0.97,
                ),
                ExtractedSkill(
                    name="TypeScript",
                    proficiency="expert",
                    years=4.0,
                    evidence="TypeScript-first mobile dev",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="iOS",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Swift, native modules",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="React",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Web companion apps",
                    confidence=0.87,
                ),
                ExtractedSkill(
                    name="Node.js",
                    proficiency="novice",
                    years=1.5,
                    evidence="Mobile BFF APIs",
                    confidence=0.75,
                ),
                ExtractedSkill(
                    name="Redux",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="State management in all apps",
                    confidence=0.88,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="PayGo — Fintech Payment Mobile App",
                    role="Lead Mobile Developer",
                    description=(
                        "Built a UPI + wallet payment app in React Native with biometric authentication and NFC tap-to-pay. "
                        "Reached 500K downloads in 6 months with 4.7 App Store rating. "
                        "Integrated Razorpay and Google Pay APIs for seamless payment flows."
                    ),
                    start_date="2022-01",
                    end_date="2023-11",
                    technologies=[
                        "React Native",
                        "TypeScript",
                        "iOS",
                        "Razorpay",
                        "Redux",
                        "Firebase",
                    ],
                ),
            ],
            certifications=[],
        ),
    },
    # ── 11. Senior frontend, not recently on project (query 3 strong hit) ─────
    {
        "email": "aditi.singh@demo.com",
        "availability": "available",
        "current_project": None,
        "last_project_end_date": date(2023, 8, 1),
        "profile": StructuredProfile(
            name="Aditi Singh",
            email="aditi.singh@demo.com",
            location="Bangalore",
            title="Senior Frontend Engineer",
            total_years_exp=9.0,
            summary=(
                "Senior frontend engineer with 9 years across React, Angular, and Vue ecosystems. "
                "Strongest in building high-performance UIs, micro-frontend architectures, and large-scale component libraries. "
                "Free since August 2023 and actively seeking a new challenge."
            ),
            skills=[
                ExtractedSkill(
                    name="React",
                    proficiency="expert",
                    years=8.0,
                    evidence="8 years React, inc. React 18",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="Angular",
                    proficiency="expert",
                    years=4.0,
                    evidence="Led Angular 12 → 16 upgrade",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="Vue.js",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Vue 3 + Composition API",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="TypeScript",
                    proficiency="expert",
                    years=6.0,
                    evidence="All major projects in TS",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="Webpack",
                    proficiency="expert",
                    years=5.0,
                    evidence="Custom module federation config",
                    confidence=0.93,
                ),
                ExtractedSkill(
                    name="CSS",
                    proficiency="expert",
                    years=9.0,
                    evidence="CSS-in-JS, Tailwind, BEM",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="Jest",
                    proficiency="expert",
                    years=6.0,
                    evidence="100% unit test coverage on component libs",
                    confidence=0.94,
                ),
                ExtractedSkill(
                    name="GraphQL",
                    proficiency="intermediate",
                    years=2.5,
                    evidence="Client-side Apollo queries",
                    confidence=0.84,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="MicroFE — Enterprise Micro-Frontend Platform",
                    role="Principal Frontend Engineer",
                    description=(
                        "Designed a module-federation-based micro-frontend platform used by 6 independent product teams. "
                        "Reduced page load time by 55% through code splitting and lazy loading. "
                        "Standardized design token adoption across 12 React and Angular apps."
                    ),
                    start_date="2020-03",
                    end_date="2023-07",
                    technologies=[
                        "React",
                        "Angular",
                        "Webpack Module Federation",
                        "TypeScript",
                        "Jest",
                    ],
                ),
            ],
            certifications=[],
        ),
    },
    # ── 12. Java + payment specialist, Pune (query 2 alternative hit) ─────────
    {
        "email": "sanjay.kumar@demo.com",
        "availability": "available",
        "current_project": None,
        "last_project_end_date": date(2024, 5, 1),
        "profile": StructuredProfile(
            name="Sanjay Kumar",
            email="sanjay.kumar@demo.com",
            location="Pune",
            title="Backend Developer",
            total_years_exp=7.0,
            summary=(
                "Backend developer in Pune specializing in fintech and payment systems using Java. "
                "6 years of hands-on experience with Razorpay, Stripe, PayTM, and UPI payment flows. "
                "Built payment platforms handling ₹100Cr+ monthly volume for enterprise clients."
            ),
            skills=[
                ExtractedSkill(
                    name="Java",
                    proficiency="expert",
                    years=7.0,
                    evidence="Java since 2017",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="Spring Boot",
                    proficiency="expert",
                    years=6.0,
                    evidence="Spring Boot microservices throughout career",
                    confidence=0.98,
                ),
                ExtractedSkill(
                    name="Payment Gateways",
                    proficiency="expert",
                    years=5.0,
                    evidence="Razorpay, Stripe, PayTM, UPI",
                    confidence=0.99,
                ),
                ExtractedSkill(
                    name="PostgreSQL",
                    proficiency="expert",
                    years=5.0,
                    evidence="Ledger and transaction DB design",
                    confidence=0.95,
                ),
                ExtractedSkill(
                    name="Microservices",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="3-service decomposition",
                    confidence=0.87,
                ),
                ExtractedSkill(
                    name="Redis",
                    proficiency="intermediate",
                    years=3.0,
                    evidence="Idempotency key cache",
                    confidence=0.88,
                ),
                ExtractedSkill(
                    name="REST API",
                    proficiency="expert",
                    years=7.0,
                    evidence="PCI-DSS compliant APIs",
                    confidence=0.96,
                ),
                ExtractedSkill(
                    name="Docker",
                    proficiency="intermediate",
                    years=2.0,
                    evidence="Containerized deployments",
                    confidence=0.82,
                ),
            ],
            projects=[
                ExtractedProject(
                    name="PayHub — Enterprise Payment Orchestration",
                    role="Senior Backend Developer",
                    description=(
                        "Built a payment orchestration platform routing transactions across Razorpay, Stripe, and PayTM based on success rate and cost. "
                        "Processed ₹100Cr+ monthly with 99.97% uptime and full PCI-DSS compliance. "
                        "Implemented smart retry logic that improved payment success rates from 87% to 96%."
                    ),
                    start_date="2021-06",
                    end_date="2024-04",
                    technologies=[
                        "Java",
                        "Spring Boot",
                        "Razorpay",
                        "Stripe",
                        "PostgreSQL",
                        "Redis",
                        "Docker",
                    ],
                ),
                ExtractedProject(
                    name="UPI Gateway — Direct UPI Integration",
                    role="Backend Developer",
                    description=(
                        "Developed a direct UPI gateway integration for a leading NBFC, bypassing third-party aggregator fees. "
                        "Saved ₹80L annually in transaction fees and reduced settlement time from T+2 to T+0."
                    ),
                    start_date="2019-01",
                    end_date="2021-05",
                    technologies=["Java", "Spring Boot", "UPI", "PostgreSQL", "REST API"],
                ),
            ],
            certifications=[
                ExtractedCertification(
                    name="Oracle Certified Professional Java SE 17", issuer="Oracle", year=2022
                ),
            ],
        ),
    },
]


# ─── Inferred skills to add to select profiles ────────────────────────────────
# Key = email, value = list of inferred skill dicts
INFERRED_SKILLS: dict[str, list[dict]] = {
    "priya.sharma@demo.com": [
        {
            "name": "React Query",
            "proficiency": "intermediate",
            "years": 2.0,
            "confidence": 0.80,
            "reasoning": "Used React Query in Next.js projects",
        },
        {
            "name": "Vite",
            "proficiency": "intermediate",
            "years": 1.5,
            "confidence": 0.75,
            "reasoning": "Modern bundler used in recent projects",
        },
    ],
    "rahul.mehta@demo.com": [
        {
            "name": "Maven",
            "proficiency": "intermediate",
            "years": 5.0,
            "confidence": 0.85,
            "reasoning": "Standard Java build tool used with Spring Boot",
        },
        {
            "name": "JUnit",
            "proficiency": "intermediate",
            "years": 4.0,
            "confidence": 0.82,
            "reasoning": "Java testing standard",
        },
        {
            "name": "Hibernate",
            "proficiency": "intermediate",
            "years": 3.5,
            "confidence": 0.80,
            "reasoning": "ORM used in Spring Boot projects",
        },
    ],
    "vikram.nair@demo.com": [
        {
            "name": "AWS Lambda",
            "proficiency": "intermediate",
            "years": 2.0,
            "confidence": 0.82,
            "reasoning": "Serverless functions used in microservices",
        },
        {
            "name": "AWS SQS",
            "proficiency": "intermediate",
            "years": 2.0,
            "confidence": 0.80,
            "reasoning": "Message queuing between microservices",
        },
        {
            "name": "NestJS",
            "proficiency": "intermediate",
            "years": 2.0,
            "confidence": 0.78,
            "reasoning": "TypeScript-first Node.js framework used in services",
        },
    ],
    "karthik.ramesh@demo.com": [
        {
            "name": "Cloud Run",
            "proficiency": "expert",
            "years": 3.0,
            "confidence": 0.88,
            "reasoning": "GCP serverless containers — primary deployment target",
        },
        {
            "name": "Prisma",
            "proficiency": "intermediate",
            "years": 2.0,
            "confidence": 0.76,
            "reasoning": "ORM commonly used with Node.js + PostgreSQL",
        },
    ],
    "aditi.singh@demo.com": [
        {
            "name": "Module Federation",
            "proficiency": "expert",
            "years": 3.0,
            "confidence": 0.90,
            "reasoning": "Core technology of MicroFE platform project",
        },
        {
            "name": "Playwright",
            "proficiency": "intermediate",
            "years": 2.0,
            "confidence": 0.77,
            "reasoning": "E2E testing for frontend component library",
        },
    ],
}


# ─── Seeder ───────────────────────────────────────────────────────────────────


async def seed_employees() -> None:
    from app.ai.embeddings import embed_single

    async with SessionLocal() as session:
        print("Seeding demo employees…")

        for entry in DEMO_PROFILES:
            email: str = entry["email"]  # type: ignore[assignment]
            profile: StructuredProfile = entry["profile"]  # type: ignore[assignment]

            # Check if already seeded
            existing = await session.execute(select(Employee).where(Employee.email == email))
            emp = existing.scalar_one_or_none()

            if emp is None:
                emp = Employee(
                    id=uuid.uuid4(),
                    email=email,
                    name=profile.name,
                    location=profile.location,
                    title=profile.title,
                    availability=entry["availability"],
                    current_project=entry["current_project"],
                    last_project_end_date=entry["last_project_end_date"],
                )
                session.add(emp)
                await session.flush()
                print(f"  + created employee: {profile.name}")
            else:
                # Update mutable fields in case data changed
                emp.availability = entry["availability"]  # type: ignore[assignment]
                emp.current_project = entry["current_project"]  # type: ignore[assignment]
                emp.last_project_end_date = entry["last_project_end_date"]  # type: ignore[assignment]
                await session.flush()
                print(f"  ~ updated employee: {profile.name}")

            # Upsert skills, projects, certifications
            inferred = INFERRED_SKILLS.get(email, [])
            await upsert_from_extraction(session, emp.id, profile, inferred_skills=inferred)
            await session.flush()  # make skills visible to the reload query below

            # Save ID before expiring (accessing .id after expire triggers sync lazy-load)
            emp_id = emp.id
            session.expire(emp)

            # Reload with relationships for embedding
            result = await session.execute(
                select(Employee)
                .where(Employee.id == emp_id)
                .options(
                    selectinload(Employee.skills).joinedload(EmployeeSkill.skill),
                    selectinload(Employee.projects),
                    selectinload(Employee.certifications),
                )
            )
            emp_full = result.scalar_one()

            # Generate and store embedding (rate-limit: Voyage AI free tier = 3 RPM)
            from app.db.models import EmployeeEmbedding

            existing_emb = await session.execute(
                select(EmployeeEmbedding).where(EmployeeEmbedding.employee_id == emp_id)
            )
            if existing_emb.scalar_one_or_none() is not None:
                print(f"    ~ embedding already exists: {profile.name}, skipping")
            else:
                summary_text = render_profile_summary(emp_full)
                vector = await embed_single(summary_text)
                await upsert_employee_embedding(session, emp_id, vector, summary_text)
                print(f"    ✓ embedded: {profile.name} ({len(emp_full.skills)} skills)")
                await asyncio.sleep(21)  # stay within 3 RPM free-tier limit

        print(f"\nSeeded {len(DEMO_PROFILES)} employees.")

        # Link the demo employee user (emp@demo.com) to Priya Sharma's record
        # so the /employees/me endpoint works for the demo employee login
        from app.db.models import User

        user_res = await session.execute(select(User).where(User.email == "emp@demo.com"))
        demo_user = user_res.scalar_one_or_none()
        if demo_user:
            emp_res = await session.execute(
                select(Employee).where(Employee.email == "priya.sharma@demo.com")
            )
            priya = emp_res.scalar_one_or_none()
            if priya and priya.user_id is None:
                priya.user_id = demo_user.id
                await session.commit()
                print("  ✓ linked emp@demo.com → Priya Sharma (employee profile)")
            else:
                print("  ~ emp@demo.com link already set or Priya not found")
        else:
            print("  ! emp@demo.com user not found — run seed_demo.py first")

        print("\nDone.")


if __name__ == "__main__":
    asyncio.run(seed_employees())
