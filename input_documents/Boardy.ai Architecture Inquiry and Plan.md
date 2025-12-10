# **The Architectural Anatomy of Boardy.ai: Deconstructing the Voice-First Agentic Superconnector**

## **1\. Executive Summary**

The convergence of large language models (LLMs), low-latency voice synthesis, and agentic workflows has birthed a new category of software: the Autonomous Superconnector. Boardy.ai stands as the preeminent example of this paradigm shift, moving beyond the static directory model of traditional professional networking platforms (like LinkedIn) to a dynamic, "Service as Software" architecture. Unlike passive tools that require user manipulation, Boardy operates as an active agent—a digital entity that interviews users, synthesizes unstructured intent, and autonomously executes high-value introductions.

This report provides an exhaustive technical analysis of the architecture underpinning Boardy.ai. It deconstructs the system not merely as a chatbot, but as a complex composite of real-time telephony, cognitive orchestration, semantic retrieval, and asynchronous transaction management. The analysis reveals a system designed around the philosophy of "No-UI," where the primary interface is a high-fidelity voice conversation, necessitating a sophisticated backend capable of sub-500ms latency and high-nuance emotional intelligence.

We identify the core architectural pillars:

1. **The Voice-First Ingestion Layer:** Leveraging advanced telephony (likely Vapi.ai/Twilio), streaming Automatic Speech Recognition (ASR), and state-of-the-art Text-to-Speech (ElevenLabs) to create a "Pixar-like" character experience.  
2. **The Cognitive Orchestration Engine:** A "Half OpenAI" reasoning core that manages conversation state, ensuring empathy and strategic goal alignment (e.g., identifying funding needs vs. hiring needs).  
3. **The Hybrid Matching Engine:** A sophisticated integration of Pearch.ai’s semantic search API and proprietary vector embeddings, likely augmented by a Knowledge Graph (GraphRAG) to map the complex topology of professional relationships.  
4. **The Transactional State Machine:** A rigid, compliance-focused backend (influenced by the founders’ fintech and legal backgrounds) that enforces a "double-opt-in" protocol to maintain high network trust.

Furthermore, this report explores the engineering provenance of the system—traceable to the high-frequency trading backgrounds of its CTO, Abhinav Boyed, and the fintech scalability experience of CEO Andrew D’Souza—arguing that Boardy is architected less like a social network and more like a high-speed matchmaking exchange. By prioritizing depth of connection over breadth of features, and eschewing a dashboard for a voice-only interface, Boardy.ai represents a radical simplification of the user experience enabled by a radical increase in backend complexity.

## **2\. Introduction: The Agentic Shift in Professional Networking**

### **2.1 From Tools to Agents: The "Service as Software" Paradigm**

The history of software has largely been the history of toolmaking. Microsoft Excel, Salesforce, and LinkedIn are powerful tools, but they are fundamentally passive; they rest in a state of inertia until a human operator inputs data or queries a database. The burden of labor—the "work" of calculating, tracking, or searching—remains with the user. The advent of Generative AI has catalyzed a transition to "Agentic AI," where software moves from being a tool to being a worker.

Boardy.ai exemplifies this transition in the domain of professional networking. It does not provide a search bar for users to find investors; it *is* the entity that finds the investor. This distinction is architectural, not just functional. A tool-based architecture optimizes for *query speed* and *interface usability*. An agentic architecture, like Boardy’s, optimizes for *intent understanding*, *autonomous reasoning*, and *task execution*. The system is designed to perform labor: the labor of interviewing, the labor of vetting, and the labor of introduction.

This shift necessitates a "Service as Software" architecture. In traditional SaaS (Software as a Service), the user rents the tool. In Boardy’s model, the user employs the service. The software behaves like a service provider—specifically, a high-end executive assistant or a super-connector. This requires the underlying architecture to maintain long-running states, remember context over weeks or months, and act asynchronously without user triggers.

