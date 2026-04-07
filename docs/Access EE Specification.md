# **Access EE Specification v1.0.0**

## *Access Enterprise Edition — Normative Specification*

***

## Document Control

*   **Name:** Access EE Specification
*   **Version:** 1.0.0
*   **Status:** Final
*   **Publication Date:** April 6, 2026
*   **Scope:** Normative
*   **Applicability:** Microsoft Access systems treated as enterprise‑grade software systems

***

## Table of Contents

1.  Purpose and Scope
2.  Fundamental Principle
3.  Definition of Source Code
4.  Developer Responsibility
5.  Logical Structure of the Source Code
6.  Executable Code
7.  Interface and Presentation
8.  Queries and Data Access Logic
9.  Data Model
10. Data as Part of the Source Code
11. Build Process
12. Recognized Environments
13. DEV/PROD Governance
14. Quality and Functional Validation
15. Static Code Security
16. Traceability and Evidence
17. Version Stamping
18. Version Description
19. Organizational Requirements
20. Alignment with External Standards
21. Closing Provisions

***

## 1. Purpose and Scope

This specification defines the **Access EE (Access Enterprise Edition)** standard, a normative model for the development, maintenance, validation, promotion, and auditing of Microsoft Access‑based systems that must operate under enterprise‑level requirements for software engineering discipline, technical governance, operational predictability, and auditability.

Access EE establishes **technical, organizational, and procedural requirements**, independent of specific tools, with the purpose of eliminating informal practices historically associated with the Access platform and aligning it with modern software engineering standards.

***

## 2. Fundamental Principle

Under Access EE, Microsoft Access binary files—including but not limited to `.accdb` and `.accde`—**DO NOT constitute source code**.

Source code is defined exclusively as the **complete set of versionable textual artifacts** that fully describe the system’s behavior, structure, data model, internal relationships, and essential data, such that the system can be reconstructed **entirely and deterministically** without reliance on any pre‑existing binary state.

These textual artifacts constitute the **single normative source of truth** for the system.

***

## 3. Definition of Source Code

For the purposes of Access EE, *source code* comprises every textual artifact required to fully and unambiguously represent:

*   functional behavior;
*   business logic;
*   user interface and interaction flow;
*   data structures;
*   internal relationships;
*   essential system data.

Source code is not an execution medium. It is the **complete descriptive representation of the system**, not the container used to run it.

***

## 4. Developer Responsibility

It is the responsibility of the developer, or the responsible technical team, to ensure that the source code is complete, coherent, up to date, and available.

No functionality may depend solely on opaque binary state.  
Direct modification of executable artifacts is not recognized as a valid system change and constitutes **non‑compliance with Access EE**.

***

## 5. Logical Structure of the Source Code

The source code shall be organized within a single canonical directory, conventionally named `src`, which fully materializes the system in textual form.

This structure must enable human inspection, automated analysis, historical traceability, and full system reconstruction.

***

## 6. Executable Code

All executable system logic must exist explicitly in textual form. This includes standard modules, class modules, form and report code, utility routines, and integration logic.

No system behavior may rely exclusively on binary‑stored code.

***

## 7. Interface and Presentation

Forms and reports must be represented in complete textual form sufficient to describe layout, properties, data sources, events, and associated code, enabling reconstruction and static behavioral analysis.

***

## 8. Queries and Data Access Logic

All queries must be represented textually, including SQL, parameters, and relevant properties.

Queries shall not exist solely within binary database state.

***

## 9. Data Model

The data model is part of the Access EE source code.

Each table must be fully described textually, including fields, data types, properties, primary keys, and indexes.  
Relationships must be explicitly declared, covering cardinality, referential integrity, and update/delete rules.

Implicit or binary‑only relationships are not acceptable.

***

## 10. Data as Part of the Source Code

Access EE allows and requires, where appropriate, that essential data form part of the source code. This includes domain data, configuration tables, and bootstrap or validation datasets.

Exclusion of data must be deliberate, justified, and documented.

***

## 11. Build Process

The build process transforms textual source code into an executable artifact.  
This process must be deterministic, isolated, and must not depend on any pre‑existing binary state.

A build output is always a **derived, disposable artifact**, never source code.

***

## 12. Recognized Environments

Access EE formally recognizes two environments: Development (DEV) and Production (PROD).

DEV exists for inspection, validation, and adjustment.  
PROD is immutable, non‑editable, and derived exclusively from validated source code.

***

## 13. DEV/PROD Governance

Strict separation between DEV and PROD is mandatory.  
No changes may be performed directly in production.

All modifications must return to the source code and pass validation and build again.

***

## 14. Quality and Functional Validation

System quality must be demonstrated prior to build through structural, functional, and integrity validation of the source code.

Quality is a **verifiable property of the source code**, not a side effect observed at runtime.

***

## 15. Static Code Security

Before build, source code must undergo static security verification performed exclusively on textual artifacts.

This verification must detect semantically unsafe constructs, including but not limited to external command execution, dynamically created objects with significant side effects, calls to sensitive operating system functions, indirect code execution, uncontrolled environmental dependencies, and non‑statistically traceable execution flows.

The analysis must be rule‑based and severity‑classified.  
High‑risk findings must block the build.

***

## 16. Traceability and Evidence

All executable artifacts must be traceable to an identifiable source code state.

Build, validation, and promotion processes must generate verifiable technical evidence.  
Full system reconstruction from source code constitutes the ultimate proof of compliance.

***

## 17. Version Stamping

Access EE mandates the use of **Semantic Versioning**, following the `MAJOR.MINOR.PATCH` format as defined at:

**<https://semver.org>**

Version numbers are properties of the source code and must reflect the actual technical impact of changes.

***

## 18. Version Description

Every source code change must include a structured, semantically explicit description capable of expressing change type, scope, and impact.

Ambiguous or purely narrative descriptions do not satisfy Access EE requirements.

***

## 19. Organizational Requirements

Organizations must define clear responsibilities, change discipline, and team competence to sustain Access EE compliance.

Informal processes or undocumented exceptions invalidate conformity, even if the system functions technically.

***

## 20. Alignment with External Standards

Access EE is structurally aligned with internationally recognized software engineering and governance principles, including those reflected in ISO/IEC 12207, ISO/IEC 25010, COBIT, and regulated change‑control environments.

This alignment is structural and technically demonstrable.

***

## 21. Closing Provisions

A system may be declared **Access EE compliant** only if it can be fully reconstructed from versionable textual artifacts, employs a deterministic build process, strictly separates DEV and PROD, demonstrates pre‑execution quality and security, and maintains complete traceability throughout its lifecycle.

***

## Document Version Control

| Version | Date       | Description                       |
| ------: | ---------- | --------------------------------- |
|   1.0.0 | 2026‑04‑06 | First finalized normative version |

***
