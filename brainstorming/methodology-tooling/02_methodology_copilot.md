# Methodology Copilot (Agent)

## Overview
An interactive AI agent designed to act as a strict, Socratic PhD advisor. It uses a conversational loop to drill down into a student's vague ideas and forge them into a rigorous methodological framework.

## The Problem (The Argument)
When starting out, researchers don't know what they don't know. A static CLI toolkit (like `scholar-design-kit`) assumes the user already knows the name of their paradigm. The Copilot solves the "blank page syndrome" by interviewing the user, extracting their latent intent, and mapping it to the formal academic lexicon defined in Module 00.2.

## Detailed Specs

### Phase 1: The Hook (Intent Extraction)
The agent opens with an open-ended question: *"What is the core problem you are trying to solve in your own words?"*
As the user types their messy, jargon-free idea, the LLM analyzes the text for intent clues:
- Words like "measure, impact, effect, optimize" $\to$ leans Positivist / Quantitative.
- Words like "understand, experience, perceive, navigate" $\to$ leans Constructivist / Qualitative.
- Words like "build, implement, framework, tool" $\to$ leans Design Science.

### Phase 2: The Socratic Grill
The agent enters a verification loop. It presents the user with two competing statements to force a decision.
*Example:* "It sounds like you want to study AI in classrooms. Which of these is closer to your goal? 
A) I want to know *if* AI improves grades by exactly how much.
B) I want to know *how* teachers feel when AI is introduced into their syllabus."

### Phase 3: The Lexicon Translation & Rigor Enforcement
Once the paradigm is locked (e.g. Interpretivist), the Copilot formally defines the terms.
It bans the user from using words like "Bias" or "External Validity" (which belong to Quantitative paradigms) and forces them to use the Lincoln & Guba framework terms: **Credibility, Transferability, Dependability, and Confirmability**.

### Phase 4: Output
The Copilot formats the entire conversation history into a formal `research_protocol.md` and hands it over to the `scholar-design-kit` for final validation and PDF compilation.
