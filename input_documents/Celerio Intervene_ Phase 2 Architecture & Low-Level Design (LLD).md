# **Celerio Intervene: Phase 2 Architecture & Low-Level Design (LLD)**

This document outlines the **Autonomous Revenue Architect** system. It is designed to be "One-Shot" coded using **Cursor Composer** (Claude 3.7 Sonnet / 3.5 Sonnet) or **Kilo**.

## **1\. System Architecture**

The system operates as a **Stateful Multi-Agent System** orchestrating three external "Super-APIs" to mimic a human consultant's workflow.

### **High-Level Data Flow**

1. **Trigger:** Phase 1 (Scout) pushes a Company Profile (JSON) into the leads table.  
2. **Orchestrator (LangGraph):** Wakes up, analyzes the profile, and selects an outreach strategy.  
3. **Action Layer:**  
   * **LinkedIn/Email:** Uses **Unipile** to send a hyper-personalized "Stall Diagnosis" DM.  
   * **Voice:** Uses **Bland AI** to conduct a "Discovery Call" if the prospect engages.  
   * **Data:** Uses **Unified.to** to ingest raw CRM data (HubSpot/Salesforce) once authorized.  
4. **Presentation Layer:** A "Founder Portal" (React) where the prospect views their "Revenue Bowtie" diagnosis and unlocks the "90-Day Plan" via **Stripe**.

## ---

**2\. Database Schema (Supabase)**

**Instruction for Dev Team:** Run this SQL in the Supabase SQL Editor to hydrate the backend state.

SQL

\-- The Master Ledger of "Stalling" Companies  
create table leads (  
  id uuid primary key default gen\_random\_uuid(),  
  company\_name text not null,  
  website\_url text,  
  founder\_linkedin\_url text,  
  status text default 'new', \-- new, contacting, engaged, diagnosing, converted, dead  
  stall\_signals jsonb, \-- { "hiring\_freeze": true, "traffic\_drop": "20%" }  
  created\_at timestamp with time zone default now()  
);

\-- The Interaction Log (Memory for the Agent)  
create table interactions (  
  id uuid primary key default gen\_random\_uuid(),  
  lead\_id uuid references leads(id),  
  channel text, \-- 'linkedin', 'email', 'voice\_bland'  
  direction text, \-- 'inbound', 'outbound'  
  content text,  
  metadata jsonb, \-- { "call\_id": "...", "sentiment": "positive" }  
  created\_at timestamp with time zone default now()  
);

\-- The Celerio Diagnostic State (The "Brain" Dump)  
create table diagnostics (  
  id uuid primary key default gen\_random\_uuid(),  
  lead\_id uuid references leads(id),  
  vector\_market\_score int, \-- 0-100  
  vector\_motion\_score int,  
  vector\_messaging\_score int,  
  crm\_data\_snapshot jsonb, \-- Real data from Unified.to  
  prescription\_markdown text, \-- The generated 90-day plan  
  is\_unlocked boolean default false \-- Stripe payment status  
);

## ---

**3\. Backend Implementation (LangGraph \+ Python)**

**Dev Instruction:** Use this specific prompt in **Cursor Composer**. It defines the "State Machine" that prevents the bot from hallucinating or spamming.

### **Prompt Block 1: The Agent Brain (agent.py)**

Role: You are a Senior Python Backend Architect.  
Goal: Build a LangGraph StateMachine that orchestrates a sales intervention agent.  
1\. Define State:  
Create a TypedDict named AgentState containing:

* lead\_id: str  
* profile: dict (Company Name, Founder Name, Stall Signals)  
* interaction\_history: list  
* engagement\_stage: "outreach" | "discovery" | "data\_sync" | "prescription"  
* vectors: dict (Market, Motion, Messaging scores)

**2\. Define Nodes:**

**Node A: monitor\_inbox**

* Input: lead\_id  
* Action: Check **Supabase** interactions table for new replies (webhooks will populate this).  
* Logic: If new reply contains "Positive Sentiment" (use TextBlob or simple keyword check), transition to schedule\_discovery. If "Stop/Unsubscribe", transition to end.

**Node B: execute\_outreach**

* Action: If engagement\_stage is "outreach", verify no message sent in last 3 days.  
* Tool: Call send\_unipile\_linkedin\_dm.  
* Prompt Logic: "You are Celerio. Write a 1-sentence DM to {Founder} about {Stall\_Signal}. Do not sound like a bot. End with 'Open to a 5-min diagnosis?'"

**Node C: trigger\_voice\_agent (Bland AI)**

* Trigger: If engagement\_stage becomes "discovery" (User said "Call me").  
* Action: Call bland\_ai.calls.create().  
* Payload: Pass pathway\_id="" and inject stall\_signals into the dynamic\_data field so the voice bot knows context.

**Node D: generate\_prescription**

* Trigger: engagement\_stage is "prescription" (CRM data received).  
* Action: Use LLM (Claude 3.5 Sonnet) to compare crm\_data against benchmarks.  
* Output: Save a Markdown "90-Day Plan" to Supabase.

**3\. Define Edges:**

* monitor\_inbox \-\> execute\_outreach (if no reply & time \< 7 days).  
* monitor\_inbox \-\> trigger\_voice\_agent (if reply \== "call me").  
* trigger\_voice\_agent \-\> wait\_for\_crm\_sync.

