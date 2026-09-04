# Vantage Documentation Index

Welcome to the technical and operational documentation for **Vantage**—an AI-powered road safety intelligence and traffic risk analysis platform.

This documentation suite provides a complete, authoritative reference for developers, transport safety analysts, and system evaluators. All documents describe the current implementation of the codebase.

---

## Documentation Roadmap

| Document | Description | Target Audience |
| --- | --- | --- |
| [**Architecture**](architecture.md) | High-level system architecture, component interaction, service boundaries, and data flow pipelines. | Architects, Engineers |
| [**System Overview**](system-overview.md) | Product vision, core analytical concepts, real-time telemetry vs. empirical evidence vs. AI synthesis. | Developers, Evaluators |
| [**Frontend Architecture**](frontend.md) | TanStack Start, React 19, routing hierarchy, UI components, state management, and export engines. | Frontend Developers |
| [**Backend Architecture**](backend.md) | FastAPI application structure, lifespan management, service layers, error handling, and provider integrations. | Backend Developers |
| [**API Reference**](api.md) | Exhaustive REST API specification covering schemas, request/response models, endpoints, and error responses. | API Consumers, Integrators |
| [**Machine Learning Models**](models.md) | Detailed methodology for Severity Prediction, Hotspot Explorer, and Road Risk Analysis. | Data Scientists, ML Engineers |
| [**Journey Safety Analysis**](journey-safety.md) | End-to-end 11-step journey analysis pipeline, deterministic risk guardrails, and corridor matching. | Core Platform Engineers |
| [**Gemini & AI Synthesis**](ai-gemini.md) | Grounded LLM synthesis architecture, prompt engineering constraints, multi-provider routing, and fallbacks. | AI/LLM Engineers |
| [**Design System**](design-system.md) | Visual tokens, color palettes, status badge indicators, UI component patterns, and typography. | Designers, UI Developers |
| [**Setup & Development**](setup.md) | Local development environment setup, prerequisites, dependency installation, and test suite execution. | All Contributors |
| [**Deployment Guide**](deployment.md) | Deployment readiness, resource sizing considerations, large model artifact constraints, and cloud strategy. | DevOps, SREs |
| [**System Limitations**](limitations.md) | Comprehensive catalog of scientific, geographic, algorithmic, and operational system constraints. | Evaluators, Stakeholders |

---

## Public Product Modules vs. Internal Implementation

Vantage standardizes its public interfaces around human-readable domain concepts while preserving clear internal engineering mappings:

| Public Module Name | Primary Function | Internal Implementation Reference | Underlying Model / Engine |
| --- | --- | --- | --- |
| **Severity Prediction** | Collision injury severity classification | `Student A` | 138-feature Random Forest Classifier |
| **Hotspot Explorer** | Spatial accident cluster density mapping | `Student B` | DBSCAN Density-Based Spatial Clustering |
| **Road Risk Analysis** | Structural network topological risk evaluation | `Student C` | Graph Neural Network (GNN) on Road Graphs |
| **AI Infrastructure Report** | Multi-model transport planning synthesis | `LLM Report Service` | Grounded Gemini Synthesis with Multi-Model Grounding |
| **Journey Safety Analysis** | Route corridor multi-source safety assessment | `Journey Service` | Multi-provider Pipeline + Deterministic Assessment + Gemini |
| **History** | Local analysis record persistence | `History API / LocalStorage` | Client-Side Structured Storage |

---

## Getting Started

- To set up the platform locally, follow the [**Setup Guide**](setup.md).
- To explore the architectural data flow, read the [**Architecture Overview**](architecture.md).
- To inspect endpoint schemas, review the [**API Reference**](api.md).
