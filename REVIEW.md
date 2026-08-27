# Claude Code Review Configuration

This repository contains the `odmlib v0.2.1` codebase. This file establishes strict operational parameters and constraints for Claude Code sessions analyzing this repository.

## 🚫 Critical Constraints & Execution Rules

1. **NO CODE MODIFICATIONS DURING CODE REVIEWS OR PLAN GENERATION:** 
   * Claude is strictly prohibited from writing, updating, creating, deleting, or altering any files in this repository or the local file system during a code review or plan generation.
   * Do not generate or apply patches, git commits, or file changes during a code review or plan generation.

2. **NO LOCAL RUNTIME CHANGES DURING CODE REVIEWS OR PLAN GENERATION:** 
   * Do not install, update, or remove any packages, dependencies, or environment variables.
   * Do not execute local test suites or compilation scripts unless explicitly requested in a separate, interactive prompt.

3. **PLAN MODE COMPLIANCE DURING CODE REVIEWS OR PLAN GENERATION:** 
   * Always operate under the equivalent of `--mode plan` during code reviews or plan generation. 
   * If a write command or execution action is generated, abort the operation immediately and return to pure analysis during code reivews and plan generation.

## 🎯 Review Scope & Objectives

When conducting a codebase review, focus exclusively on generating high-fidelity documentation, reports, and recommendations covering:

* **Bug Detection:** Identify potential runtime errors, edge-case failures, unhandled exceptions, and logic bugs within the ODM parsing, validation, and generation modules.
* **Structural Improvements:** Provide actionable architectural feedback on the object model, serialization layers, and inheritance patterns.
* **Performance Enhancements:** Highlight inefficiencies in XML/JSON processing, memory overhead, or redundant data loops.
* **Standards Conformance:** Evaluate how cleanly the codebase adheres to standard Python (PEP 8) practices and typical ODM specifications.

## 📊 Output Format Requirement

Present all findings within the interactive terminal interface as standard Markdown blocks, categorized into:
1. Critical Bugs / Edge Cases
2. Structural & Architectural Recommendations
3. Performance Optimizations
