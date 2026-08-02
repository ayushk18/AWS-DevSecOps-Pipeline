# AWS-DevSecOps-Pipeline

A production-grade DevSecOps CI/CD pipeline demonstrating secure software development lifecycle practices for a Python Flask application.

## 🎯 Project Overview

This project implements automated security scanning, containerization, and cloud deployment with real-time monitoring and incident detection.

**Status:** In Development (Phase 0 of 11)

## 🏗️ Architecture

- **Application:** Python Flask REST API with PostgreSQL
- **CI/CD:** GitHub Actions with security gates
- **Security:** SAST (Semgrep), secrets scanning (GitLeaks), container scanning (Trivy), DAST (OWASP ZAP)
- **Deployment:** Docker + Docker Compose on AWS EC2 (free tier)
- **Orchestration:** Kubernetes (Minikube for local, manifests in repo for learning)
- **Monitoring:** Prometheus + Grafana
- **Secrets:** HashiCorp Vault (optional advanced phase)

## 📋 Phases

- [ ] Phase 0: Project Planning & Architecture
- [ ] Phase 1: Development Environment Setup
- [ ] Phase 2: Vulnerable Flask Application
- [ ] Phase 3: Containerization
- [ ] Phase 4: CI/CD Pipeline (GitHub Actions)
- [ ] Phase 5: Security Integration
- [ ] Phase 6: AWS Deployment
- [ ] Phase 7: Kubernetes (Local Demo)
- [ ] Phase 8: Secrets Management (Vault)
- [ ] Phase 9: Monitoring (Prometheus/Grafana)
- [ ] Phase 10: Security Hardening
- [ ] Phase 11: Documentation & Interview Prep

## 🚀 Quick Start

(To be filled in Phase 1)

## 📚 Documentation

- Architecture decisions: `/docs`
- Security policies: `/security`
- Kubernetes manifests: `/k8s`
- Deployment guides: `/docs`

## 📝 License

MIT (TBD)