Tech Stack: Python 3.11, LangGraph, Supabase-py.  
Output: Generate agent\_graph.py and requirements.txt.

## ---

**4\. The "Boardy" Voice Logic (Bland AI Configuration)**

**Dev Instruction:** Do not code the conversation flow in Python. Use **Bland AI's Conversational Pathways** editor (Visual Builder) to handle the latency.

**Configuration Prompt for Bland AI Portal:**

* **Voice:** "Josh" or "Matt" (Sound authoritative, not cheery).  
* **Max Latency:** set to \<1000ms.  
* **System Prompt:**"You are Celerio, a Revenue Architect. You called {name} because their data signals a stall. You are NOT selling. You are diagnosing.  
  Phase 1: The Hook  
  "I'm looking at your traffic graph. It's flatlining, but I see you just hired 3 engineers. That usually means a 'Motion' problem. Is that fair?"  
  Phase 2: The Bowtie Diagnostic  
  If they say 'Yes': "Okay. Let's look at the Revenue Bowtie. Is your issue on the Left Side (Leads) or the Center (Closing)?"  
  If 'Leads': "Got it. Acquisition Leakage. We need to check your Messaging Vector."  
  If 'Closing': "Understood. Sales Velocity Physics. We need to check your Motion Vector."  
  Phase 3: The Close  
  "I can't fix this over the phone. I need to run your HubSpot data through my model to generate a 90-day fix. I'm texting you a secure link now. Click it to authorize the sync." (Tool Call: send\_sms\_link)

## ---

**5\. Frontend "Founder Portal" (React \+ Shadcn)**

**Dev Instruction:** Use this prompt in **Cursor Composer** to build the client-facing dashboard.

### **Prompt Block 2: The Celerio Dashboard**

Role: Senior Frontend Engineer.  
Goal: Build the "Celerio Founder Portal" where users view their diagnosis.  
Stack: React, Vite, Tailwind CSS, Shadcn/UI, Recharts, Framer Motion.  
**1\. The "Revenue Bowtie" Component:**

* Create a custom SVG component representing the "Bowtie" diagram (from uploaded image).  
* **Behavior:** It must be interactive.  
  * **Left Side (Marketing):** Hovering highlights "Acquisition Leakage".  
  * **Center (Sales):** Hovering highlights "Sales Velocity".  
  * **Right Side (CS):** Hovering highlights "Expansion Stagnation".  
* **State:** The bowtie colors should be Grey (Locked) initially. As data comes in from the backend, color the sections Red (Critical), Yellow (Warning), or Green (Healthy).

**2\. The "Unified" Integration Modal:**

* Implement the **Unified.to** embedded React widget.  
* **Trigger:** A prominent button "Connect CRM to Diagnose".  
* **Action:** On success, POST the connection\_id to my backend endpoint /api/sync-crm.

**3\. The "90-Day Plan" Paywall:**

* Create a PlanDisplay component.  
* **Logic:** If is\_unlocked is false, apply a CSS blur-md filter to the text content and overlay a "Unlock Full Plan \- $X" button (Stripe Link).  
* **Content:** The plan text comes from the Supabase diagnostics table.

**4\. Vibe:**

* Dark Mode only.  
* Font: Inter or Geist Mono.  
* Colors: Deep Navy (\#0f172a), Neon Cyan (\#06b6d4) for accents.

**Output:** Generate App.jsx, Bowtie.jsx, and Dashboard.jsx.

## ---

**6\. Integration Glue (The "Secret Sauce")**

To make this autonomous, you need specific API helper functions.

### **A. Unipile (LinkedIn DMs)**

Endpoint: POST https://api.unipile.com/api/v1/chats  
Vibe Code Instruction:  
"Write a Python function send\_linkedin\_dm(provider\_id, text) using requests. Handle rate limits by checking the 429 status code and sleeping. Ensure the text is spintaxed (randomized variations) to avoid spam detection."

### **B. Unified.to (CRM Extraction)**

Endpoint: GET /crm/deals & GET /crm/companies  
Logic:  
"Write a Python function calculate\_sales\_velocity(connection\_id) that fetches closed-won deals from Unified.to.  
Formula: (Num Opportunities \* Deal Value \* Win Rate) / Sales Cycle Length.  
Return this float as the 'Motion Score'."

### **C. Stripe (The Lock)**

**Logic:**

"Create a Supabase Edge Function stripe-webhook that listens for checkout.session.completed. When received, update the diagnostics table: set is\_unlocked \= true for the matching lead\_id."

## ---

**7\. Execution Checklist for Dev Team**

1. **Day 1:** Run Supabase SQL. Deploy LangGraph backend (Docker on Railway/Render). Set up Unipile/Bland/Unified API keys.  
2. **Day 2:** "Vibe Code" the React Frontend using Prompt Block 2\. Integrate the Unified.to widget.  
3. **Day 3:** Configure Bland AI Pathway (Visual Editor). Test the "Voice \-\> SMS Link \-\> CRM Connect" loop.  
4. **Day 4:** Turn on the Phase 1 Scout. Feed 5 test leads. Watch the autonomous intervention happen.