### **2.2 The "No-UI" Philosophy and Voice as High-Bandwidth Ingestion**

A defining characteristic of Boardy.ai is its rejection of the Graphical User Interface (GUI). There is no app to download, no dashboard to configure, and no complex profile settings to manage.1 The primary interface is the telephone.

From an information theory perspective, this is a strategic architectural decision. Text-based forms are "lossy" compression algorithms for human intent. When a founder selects "Seed Stage" from a dropdown menu, the nuance of their situation—perhaps they are technically pre-seed but have high ARR, or they need a specific type of strategic investor—is lost. Voice, conversely, is a high-bandwidth data stream. It carries not just semantic content (words) but also prosodic information (tone, hesitation, excitement).

Boardy’s architecture is built to ingest this unstructured, high-fidelity data. By conducting a 20-minute voice interview, the system captures thousands of data points that a form could never elicit. The "No-UI" design forces the backend to be exceptionally robust; there are no visual cues to guide the user, so the AI’s conversational logic must be flawless to prevent user confusion. The architecture effectively trades frontend complexity (React components, state management) for backend complexity (ASR, NLU, latency optimization).

### **2.3 The Engineering DNA: Fintech, HFT, and Legal Compliance**

The architecture of any complex system is a reflection of the team that builds it (Conway's Law). Boardy’s founding team brings a unique confluence of skills that shape its technical design:

* **Andrew D'Souza (CEO):** As the co-founder of Clearco, D'Souza has extensive experience in data-driven fintech. This influences Boardy’s focus on structured metrics (e.g., funding amounts, ARR) and the vision of the "Boardy Economy".1 The architecture likely inherits fintech-grade data handling practices.  
* **Abhinav Boyed (CTO):** With a background at Citadel (High-Frequency Trading) building low-latency rule engines in Golang 2, Boyed’s expertise is critical for the real-time telephony stack. Voice AI requires sub-500ms latency to feel natural; techniques from HFT (optimizing network hops, efficient memory management) are directly applicable here.  
* **Matt Stein (Co-Founder):** A lawyer specializing in AI and privacy.3 His influence is visible in the rigorous "double-opt-in" state machine and the privacy-first data architecture. The system is designed to prevent data leakage and ensure consent, treating introductions as legalistic transactions of trust.  
* **Shen Sivananthan:** Bringing engineering leadership from FreshBooks, ensuring the scalability and reliability of the platform as it transitions from a prototype to a service handling millions of calls.4

This pedigree suggests an architecture that prioritizes *speed* (for voice), *compliance* (for trust), and *data fidelity* (for matching).

## **3\. The Voice-First Ingestion Layer: Real-Time Telephony Architecture**

The most technically demanding component of Boardy is the real-time voice interface. Achieving a "magical" conversational experience requires orchestrating a complex pipeline of transcoding, transcription, intelligence, and synthesis within a strict latency budget.

### **3.1 The Latency Budget and the 500ms Threshold**

In human conversation, a pause of longer than 500-700 milliseconds is perceived as "slow" or indicates a connection problem. For an AI agent to feel "present" and "witty," it must respond within this window. Boardy’s architecture must navigate the following sequence:

1. **Network Transit (User to Server):** \~50ms  
2. **Voice Activity Detection (VAD):** \~20ms  
3. **Automatic Speech Recognition (ASR):** \~150ms  
4. **LLM Inference (Time to First Token):** \~200ms  
5. **Text-to-Speech (TTS) Synthesis:** \~100ms  
6. **Network Transit (Server to User):** \~50ms

A naïve implementation sums these to \>500ms. Therefore, Boardy’s architecture likely employs *streaming* and *optimistic execution* at every layer to overlap these processes.

### **3.2 The Telephony Gateway (SIP and WebSockets)**

The entry point is the Public Switched Telephone Network (PSTN). Boardy likely uses a Communication Platform as a Service (CPaaS) provider to bridge the PSTN to its cloud infrastructure.

* **Provider:** While Twilio is the industry standard, **Vapi.ai** 5 has gained traction for voice AI agents because it handles the orchestration of VAD and interruption handling out-of-the-box. Given the community discussions and the "stack" typically associated with modern AI agents, it is highly probable Boardy uses a layer like Vapi or a custom implementation on top of Twilio Media Streams.  
* **Protocol:** The connection from the telephony provider to Boardy’s backend is likely a **WebSocket**. This persistent, bi-directional connection allows raw audio (usually µ-law encoded 8kHz) to be streamed in real-time. Unlike HTTP REST, which is request-response, WebSockets allow the server to push audio (the AI speaking) at any time.

### **3.3 Voice Activity Detection (VAD) and Interruption Handling**

A critical architectural component is the VAD module. It acts as the traffic cop of the conversation.

* **The Challenge:** The system must distinguish between a user finishing a sentence (end-of-turn) and a user pausing to think (mid-turn).  
* **The "Barge-In" Architecture:** If the user interrupts Boardy (barge-in), the system must instantly stop audio playback. This requires the VAD to be running on the inbound audio stream *even while* the system is sending outbound audio.  
* **Implementation:** This is often implemented at the Edge or within the Telephony Gateway to minimize latency. When speech is detected, a "Clear Buffer" command is sent to the audio output stream, silencing the AI immediately to allow the user to speak. This requires a full-duplex architecture where listening and speaking are concurrent threads.

### **3.4 Automatic Speech Recognition (ASR)**

Boardy needs to transcribe audio into text for the LLM.

* **Streaming ASR:** The architecture uses a streaming ASR model (likely **Deepgram** or **OpenAI Whisper** via API). Deepgram is often favored in high-performance agents for its speed and "endpointing" capabilities.  
* **Contextual Biasing:** Networking conversations are full of proper nouns: "Sequoia," "SaaS," "EBITDA," "Solana." Generic ASR models often fail here. Boardy’s architecture likely injects a "vocabulary list" derived from the user's LinkedIn profile 6 into the ASR model context. If the user works at "Anthropic," the ASR is primed to recognize that word, reducing transcription errors.

### **3.5 Text-to-Speech (TTS) and the "Pixar" Persona**

The output of the system is the voice. Andrew D’Souza refers to Boardy as having an "Australian accent" and being "half Pixar".1 This persona is a deliberate architectural choice to disarm users and lower the barrier to sharing information.

* **Technology:** **ElevenLabs** is the industry leader for high-fidelity, low-latency AI voice, and Boardy has been explicitly linked to ElevenLabs in hackathons and integrations.7 The "Turbo" models from ElevenLabs offer sub-100ms latency.  
* **Prosody and Emotion:** The TTS engine is not just reading text; it is acting. The LLM likely generates "stage directions" (e.g., \<break time="0.5s" /\> or \<tone="excited"\>) that are parsed by the TTS engine to modulate pitch and speed. This prevents the "robotic" feel.  
* **Streaming Synthesis:** To hide latency, the TTS engine begins synthesizing audio as soon as the LLM generates the first few tokens of the response. It does not wait for the full sentence. The audio is streamed back to the telephony gateway in chunks, ensuring the user hears the voice almost immediately after the LLM starts "thinking."

## **4\. The Cognitive Core & Orchestration Architecture**

If the voice layer is the "body," the cognitive core is the "mind." Boardy utilizes Large Language Models (LLMs) to understand intent, manage conversation flow, and make decisions.

### **4.1 The "Half OpenAI" Reasoning Engine**

The core reasoning capability is powered by a Foundation Model, identified as OpenAI (likely **GPT-4o** due to its multimodal and speed capabilities).1

* **Why GPT-4o?** Its native reasoning capabilities allow it to handle complex, non-linear conversations. Unlike older chatbots that followed a decision tree (If X, say Y), Boardy’s LLM dynamically decides the next step based on the conversation context.  
* **System Prompt Engineering:** The "personality" of Boardy is defined in a massive System Prompt. This prompt acts as the "Constitution" of the agent. It likely contains:  
  * **Persona:** "You are Boardy, a superconnector. You are friendly, concise, and have an Australian wit."  
  * **Directives:** "Your goal is to extract the user's 'Ask' and 'Offer'. Do not be pushy. Use active listening."  
  * **Guardrails:** "Do not promise investment. Do not share PII of other users."  
* **Refinement Loop:** The prompt is not static. The team, including a creative writer with a background in theater 1, iteratively refines this prompt based on conversation logs to tune the "vibe" of the agent.

### **4.2 Context Management and Memory**

A conversation about a user's career can be long and detailed. Managing the LLM's "Context Window" is a key architectural challenge.

* **Short-Term Memory (Session Context):** The system maintains a sliding window of the current conversation transcript.  
* **Long-Term Memory (User Profile):** When a user calls back weeks later, Boardy remembers them. This implies a **RAG (Retrieval-Augmented Generation)** architecture for memory.  
  * **Mechanism:** Past conversations are summarized and stored in a database (likely PostgreSQL).  
  * **Retrieval:** When a user calls, their profile and past summaries are retrieved and injected into the System Prompt. This allows Boardy to say, "Hey, how did that pitch meeting go last week?" creating the illusion of a continuous relationship.  
* **Stateful Orchestration:** Boardy is likely built on an orchestration framework like **LangChain** or **LangGraph**. This allows the system to maintain a "State" object (e.g., state: { phase: "discovery", data\_collected: \["name", "role"\], missing: \["funding\_stage"\] }). The LLM is tasked with transitioning the state from "Discovery" to "Matching."

### **4.3 Tool Use and Function Calling**

The LLM does not just generate text; it executes actions. Using OpenAI’s Function Calling API, the architecture defines "Tools" the LLM can invoke:

* search\_pearch(query): To query the external database.  
* query\_internal\_network(vector): To search Boardy’s proprietary user base.  
* schedule\_follow\_up(time): To interact with the calendar system.  
* log\_insight(text): To save a key piece of information to the user's profile.

When the LLM detects a need to perform an action (e.g., "I can check my network for that"), it pauses generation, executes the function code, and uses the output to generate the final verbal response.

## **5\. The Matching Engine & Data Infrastructure**

The value of Boardy lies in the quality of its connections. This requires a Matching Engine that transcends simple keyword matching.

### **5.1 The "Moat": Proprietary Unstructured Data**

Andrew D’Souza highlights a "moat" built on **50,000+ human conversations**.1 This is a unique dataset. Unlike LinkedIn, which has structured, self-reported (and often inflated) data, Boardy has unstructured, candid conversational data.

* **Data Pipeline:**  
  1. **Transcription:** Every call is transcribed.  
  2. **Extraction:** An LLM extracts key entities (Tech Stack, Funding History, Personality Traits).  
  3. **Vectorization:** The unstructured text (and potentially the "vibe" or sentiment) is converted into high-dimensional vectors (Embeddings).  
  4. **Storage:** These vectors are stored in a Vector Database (likely **Pinecone**, **Weaviate**, or **pgvector**).

### **5.2 Pearch.ai Integration: Semantic Search at Scale**

A crucial architectural detail is the integration with **Pearch.ai**.8 Pearch provides a "natural language candidate search API" that Boardy uses to power its discovery.

* **The Problem:** Searching for people is hard. "Find me a react developer" is easy. "Find me a CTO who has scaled a fintech team from 10 to 100" is hard for traditional SQL databases.  
* **The Solution:** Pearch.ai allows Boardy to pass the natural language intent directly to the search engine. Pearch’s API likely returns a ranked list of candidates from a massive external dataset (30M+ companies).  
* **Hybrid Search:** Boardy’s architecture likely performs a "Federated Search":  
  * **Query 1 (Internal):** Search Boardy’s proprietary vector database for "warm" connections (people already in the network).  
  * **Query 2 (External \- Pearch):** Search the broader world for perfect profile matches.  
  * **Synthesis:** The LLM re-ranks these results, prioritizing internal/warm connections but supplementing with external candidates if no internal match exists.

### **5.3 Knowledge Graphs and GraphRAG**

While Vector Search finds *similar* things, **Knowledge Graphs** find *connected* things. Professional networking is a graph problem.

* **Graph Database:** The architecture likely employs a Graph Database (like **Neo4j** or **FalkorDB**, hinted at in RAG discussions 9).  
* **Nodes:** Users, Companies, VC Firms, Universities.  
* **Edges:** "FOUNDED," "INVESTED\_IN," "WORKED\_AT," "INTRODUCED\_TO."  
* **GraphRAG:** When the LLM considers an intro, it queries the graph.  
  * *Query:* "Who does User A know that knows User B?"  
  * *Reasoning:* "User A’s previous co-founder is now a partner at the VC firm User B wants to reach."  
  * *Result:* This "path" becomes the context for the introduction, making it warm rather than cold. This ability to reason over *paths* is what separates a "Superconnector" from a directory.

## **6\. The Transactional State Machine & Execution Layer**

Boardy is not just a chat bot; it is a workflow automation bot. It facilitates introductions, which are transactional in nature.

### **6.1 The "Double-Opt-In" Protocol**

In high-end networking, introducing two people without permission is a faux pas. Boardy automates the "Double-Opt-In" (DOI) process, which acts as a state machine for every potential connection.

* **State 1: Identification.** The engine identifies a match.  
* **State 2: Unilateral Consent (Side A).** Boardy asks User A (on the call): "I know someone, User B. Want an intro?" User A says "Yes."  
* **State 3: Outreach (Side B).** Boardy sends an email (or voice call) to User B: "User A (Context) wants to meet you. Interested?"  
* **State 4: Bilateral Consent.** User B clicks "Yes."  
* **State 5: Introduction.** Boardy sends the email connecting them.

This state machine is likely implemented in a relational database (**PostgreSQL**) to ensure ACID compliance. You cannot afford to lose the state of an introduction.

### **6.2 Asynchronous Email Agents**

Much of Boardy’s work happens off the phone. The architecture includes "Headless Agents" that operate via email.

* **Email Generation:** The LLM generates personalized emails for the outreach. It uses the context from the voice call to write a compelling "blurb" about User A to send to User B.  
* **Inbound Parsing:** If User B replies to the email with "Not now, but maybe next quarter," Boardy’s email parser (likely using an LLM to classify intent) must read this, update the state in the database, and schedule a follow-up task for 3 months later.  
* **Infrastructure:** Transactional email services like **SendGrid** or **Postmark** are used for delivery, with webhooks feeding reply data back into the system.

## **7\. Infrastructure, Security, and Scalability**

### **7.1 Cloud Infrastructure: The Azure Connection**

Given the strong reliance on OpenAI and the founders' advice regarding tech stacks 10, **Microsoft Azure** is the most probable cloud environment.

* **Scalability:** Handling thousands of concurrent WebSocket connections for voice requires robust load balancing and auto-scaling. Kubernetes (AKS) is the standard solution here.  
* **Compliance:** Azure’s enterprise-grade compliance certifications align with the team’s focus on privacy and data security.

### **7.2 Data Privacy and Sovereignty**

Boardy operates in a high-trust environment.

* **Data Incident:** The team faced early scrutiny regarding data transparency 10, leading to a rigorous overhaul of their privacy communications.  
* **Architecture:** The "Privacy-First" approach implies:  
  * **Data Minimization:** Only storing what is necessary.  
  * **Access Control:** Strict RBAC (Role-Based Access Control) preventing engineers from listening to user calls without consent.  
  * **Encryption:** Data at rest (DB) and in transit (WebSockets/API) is encrypted.  
* **GDPR:** With European investors (Creandum) and a global user base, the architecture must support data sovereignty, potentially sharding data by region (EU users in EU data centers).

### **7.3 The "Cold Start" Solution**

Scalability is not just technical; it's social. Boardy solved the network effect "Cold Start" problem by manually seeding the database with high-value profiles (Founders, VCs).1

* **Architectural Implication:** The Matching Engine likely has dynamic thresholds. In the early days, with fewer nodes, the "relevance score" threshold for a match might have been looser to ensure activity. As the network grows, the algorithm tightens, prioritizing higher-quality, more specific matches.

## **8\. Future Directions: The "Boardy Economy"**

The architecture is being laid for a future that transcends simple introductions. Andrew D’Souza envisions a "Boardy Economy" exceeding the GDP of Switzerland.1

### **8.1 Agent-to-Agent (A2A) Protocols**

The future architecture will likely involve **Agent-to-Agent** communication.

* **Concept:** Instead of Boardy talking to a human VC, Boardy talks to the VC’s AI Agent.  
* **Protocol:** This requires standardized protocols for agent negotiation (e.g., "Agent Protocol" or similar emerging standards). The architecture will need to support structured data exchange between agents to negotiate meeting times, share deal flow, and execute agreements.

### **8.2 Transactional Layers**

To achieve an "Economy," the architecture must support value transfer.

* **Payments:** Integration with Stripe or similar platforms to handle "Success Fees" or subscription revenue.11  
* **Smart Contracts:** Potential future integration of blockchain for verifiable credentials or equity management (given the founders' fintech/crypto backgrounds).

## **9\. Detailed Component Breakdown Table**

To summarize the technical findings, the following table deconstructs the Boardy architecture into its constituent parts, supported by evidence from the research.

| Layer | Component | Likely Technology Stack | Function & Insight |
| :---- | :---- | :---- | :---- |
| **Ingestion** | **Telephony** | **Vapi.ai / Twilio** | Handles SIP trunking and WebSockets. Vapi is chosen for its built-in orchestration of VAD and turn-taking logic.5 |
|  | **ASR** | **Deepgram** / **Whisper** | Streaming transcription. Deepgram is favored for speed and "Nova" models that handle proper nouns well. |
| **Cognitive** | **Reasoning** | **OpenAI GPT-4o** | The "Brain." Handles NLU, intent classification, and generates conversational responses. "Half OpenAI".1 |
|  | **Orchestration** | **LangChain** / **Custom** | Manages conversation state, tool calling, and RAG pipelines. |
|  | **Persona** | **System Prompt** | Defines the "Australian, Pixar-like" character. A crucial layer of "Soft Engineering." |
| **Retrieval** | **Semantic Search** | **Pearch.ai** | External candidate discovery API. Provides access to 30M+ profiles.8 |
|  | **Vector DB** | **Pinecone** / **pgvector** | Stores embeddings of user conversations for internal matching. The "Moat." |
|  | **Knowledge Graph** | **Neo4j** / **GraphRAG** | Maps relationships (Who knows Who). Critical for "warm" intros. |
| **Output** | **TTS** | **ElevenLabs** | Generates the "Australian" voice. "Turbo" model for low latency.7 |
| **Execution** | **State Machine** | **PostgreSQL** | Tracks the "Double-Opt-In" status (Pending \-\> Accepted \-\> Intro). ACID compliance is key. |
|  | **Email** | **SendGrid** / **Postmark** | Delivers the actual introduction emails and handles async communication. |
| **Infra** | **Cloud** | **Microsoft Azure** | Scalable compute. Chosen for security and relationship with OpenAI. |

## **10\. Conclusion**

Boardy.ai represents a sophisticated evolution in application architecture. It moves away from the CRUD (Create, Read, Update, Delete) paradigm of traditional web apps and towards an **Agentic Loop** (Perceive, Reason, Act).

By forcing the interaction through a voice-only interface, the team has necessitated the creation of a backend that is exceptionally capable of understanding nuance. The integration of **ElevenLabs** for presence, **Pearch.ai** for reach, and **OpenAI** for reasoning creates a "Composite AI" system that is greater than the sum of its parts.

The architecture is designed for **trust**. Through its "No-UI" simplicity, its "Pixar" persona, and its rigorous "Double-Opt-In" state machine, Boardy creates a digital environment where users feel comfortable sharing the high-fidelity data that powers the entire system. As the network grows, the accumulation of this proprietary conversational data into a Vector/Graph hybrid database will likely cement Boardy’s position not just as a tool, but as a central infrastructure layer for the professional economy.

#### **Works cited**

1. How Boardy Raised $8M on Its Own Platform with Founder Andrew ..., accessed December 10, 2025, [https://www.justgogrind.com/p/andrew-d-souza-boardy-ai](https://www.justgogrind.com/p/andrew-d-souza-boardy-ai)  
2. Abhinav B. \- Prev. CTO & Co-founder @ Boardy AI | LinkedIn, accessed December 10, 2025, [https://www.linkedin.com/in/abhinavboyed/](https://www.linkedin.com/in/abhinavboyed/)  
3. Matthew Stein \- Artificial Intelligence Law Lawyer \- Portland, ME, accessed December 10, 2025, [https://www.bestlawyers.com/lawyers/matthew-stein/185204](https://www.bestlawyers.com/lawyers/matthew-stein/185204)  
4. AI networking agent Boardy secures $8 million investment all on its own, accessed December 10, 2025, [https://americanbazaaronline.com/2025/01/15/ai-networking-agent-boardy-secures-8-million-investment-all-on-its-own458350/](https://americanbazaaronline.com/2025/01/15/ai-networking-agent-boardy-secures-8-million-investment-all-on-its-own458350/)  
5. How Could a Tool Like Boardy.ai Be Technically Built? · AI Automation Society \- Skool, accessed December 10, 2025, [https://www.skool.com/ai-automation-society/how-could-a-tool-like-boardyai-be-technically-built](https://www.skool.com/ai-automation-society/how-could-a-tool-like-boardyai-be-technically-built)  
6. Boardy, accessed December 10, 2025, [https://www.boardy.ai/](https://www.boardy.ai/)  
7. ElevenLabs x a16z Global Hackathon: Ask Chum AI \- YouTube, accessed December 10, 2025, [https://www.youtube.com/watch?v=ETIdABFx7hg](https://www.youtube.com/watch?v=ETIdABFx7hg)  
8. PEARCH AI FAQ — Everything About the People Search & Sourcing API, accessed December 10, 2025, [https://pearch.ai/frequently-asked-questions](https://pearch.ai/frequently-asked-questions)  
9. How to Build an AI RAG Workflow using FalkorDB \+ N8N \+ Graphiti Agent Module, accessed December 10, 2025, [https://www.falkordb.com/blog/ai-rag-workflow-falkordb-n8n-graphiti/](https://www.falkordb.com/blog/ai-rag-workflow-falkordb-n8n-graphiti/)  
10. AI Bot, Boardy, Just Closes $8M Seed Round Entirely On Its Own : r/ArtificialInteligence, accessed December 10, 2025, [https://www.reddit.com/r/ArtificialInteligence/comments/1i3ebj0/ai\_bot\_boardy\_just\_closes\_8m\_seed\_round\_entirely/](https://www.reddit.com/r/ArtificialInteligence/comments/1i3ebj0/ai_bot_boardy_just_closes_8m_seed_round_entirely/)  
11. News \- Horizon Capital, accessed December 10, 2025, [https://horizoncap.vc/category/news/](https://horizoncap.vc/category/news/)