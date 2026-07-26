# PAYNOVA - Smart Banking with AI Agents

PAYNOVA is a university graduation project that explores how AI agents can provide a conversational interface for digital banking operations.

## What is this project?

PAYNOVA was designed to replace repetitive banking workflows and traditional interfaces with a more natural chat experience.

Instead of navigating through several screens, users can describe what they want in Arabic or English. The AI system then identifies the request and routes it to the appropriate banking workflow.

> PAYNOVA is an academic prototype and is not intended for real financial use.

## How does it work?

The system uses locally hosted language models to provide greater control over customer data and privacy.

Each request is classified into one of two processing paths:

| Request type | Example | Processing path |
|---|---|---|
| Informational | “What currencies does the bank support?” | Retrieves relevant bank documents and generates a grounded answer using RAG |
| Action | “Exchange 100 USD to EUR” | Selects a banking function, extracts the provided arguments, collects missing information, and prepares the action for confirmation |

The system separates these paths because answering a question and preparing a banking operation require different validation and safety controls.
## Demo

This silent demonstration shows the AI agent handling three banking requests:

1. Exchanging between currencies
2. Applying for a loan
3. Emptying a saving jar


https://github.com/user-attachments/assets/b1e43166-23ec-4344-b428-def4af8d3e50


## Request Flows

### Informational requests

Informational requests are routed to the retrieval pipeline. The system retrieves relevant bank documents and uses the RAG agent to generate a grounded answer.

[![Informational-request sequence diagram](docs/assets/diagrams/informational-request-sequence.png)](docs/assets/diagrams/INFORMATIONAL_SCENARIO.PNG)

### Action requests

Action requests are routed to the function-selection pipeline. The system identifies the required operation, extracts available arguments, collects missing information, and prepares the action for confirmation.

[![Action-request sequence diagram](docs/assets/diagrams/action-request-sequence.png)](docs/assets/diagrams/ACTION_SCENARIO.PNG)
