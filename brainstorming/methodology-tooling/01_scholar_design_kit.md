# Scholar Design Kit

## Overview
A rigid, offline-first CLI toolkit designed to force early-stage researchers to thoroughly plan, audit, and mathematically validate their research *before* writing a single line of code or running an experiment.

## The Problem (The Argument)
Novice researchers often jump straight into data collection without pre-registering their hypotheses, resulting in HARKing (Hypothesizing After Results are Known) and p-hacking. Furthermore, they often struggle with estimating the required sample size, leading to underpowered studies (Positivist) or superficial interviews without saturation (Qualitative).

## Detailed Specs

### 1. `scholar-design preregister`
**Function:** An interactive terminal checklist wizard that enforces strict adherence to global reporting guidelines based on the chosen paradigm.
* If **Systematic Review**, it enforces the **PRISMA** checklist.
* If **Randomized Trial**, it enforces **CONSORT**.
* If **Observational Study**, it enforces **STROBE**.
**Output:** A locked, timestamped `preregistration.md` or `.json` file that is formatted perfectly for submission to the Open Science Framework (OSF).

### 2. `scholar-design power`
**Function:** A statistical calculator module.
* **For Quantitative (Positivist):** Uses `scipy.stats` and `statsmodels` to prompt the user for their desired Alpha ($\alpha = 0.05$), Power ($1-\beta = 0.80$), and Expected Effect Size (Cohen's $d$). It then calculates the exact $N$ (Sample Size) required.
* **For Qualitative (Interpretivist):** Instead of math, it guides the user through a "Data Saturation Rubric" (e.g., minimum 12-15 interviews for thematic saturation, based on Guest et al., 2006).

### 3. `scholar-design mismatch-check`
**Function:** A static analyzer for research plans. 
* Uses an LLM or rigid rules to scan the user's `preregistration.md`.
* **Example Flag:** "Warning: You declared an *Interpretivist Phenomenological* paradigm, but your research question asks to 'measure the statistical impact'. You must change your question to explore 'experiences' or change your paradigm to 'Positivist'."

## Why this works
It takes abstract concepts from Module 00.2 and turns them into enforced software checks, treating research design with the same rigor as compiling code.
