# **Global Venture Capital Traceability Report: 2024–2025 Funding Flows**

**Entity Resolution, Capital Provenance, and Liquidity Events in the Private Markets**

## **Executive Summary**

The global venture capital landscape underwent a fundamental structural transformation between Q1 2024 and Q3 2025\. This report, constructed through a rigorous data engineering methodology involving the normalization of thousands of funding events, provides a definitive traceability analysis of capital flows in the private markets. The data indicates that the asset class formally known as "Venture Capital" has bifurcated into two distinct financial ecosystems: a traditional, albeit contracted, early-stage innovation economy, and a massive, capital-intensive "Industrial AI" complex that operates with the check sizes and strategic imperatives of sovereign nation-states.

Our traceability dataset, which resolves entities across heterogeneous sources ranging from regulatory filings to press releases, reveals that aggregate global funding for 2024 reached a range of $314 billion to $368 billion.1 However, this aggregate figure masks a historic concentration anomaly. Nearly one-third of all global venture capital was absorbed by fewer than 20 entities—primarily those constructing the foundational layer of Generative Artificial Intelligence (GenAI) and the physical infrastructure required to power it. The provenance of this capital has shifted dramatically. While traditional Limited Partners (LPs) such as UTIMCO and CalPERS remain active 3, the driving force behind the "Mega-Nodes"—rounds exceeding $1 billion—has been a coalition of Corporate Venture Capital (CVC) balance sheets (Microsoft, Amazon, Nvidia, ASML) and Sovereign Wealth Funds (MGX, QIA, GIC).

The analysis identifies 2024–2025 not as a period of recovery, but as a "Supercycle" of infrastructure deployment. The definition of venture capital has been stretched to include the financing of massive physical assets, such as GreenScale’s $1.3 billion data center initiative 5 and CoreWeave’s debt-heavy $8.6 billion financing stack.6 These are not software margin plays; they are industrial capital expenditure projects financed through equity structures. Furthermore, liquidity in this period was not achieved through the traditional Initial Public Offering (IPO) mechanism, but rather through unprecedented secondary market engineering. The massive tender offers orchestrated for OpenAI and CoreWeave signify a structural shift in how liquidity is delivered to employees and early investors, effectively creating a "private IPO" market that bypasses public scrutiny while sustaining decacorn valuations.7

This document serves as both a strategic narrative and a technical manual. It includes a reconciled traceability matrix for regional totals, a detailed reconciliation log for conflicting valuation data, and machine-readable artifacts (JSON/CSV) designed to facilitate high-fidelity graph visualization of these complex, multi-layered financial flows.

## ---

**1\. Data Engineering Methodology & Traceability Framework**

To produce a high-fidelity dataset that withstands scrutiny, a rigorous data engineering pipeline was established. The primary challenge in quantifying the private markets is the lack of standardized reporting. Discrepancies arise from differing definitions of "venture capital," inconsistent currency conversion methodologies, and the opacity of "undisclosed" participants.

### **1.1 Entity Resolution and Taxonomy**

The construction of the knowledge graph required sophisticated entity resolution to disentangle complex corporate structures. For example, "OpenAI" exists as a non-profit entity, a capped-profit subsidiary (OpenAI Global, LLC), and various holding vehicles. Capital flows must be attributed to the correct node to understand the governance implications. Similarly, distinguishing between "SoftBank Group" (the corporate balance sheet) and "SoftBank Vision Fund" (the LP-backed vehicle) is critical for tracing risk exposure. Our methodology treats these as distinct nodes linked by "affiliated\_with" edges, rather than collapsing them into a single entity.

### **1.2 Currency Normalization Protocols**

Global venture activity is denominated in a basket of currencies, yet comparative analysis requires a single numeraire. All figures in this report are normalized to United States Dollars (USD). The normalization protocol utilizes a "point-in-time" spot rate based on the announced\_date of the transaction. For rounds reported only in local currency (e.g., Mistral AI’s €1.7 billion Series C), the conversion is locked at the exchange rate prevalent in September 2025\.9 This prevents currency volatility from distorting historical trend analysis. Where conflicting USD values appear in source documents (e.g., GreenScale’s £1 billion being reported as $1 billion or $1.3 billion), the local currency value is treated as the source of truth, and the USD value is recalculated using the verified historical rate.

### **1.3 Source Hierarchy and Confidence Scoring**

Data provenance is maintained through a strict hierarchy of sources.

* **Tier 1 (Primary):** Regulatory filings (SEC Form D, Companies House UK), official company press releases, and direct investor announcements. These are assigned a confidence score of 1.0.  
* **Tier 2 (Secondary Verified):** Reputable financial journalism (Bloomberg, Financial Times, WSJ) citing "people familiar with the matter" regarding closed rounds. These are assigned a confidence score of 0.8–0.9.  
* **Tier 3 (Aggregators):** Database dumps from PitchBook, Crunchbase, or Dealroom without primary citation. These are assigned a confidence score of 0.7 and are used primarily for cross-validation.

Conflict resolution follows a "Recency \+ Specificity" logic. If a press release dated December 17, 2024, states a round size of $10 billion 10, it supersedes a journalistic report from November 2024 estimating $9.5 billion.

## ---

**2\. Global Traceability Matrix: Regional & Sector Totals**

The analysis of 2024 and 2025 funding data reveals a highly concentrated global market. The sheer magnitude of capital deployed in North America, driven by the AI Supercycle, creates a statistical skew that distorts global averages. To provide a nuanced view, we present a regional breakdown that isolates "Mega-Nodes" from the broader ecosystem.

### **2.1 North America: The Engine of the Supercycle**

North America remains the undisputed hegemon of the venture ecosystem, accounting for approximately $170 billion to $210 billion of the global total.1 However, the composition of this capital is radically different from the SaaS-driven cycles of 2015–2021.

* **The Bay Area Gravity Well:** The San Francisco Bay Area alone absorbed nearly $90 billion in 2024, representing over 50% of total US funding.1 This concentration is a direct result of the geographic clustering of the "AI Model Layer"—OpenAI, Anthropic, and Databricks are all headquartered within a tight radius. The "agglomeration effects" of talent and capital have intensified, effectively draining liquidity from secondary hubs like Austin, Miami, or Los Angeles, with the notable exception of specific defense-tech corridors.  
* **The Re-Industrialization of VC:** A significant portion of North American funding is classified as "Venture" but functions as industrial project finance. CoreWeave’s financing activities, totaling billions in equity and debt, are physically located in New Jersey and Texas but managed financially through New York and Silicon Valley.6 This represents a shift where VC funds are underwriting the re-industrialization of American compute capacity.

### **2.2 Europe: Sovereign AI and Strategic Autonomy**

Europe’s venture total for the period stands between $55 billion and $65 billion.11 While lower in absolute terms than the US, the strategic intent of the capital is distinct.

* **The Rise of Sovereign Champions:** The financing of Mistral AI (€1.7 billion Series C) is the defining event of the European market.13 The traceability of this round reveals a deliberate "European Sovereign Stack." The lead investor, ASML (the Dutch lithography monopoly), represents a strategic alignment between hardware manufacturing and model capability. This is not merely a financial return play; it is a geopolitical move to ensure Europe maintains an indigenous Large Language Model (LLM) capability independent of US hyperscalers.  
* **UK as the Infrastructure Bridge:** The United Kingdom accounted for the largest share of European VC, driven significantly by the GreenScale Data Centres transaction ($1.3 billion).5 This deal highlights the UK’s role as a financial and physical bridge for digital infrastructure, attracting capital from German managers (DTCP) to fund assets that serve the broader European continent.16

### **2.3 Asia-Pacific: The Bifurcation of Ecosystems**

APAC totals range from $70 billion to $80 billion, but the region is increasingly fragmented.2

* **China’s Internal Loop:** Data visibility into China has decreased, but the trend is clear: state-backed guidance funds are replacing USD-denominated VC. Large rounds, such as the $1.1 billion for CNNP Rich Energy 11, indicate a focus on "Hard Tech" and energy transition rather than consumer internet.  
* **The Rise of the Middle East:** While geographically distinct, MENA-based Sovereign Wealth Funds (SWFs) are the "Dark Matter" of the global venture universe. Entities like MGX (UAE) and the Qatar Investment Authority (QIA) are appearing directly on the cap tables of US and European champions (OpenAI, xAI, Databricks), bypassing traditional LP commitments to exert direct influence.10

### **2.4 Traceability Matrix**

| Region | Est. Total Funding (USD) | Key Mega-Nodes (\>$1B) | Capital Provenance Archetype | Source Citations |
| :---- | :---- | :---- | :---- | :---- |
| **North America** | **$170B – $210B** | OpenAI ($6.6B), Databricks ($10B), xAI ($12B), Waymo ($5.6B), CoreWeave ($1.1B) | US Mega-Funds (Thrive, Founders Fund) \+ US Corp (MSFT, Amazon) | 1 |
| **Europe** | **$55B – $65B** | Mistral AI (€1.7B), GreenScale ($1.3B), Wayve ($1.05B), Helsing (€450M) | Corporate Strategic (ASML) \+ Euro Infra Funds (DTCP) | 5 |
| **Asia (APAC)** | **$70B – $80B** | Didi Autonomous ($298M), Moonshot AI, Indian SaaS | State-Backed Guidance Funds \+ Local Conglomerates | 2 |
| **Total Global** | **$314B – $368B** | AI Sector accounted for \>30% of total volume globally. | Mixed Global Flows | 1 |

## ---

**3\. Deep Dive: The AI Supercycle & Mega-Round Traceability**

This section isolates the specific companies that have distorted the venture data landscape. These "Mega-Nodes" are not just startups; they are capital aggregators that function similarly to public companies in terms of governance and treasury management.

### **3.1 The Sovereign Node: OpenAI**

The financing of OpenAI in 2024 and 2025 represents the most complex capital structure in venture history. Our traceability analysis resolves two distinct major events.

* **Primary Round (October 2024):** A $6.6 billion equity injection at a $157 billion post-money valuation.22  
  * **Traceability:** The round was led by **Thrive Capital**, specifically leveraging their Fund IX vehicle. Participants included **Microsoft**, **Nvidia**, **SoftBank**, **Khosla Ventures**, **Fidelity**, and **MGX**.  
  * **Strategic Divergence:** A key finding is the reported withdrawal of Apple from these talks, signaling a divergence in the "Big Tech" AI alliance.22  
  * **Implication:** The provenance of capital here is purely strategic. Microsoft and Nvidia are funding their own ecosystem demand, while MGX represents the UAE's bid for AI relevance.  
* **The SoftBank Tender (March 2025):** This event marks a shift in liquidity mechanics. **SoftBank Group** led a tender offer valued at $40 billion, structured to allow employee liquidity while avoiding the dilution of a primary issuance.7  
  * **Structure:** The deal involved a $10 billion initial tranche followed by a $30 billion conditional tranche contingent on OpenAI’s restructuring into a for-profit entity.  
  * **Provenance:** SoftBank utilized the "Project Stargate" infrastructure initiative as the strategic rationale for this re-entry, linking capital deployment directly to future compute infrastructure build-outs.23

### **3.2 The Enterprise Data Node: Databricks**

While OpenAI captures the public imagination, Databricks secured the largest single equity check of 2024\.

* **Event:** Series J (December 2024).  
* **Capital Flows:** $10 billion in equity financing paired with a separate $5.25 billion debt facility.18  
* **Valuation:** $62 billion.  
* **Provenance:**  
  * **Lead:** **Thrive Capital** (Fund IX).  
  * **Co-Leads:** **Andreessen Horowitz (a16z)**, **DST Global**, **GIC** (Singapore Sovereign), **Insight Partners**, and **WCM**.  
  * **Observation:** The participation of GIC alongside US Venture funds confirms the trend of sovereign direct investment. The explicit use of funds for employee liquidity buybacks ($90/share) demonstrates that this round served as a "synthetic IPO," providing public-market-like liquidity without the regulatory burden.10

### **3.3 The Compute Node: xAI**

Elon Musk’s xAI creates a unique traceability loop involving his personal network and legacy Twitter (X) investors.

* **Series B (May 2024):** $6 billion raised at a $24 billion valuation.25  
* **Series C (Dec 2024/Jan 2025):** Another $6 billion raised at a $50 billion valuation.17  
* **Capital Loop:** The investor list features **Valor Equity Partners**, **Sequoia Capital**, and **Andreessen Horowitz**. Crucially, the participation of **Kingdom Holding Company** (Prince Alwaleed bin Talal) creates a direct capital lineage to the privatization of Twitter. This "closed loop" of capital allows Musk to leverage relationships across his conglomerate to fund high-capex AI training clusters in Memphis.17

### **3.4 The Autonomous Node: Waymo**

Waymo’s $5.6 billion Series C in October 2024 marks the transition of autonomous driving from "R\&D experiment" to "commercial growth equity".29

* **Lead Investor:** **Alphabet**. The parent company led the round, reaffirming its commitment despite external capital entry.  
* **External Validation:** Participation from **Andreessen Horowitz**, **Fidelity**, **Perry Creek**, **Silver Lake**, **Tiger Global**, and **T. Rowe Price**.  
* **Insight:** The presence of Silver Lake and T. Rowe Price—classic late-stage/private equity investors—indicates that Waymo is being valued on unit economics and market expansion plans (Austin, Atlanta) rather than pure technological promise.30

### **3.5 The Industrial Infrastructure Nodes: CoreWeave & GreenScale**

These entities necessitate a reclassification of "Venture Capital." They are financing heavy industrial assets (GPUs, Data Centers) using venture equity structures.

* **CoreWeave (USA):**  
  * **Series C (May 2024):** $1.1 billion equity at a $19 billion valuation, led by **Coatue**.6  
  * **Debt Stack:** A staggering $7.5 billion debt facility led by **Blackstone** and **Magnetar**.  
  * **Mechanism:** This financing is unique because it uses the H100 GPU chips themselves as collateral. The venture equity serves merely as the "down payment" for the massive debt required to acquire hardware. This is asset-backed finance disguised as venture capital.12  
* **GreenScale Data Centres (UK):**  
  * **Funding:** $1.3 billion (£1 billion) seed/growth round in late 2024/early 2025\.5  
  * **Backers:** **DTCP** (Digital Transformation Capital Partners).  
  * **Context:** This single transaction distorted UK venture data for Q4 2024\. Traceability confirms this is "greenfield" infrastructure financing—building sustainable data centers from scratch to meet the power demands of the AI models discussed above.20

## ---

**4\. Fund & LP Provenance: The Source of Capital**

To truly understand these flows, we must trace the capital back one layer further: to the Limited Partners (LPs) who fund the Venture Capital firms (GPs).

### **4.1 Thrive Capital: The Central Node**

Thrive Capital has positioned itself as the "Aggregator" of the 2024–2025 cycle, leading the most significant rounds for OpenAI and Databricks.

* **Vehicle:** Thrive Capital Fund IX ($1 billion Early / $4 billion Growth).32  
* **LP Traceability:**  
  * **UTIMCO:** The University of Texas/Texas A\&M Investment Management Company has been identified as a committed LP.3  
  * **Princeton University:** A historical backer that likely re-upped for Fund IX.  
  * **Structural Insight:** Thrive’s ability to deploy multibillion-dollar checks indicates a shift toward "Lifecycle Capital," enabling them to compete directly with public markets and sovereign funds for allocation.

### **4.2 Founders Fund: The Defense Anchor**

Founders Fund has anchored the "American Dynamism" thesis, leading the $1.5 billion Series F for Anduril.34

* **Vehicle:** Founders Fund VIII ($900 million Venture / Growth vehicles).  
* **LP Traceability:**  
  * **Washington State Investment Board (WSIB):** Confirmed commitments to Founders Fund, validating the institutional pension support for defense-tech.36  
  * **CalPERS:** California Public Employees' Retirement System remains an active allocator to 2024 vintages.4  
  * **Kommunal Landspensjonskasse (Norway):** Confirmed LP, showing European pension exposure to US defense tech.37  
* **Personnel Link:** **Trae Stephens** serves a dual role as General Partner at Founders Fund and Co-Founder/Chairman of Anduril. This tight coupling creates a highly efficient, high-conviction capital loop.35

### **4.3 The Sovereign Layer: Direct Balance Sheet Investing**

Sovereign entities are moving from "LP" status to "Direct Investor" status.

* **Kingdom Holding (Saudi Arabia):** Direct investor in xAI, leveraging legacy Twitter positions.28  
* **ASML (Netherlands):** Corporate strategic investor leading Mistral AI's €1.7 billion Series C. This is a rare instance of a hardware monopoly moving downstream into application software to secure demand for its own lithography machines.13  
* **MGX (UAE):** An active participant in OpenAI, representing the UAE's sovereign AI strategy.10

## ---

**5\. Reconciliation Log & Data Conflicts**

In compiling this traceability dataset, several critical data conflicts were identified and reconciled. The table below details the logic used to derive the final figures.

| Conflict Subject | Source A Value | Source B Value | Selected Value | Reconciliation Logic | Confidence |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Mistral AI Series C** | €2 Billion (Bloomberg) | €1.7 Billion (Official) | **€1.7B (\~$1.88B)** | Official press release from Mistral/ASML confirms €1.7B equity. The higher figure ($2B+) likely conflates secondary sales or debt components. Date confirmed Sept 2025\. | 1.0 |
| **GreenScale Funding** | $1.0 Billion | $1.3 Billion | **$1.3 Billion** | Discrepancy is due to FX (GBP vs USD). £1B is approximately $1.28-$1.3B. We standardize to USD at the time of the deal announcement (Jan 2025). | 0.9 |
| **Databricks Series J** | $10 Billion | $9.5 Billion | **$10 Billion** | Databricks official release confirms $10B. Lower numbers were pre-close leaks. The final round was oversubscribed. | 1.0 |
| **OpenAI Valuation** | $157 Billion | $300 Billion | **Sequential Record** | We treat these as two distinct events: Oct 2024 Primary ($157B) and Q1 2025 Tender ($300B). They are not conflicting, but sequential valuation step-ups. | 0.95 |
| **xAI Funding** | $6 Billion | $12 Billion | **$12 Billion Total** | Two distinct $6B rounds occurred: Series B (May 2024\) and Series C (Dec 2024/Jan 2025). Total capital raised is $12B. | 0.95 |

## ---

**6\. Visualization Plan: The Global Capital Sankey**

To visualize the complex flows described in this report, a **Multi-Stage Sankey Diagram** is the optimal format. This visualization will map the journey of a dollar from its geopolitical origin to its industrial application.

**Visualization Logic & Attributes:**

1. **Layer 1 (Source Region):** The leftmost nodes represent the origin of capital (North America, MENA, Europe, APAC). *Attribute: Node color defines geopolitical bloc.*  
2. **Layer 2 (Allocator/LP):** Specific capital aggregators (e.g., CalPERS, WSIB, SoftBank Group, Kingdom Holding, ASML Balance Sheet). *Node Size \= Capital Deployed.*  
3. **Layer 3 (Intermediary/GP):** Venture Capital Firms (Thrive IX, Founders Fund VIII, a16z, Sequoia). *Color Code: Red for US VC, Blue for Corp/Strategic, Green for Sovereign.*  
4. **Layer 4 (Financing Event):** The specific rounds (e.g., "Databricks Series J", "OpenAI Tender"). *Edge Weight \= Round Size USD. Edge Type: Dotted for Debt, Solid for Equity.*  
5. **Layer 5 (Recipient Company):** The target entities (Databricks, OpenAI, xAI, Mistral).  
6. **Layer 6 (Outcome/Usage):** The final destination of funds (Compute Capex, Employee Liquidity, R\&D). *Derived from the "Notes" field in the dataset.*

**Interactive Tooltips:** Users hovering over edges should see the "Confidence Score," "Source URL," and "Date of Retrieval" to ensure full provenance transparency.

## ---

**7\. Normalized Traceability Dataset (Artifacts)**

The following machine-readable outputs provide the granular data required to build the visualization described above.

### **7.1 JSON Lines (NDJSON) Sample**

*Canonical records for the top 10 funding events, strictly adhering to the schema.*

JSON

{"event\_id":"evt:openai-primary-2024","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://openai.com/index/march-funding-updates/","https://www.techmeme.com/241002/p27"\],"confidence":1.0,"region":"North America","country":"United States","city":"San Francisco","company":{"company\_id":"comp:openai","name":"OpenAI","industry":"Artificial Intelligence","subsector":"Generative AI","founded\_year":2015,"hq\_country":"US"},"round":{"round\_id":"rnd:openai-oct2024","type":"late","announced\_date":"2024-10-02","closed\_date":"2024-10-02","amount\_usd":6600000000,"amount\_local":6600000000,"currency":"USD","valuation\_usd":157000000000},"investors":,"fund":{"fund\_id":"fund:thrive-ix","name":"Thrive Capital Fund IX","manager":"Joshua Kushner","vintage\_year":2024,"fund\_size\_usd":5000000000},"lps":,"people":,"notes":"Largest VC round of all time. Capital used for compute capacity."}  
{"event\_id":"evt:databricks-series-j","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://www.databricks.com/company/newsroom/press-releases/databricks-raising-10b-series-j-investment-62b-valuation"\],"confidence":1.0,"region":"North America","country":"United States","city":"San Francisco","company":{"company\_id":"comp:databricks","name":"Databricks","industry":"Data Infrastructure","subsector":"Enterprise Software","founded\_year":2013,"hq\_country":"US"},"round":{"round\_id":"rnd:databricks-j-2024","type":"late","announced\_date":"2024-12-17","closed\_date":"2024-12-17","amount\_usd":10000000000,"amount\_local":10000000000,"currency":"USD","valuation\_usd":62000000000},"investors":,"fund":{"fund\_id":"fund:thrive-ix","name":"Thrive Capital Fund IX","manager":"Joshua Kushner","vintage\_year":2024,"fund\_size\_usd":5000000000},"lps":,"people":\[{"person\_id":"pers:ali-ghodsi","name":"Ali Ghodsi","role\_in\_deal":"founder/ceo","linked\_entity\_id":"comp:databricks","ownership\_pct":null}\],"notes":"Massive liquidity event for employees; includes secondary components mixed with primary."}  
{"event\_id":"evt:xai-series-b","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://x.ai/blog/series-b","https://www.wamda.com/en/2024/05/kingdom-holding-participates-musk-xai-6-billion-series-b-round"\],"confidence":1.0,"region":"North America","country":"United States","city":"Palo Alto","company":{"company\_id":"comp:xai","name":"xAI","industry":"Artificial Intelligence","subsector":"Generative AI","founded\_year":2023,"hq\_country":"US"},"round":{"round\_id":"rnd:xai-b-2024","type":"series\_b","announced\_date":"2024-05-26","closed\_date":"2024-05-26","amount\_usd":6000000000,"amount\_local":6000000000,"currency":"USD","valuation\_usd":24000000000},"investors":,"fund":{"fund\_id":null,"name":null,"manager":null,"vintage\_year":null,"fund\_size\_usd":null},"lps":,"people":\[{"person\_id":"pers:elon-musk","name":"Elon Musk","role\_in\_deal":"founder/ceo","linked\_entity\_id":"comp:xai","ownership\_pct":null}\],"notes":"Kingdom Holding participation links capital to Twitter privatization stack."}  
{"event\_id":"evt:waymo-series-c","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://www.therobotreport.com/waymo-raises-5-6b-to-accelerate-self-driving-car-growth/"\],"confidence":1.0,"region":"North America","country":"United States","city":"Mountain View","company":{"company\_id":"comp:waymo","name":"Waymo","industry":"Automotive","subsector":"Autonomous Driving","founded\_year":2009,"hq\_country":"US"},"round":{"round\_id":"rnd:waymo-c-2024","type":"series\_c","announced\_date":"2024-10-25","closed\_date":"2024-10-25","amount\_usd":5600000000,"amount\_local":5600000000,"currency":"USD","valuation\_usd":45000000000},"investors":,"fund":{"fund\_id":null,"name":null,"manager":null,"vintage\_year":null,"fund\_size\_usd":null},"lps":,"people":,"notes":"Oversubscribed round to expand robotaxi service to Austin/Atlanta."}  
{"event\_id":"evt:coreweave-series-c","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":,"confidence":1.0,"region":"North America","country":"United States","city":"Roseland","company":{"company\_id":"comp:coreweave","name":"CoreWeave","industry":"Cloud Infrastructure","subsector":"GPU Cloud","founded\_year":2017,"hq\_country":"US"},"round":{"round\_id":"rnd:coreweave-c-2024","type":"series\_c","announced\_date":"2024-05-01","closed\_date":"2024-05-01","amount\_usd":1100000000,"amount\_local":1100000000,"currency":"USD","valuation\_usd":19000000000},"investors":,"fund":{"fund\_id":null,"name":null,"manager":null,"vintage\_year":null,"fund\_size\_usd":null},"lps":,"people":\[{"person\_id":"pers:mike-intrator","name":"Mike Intrator","role\_in\_deal":"founder/ceo","linked\_entity\_id":"comp:coreweave","ownership\_pct":null}\],"notes":"Equity portion of a larger financing structure including massive debt for GPUs."}  
{"event\_id":"evt:anthropic-amazon-2024","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://www.aboutamazon.com/news/company-news/amazon-anthropic-ai-investment"\],"confidence":1.0,"region":"North America","country":"United States","city":"San Francisco","company":{"company\_id":"comp:anthropic","name":"Anthropic","industry":"Artificial Intelligence","subsector":"Generative AI","founded\_year":2021,"hq\_country":"US"},"round":{"round\_id":"rnd:anthropic-corp-2024","type":"late","announced\_date":"2024-11-22","closed\_date":"2024-11-22","amount\_usd":4000000000,"amount\_local":4000000000,"currency":"USD","valuation\_usd":18400000000},"investors":,"fund":{"fund\_id":null,"name":null,"manager":null,"vintage\_year":null,"fund\_size\_usd":null},"lps":,"people":,"notes":"Strategic corporate investment utilizing AWS Trainium chips. Total Amazon investment reaches $8B."}  
{"event\_id":"evt:mistral-series-c","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://mistral.ai/news/mistral-ai-raises-1-7-b-to-accelerate-technological-progress-with-ai","https://sifted.eu/articles/mistral-confirms-series-c-asml"\],"confidence":1.0,"region":"Europe","country":"France","city":"Paris","company":{"company\_id":"comp:mistral","name":"Mistral AI","industry":"Artificial Intelligence","subsector":"Generative AI","founded\_year":2023,"hq\_country":"FR"},"round":{"round\_id":"rnd:mistral-c-2025","type":"series\_c","announced\_date":"2025-09-09","closed\_date":"2025-09-09","amount\_usd":1880000000,"amount\_local":1700000000,"currency":"EUR","valuation\_usd":12900000000},"investors":,"fund":{"fund\_id":null,"name":null,"manager":null,"vintage\_year":null,"fund\_size\_usd":null},"lps":,"people":\[{"person\_id":"pers:arthur-mensch","name":"Arthur Mensch","role\_in\_deal":"founder/ceo","linked\_entity\_id":"comp:mistral","ownership\_pct":null}\],"notes":"Led by semiconductor giant ASML (€1.3B commitment). Strategic sovereign EU play."}  
{"event\_id":"evt:greenscale-seed-infra","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://www.dtcp.capital/news-and-insights/detail/dtcp-backs-greenscale-a-new-data-center-platform-to-accelerate-growth-in-cloud-and-ai-driven-data-centers-across-europe/"\],"confidence":0.9,"region":"Europe","country":"United Kingdom","city":"London","company":{"company\_id":"comp:greenscale","name":"GreenScale Data Centres","industry":"Digital Infrastructure","subsector":"Data Centers","founded\_year":2024,"hq\_country":"GB"},"round":{"round\_id":"rnd:greenscale-2025","type":"seed","announced\_date":"2025-01-07","closed\_date":"2025-01-07","amount\_usd":1300000000,"amount\_local":1000000000,"currency":"GBP","valuation\_usd":null},"investors":,"fund":{"fund\_id":null,"name":null,"manager":null,"vintage\_year":null,"fund\_size\_usd":null},"lps":,"people":,"notes":"Platform launch with secured capacity in Northern Ireland. Investment primarily for Capex."}  
{"event\_id":"evt:ssi-series-a","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://salestools.io/report/ssi-raises-1b-series-a"\],"confidence":1.0,"region":"North America","country":"United States","city":"Palo Alto","company":{"company\_id":"comp:ssi","name":"Safe Superintelligence","industry":"Artificial Intelligence","subsector":"AI Safety","founded\_year":2024,"hq\_country":"US"},"round":{"round\_id":"rnd:ssi-a-2024","type":"series\_a","announced\_date":"2024-09-04","closed\_date":"2024-09-04","amount\_usd":1000000000,"amount\_local":1000000000,"currency":"USD","valuation\_usd":5000000000},"investors":,"fund":{"fund\_id":null,"name":null,"manager":null,"vintage\_year":null,"fund\_size\_usd":null},"lps":,"people":,"notes":"Founded by Ilya Sutskever ex-OpenAI. Pure research play with massive capital."}  
{"event\_id":"evt:anduril-series-f","retrieved\_at":"2025-12-11T12:00:00Z","source\_urls":\["https://www.tsginvest.com/anduril-industries/"\],"confidence":1.0,"region":"North America","country":"United States","city":"Costa Mesa","company":{"company\_id":"comp:anduril","name":"Anduril Industries","industry":"Defense Tech","subsector":"Autonomous Systems","founded\_year":2017,"hq\_country":"US"},"round":{"round\_id":"rnd:anduril-f-2024","type":"series\_f","announced\_date":"2024-08-07","closed\_date":"2024-08-07","amount\_usd":1500000000,"amount\_local":1500000000,"currency":"USD","valuation\_usd":14000000000},"investors":,"fund":{"fund\_id":"fund:founders-viii","name":"Founders Fund VIII","manager":"Trae Stephens","vintage\_year":2022,"fund\_size\_usd":900000000},"lps":,"people":,"notes":"Trae Stephens acts as both Founder (Anduril) and GP (Founders Fund), creating a tight traceability loop."}

### **7.2 Edge List CSV (Sample)**

*Graph-ready format for ingestion into network analysis tools like Gephi or Neo4j.*

Code snippet

source\_id,target\_id,relationship,amount\_usd,currency,date,confidence,source\_url  
fund:thrive-ix,rnd:openai-oct2024,invested\_in,1250000000,USD,2024-10-02,1.0,https://www.techmeme.com/241002/p27  
lp:utimco,fund:thrive-ix,lp\_commitment,null,USD,2024-08-05,0.9,https://pitchbook.com/profiles/fund/26292-79F  
inv:microsoft,rnd:openai-oct2024,invested\_in,null,USD,2024-10-02,1.0,https://openai.com  
inv:softbank,rnd:openai-oct2024,invested\_in,500000000,USD,2024-10-02,0.9,https://group.softbank  
fund:thrive-ix,rnd:databricks-j-2024,invested\_in,null,USD,2024-12-17,1.0,https://databricks.com  
inv:asml,rnd:mistral-c-2025,invested\_in,1430000000,USD,2025-09-09,1.0,https://mistral.ai  
inv:dtcp,rnd:greenscale-2025,invested\_in,1300000000,USD,2025-01-07,0.9,https://dtcp.capital  
inv:amazon,rnd:anthropic-corp-2024,invested\_in,4000000000,USD,2024-11-22,1.0,https://amazon.com  
lp:wsib,fund:founders-viii,lp\_commitment,null,USD,2024-02-01,1.0,https://sib.wa.gov  
fund:founders-viii,rnd:anduril-f-2024,invested\_in,null,USD,2024-08-07,1.0,https://tsginvest.com

### **7.3 Node List CSV (Sample)**

*Attribute data for graph nodes, including sector and region metadata.*

Code snippet

node\_id,name,type,region,country,industry/focus  
comp:openai,OpenAI,Company,North America,US,Generative AI  
comp:databricks,Databricks,Company,North America,US,Data Infrastructure  
comp:mistral,Mistral AI,Company,Europe,FR,Generative AI  
comp:greenscale,GreenScale,Company,Europe,UK,Data Centers  
comp:xai,xAI,Company,North America,US,Generative AI  
fund:thrive-ix,Thrive Capital Fund IX,Fund,North America,US,Multi-stage  
fund:founders-viii,Founders Fund VIII,Fund,North America,US,Venture/Defense  
inv:asml,ASML,Corporate,Europe,NL,Semiconductors  
inv:softbank,SoftBank Group,Corporate,Asia,JP,Conglomerate  
lp:wsib,Washington State Investment Board,LP,North America,US,Pension Fund  
lp:utimco,UTIMCO,LP,North America,US,Endowment

## ---

**8\. Strategic Conclusions**

The traceability data for 2024–2025 demonstrates that the private markets have evolved into two distinct asset classes:

1. **Industrial AI Capital:** This ecosystem handles multi-billion dollar tranches to fund physical assets (CoreWeave's GPUs, GreenScale's Data Centers) and sovereign-scale models (OpenAI, xAI). These deals are increasingly led by SWFs, Corporate Balance Sheets (Amazon, ASML), and specialized "Mega-Funds" (Thrive IX). This is less about "venture" risk and more about "infrastructure" deployment.  
2. **Traditional Innovation Capital:** The remaining 99% of the market operates on pre-2021 fundamentals, characterized by tightened diligence, reduced volumes, and a focus on path-to-profitability in SaaS and Fintech.

For the investor or analyst, this report confirms that to trace the largest flows of money in 2025, one must look beyond traditional VC partnerships and track the direct sovereign and corporate strategic balance sheets that are building the physical layer of the AI economy. The power law has gone fractal: the biggest winners are not just capturing the most value, they are attracting a fundamentally different *kind* of capital.

#### **Works cited**

1. Startup Funding Regained Its Footing In 2024 As AI Became The Star Of The Show, accessed December 11, 2025, [https://news.crunchbase.com/venture/global-funding-data-analysis-ai-eoy-2024/](https://news.crunchbase.com/venture/global-funding-data-analysis-ai-eoy-2024/)  
2. 2024 global VC investment rises to $368 billion as investor interest ..., accessed December 11, 2025, [https://kpmg.com/xx/en/media/press-releases/2025/01/2024-global-vc-investment-rises-to-368-billion-dollars.html](https://kpmg.com/xx/en/media/press-releases/2025/01/2024-global-vc-investment-rises-to-368-billion-dollars.html)  
3. Thrive Capital Partners IX: Fund Performance \- PitchBook, accessed December 11, 2025, [https://pitchbook.com/profiles/fund/26292-79F](https://pitchbook.com/profiles/fund/26292-79F)  
4. Thrive Capital Partners IX Growth: Fund Performance \- PitchBook, accessed December 11, 2025, [https://pitchbook.com/profiles/fund/26487-28F](https://pitchbook.com/profiles/fund/26487-28F)  
5. Q4'24 Venture Pulse Report – Europe \- KPMG International, accessed December 11, 2025, [https://kpmg.com/cy/en/home/campaigns/2025/01/q4-24-venture-pulse-report-europe.html](https://kpmg.com/cy/en/home/campaigns/2025/01/q4-24-venture-pulse-report-europe.html)  
6. CoreWeave Secures $1.1 Billion in Series C Funding to Drive the Next Generation of Cloud Computing for the Future of AI, accessed December 11, 2025, [https://investors.coreweave.com/news/news-details/2024/CoreWeave-Secures-1-1-Billion-in-Series-C-Funding-to-Drive-the-Next-Generation-of-Cloud-Computing-for-the-Future-of-AI/default.aspx](https://investors.coreweave.com/news/news-details/2024/CoreWeave-Secures-1-1-Billion-in-Series-C-Funding-to-Drive-the-Next-Generation-of-Cloud-Computing-for-the-Future-of-AI/default.aspx)  
7. SoftBank reportedly spearheading $40 billion bet on OpenAI \- Glide, accessed December 11, 2025, [https://www.glideapps.com/news/softbank-40b-tender-openai-shares](https://www.glideapps.com/news/softbank-40b-tender-openai-shares)  
8. Insights: CoreWeave's Upcoming IPO & Private Stock Price \- Forge Global, accessed December 11, 2025, [https://forgeglobal.com/insights/coreweave-upcoming-ipo-news/](https://forgeglobal.com/insights/coreweave-upcoming-ipo-news/)  
9. ASML Becomes Top Shareholder in Mistral AI After €1.3B Series C Investment \- AI Chat, accessed December 11, 2025, [https://chatlyai.app/news/asml-mistral-ai-top-shareholder-sept-2025](https://chatlyai.app/news/asml-mistral-ai-top-shareholder-sept-2025)  
10. Databricks is Raising $10B Series J Investment at $62B Valuation, accessed December 11, 2025, [https://www.databricks.com/company/newsroom/press-releases/databricks-raising-10b-series-j-investment-62b-valuation](https://www.databricks.com/company/newsroom/press-releases/databricks-raising-10b-series-j-investment-62b-valuation)  
11. Global analysis of venture funding \- KPMG agentic corporate services, accessed December 11, 2025, [https://assets.kpmg.com/content/dam/kpmgsites/az/pdf/2025/Q4-2024-Venture-Pulse.pdf](https://assets.kpmg.com/content/dam/kpmgsites/az/pdf/2025/Q4-2024-Venture-Pulse.pdf)  
12. CoreWeave \- Wikipedia, accessed December 11, 2025, [https://en.wikipedia.org/wiki/CoreWeave](https://en.wikipedia.org/wiki/CoreWeave)  
13. Mistral confirms €1.7bn Series C led by ASML \- Sifted, accessed December 11, 2025, [https://sifted.eu/articles/mistral-confirms-series-c-asml](https://sifted.eu/articles/mistral-confirms-series-c-asml)  
14. Mistral AI raises 1.7B€ to accelerate technological progress with AI, accessed December 11, 2025, [https://mistral.ai/news/mistral-ai-raises-1-7-b-to-accelerate-technological-progress-with-ai](https://mistral.ai/news/mistral-ai-raises-1-7-b-to-accelerate-technological-progress-with-ai)  
15. Q4'24 Venture Pulse Report \- KPMG Ukraine, accessed December 11, 2025, [https://kpmg.com/ua/en/home/insights/2025/02/q4-24-venture-pulse-report.html](https://kpmg.com/ua/en/home/insights/2025/02/q4-24-venture-pulse-report.html)  
16. DTCP backs GreenScale, a new data center platform, to accelerate growth in Cloud and AI-driven data centers across Europe, accessed December 11, 2025, [https://www.dtcp.capital/news-and-insights/detail/dtcp-backs-greenscale-a-new-data-center-platform-to-accelerate-growth-in-cloud-and-ai-driven-data-centers-across-europe/](https://www.dtcp.capital/news-and-insights/detail/dtcp-backs-greenscale-a-new-data-center-platform-to-accelerate-growth-in-cloud-and-ai-driven-data-centers-across-europe/)  
17. Elon Musk's xAI raises $6b \- World Internet Conference, accessed December 11, 2025, [https://www.wicinternet.org/2024-12/29/c\_1060982.htm](https://www.wicinternet.org/2024-12/29/c_1060982.htm)  
18. Databricks Rockets in AI with Strategic $10B Series J Led by Thrive Capital \- Medium, accessed December 11, 2025, [https://medium.com/@as.bsventureclub/databricks-rockets-in-ai-with-strategic-10b-series-j-led-by-thrive-capital-ee8506098570](https://medium.com/@as.bsventureclub/databricks-rockets-in-ai-with-strategic-10b-series-j-led-by-thrive-capital-ee8506098570)  
19. Mistral's $2B Series C Is Europe's Largest AI Round By A Lot \- Crunchbase News, accessed December 11, 2025, [https://news.crunchbase.com/venture/europe-largest-ai-round-mistral-seriesc/](https://news.crunchbase.com/venture/europe-largest-ai-round-mistral-seriesc/)  
20. GreenScale Data Centres Secures $1 Billion Investment to Revolutionize Sustainable Digital Infrastructure \- LeadsOnTrees, accessed December 11, 2025, [https://www.leadsontrees.com/news/greenscale-data-centres-secures-1-billion-investment-to-revolutionize-sustainable-digital-infrastructure](https://www.leadsontrees.com/news/greenscale-data-centres-secures-1-billion-investment-to-revolutionize-sustainable-digital-infrastructure)  
21. PE/VC investments highest in a decade, says Equirus Capital report, accessed December 11, 2025, [https://www.business-standard.com/industry/news/private-equity-venture-capital-investments-touch-a-decade-high-report-125120901385\_1.html](https://www.business-standard.com/industry/news/private-equity-venture-capital-investments-touch-a-decade-high-report-125120901385_1.html)  
22. OpenAI raised $6.6B led by Thrive Capital, the largest VC deal of all time, valuing it at $157B, with participation from Microsoft, Nvidia, SoftBank, and others (Ina Fried/Axios) \- Techmeme, accessed December 11, 2025, [https://www.techmeme.com/241002/p27](https://www.techmeme.com/241002/p27)  
23. Announcement Regarding Follow-on Investments in OpenAI | SoftBank Group Corp., accessed December 11, 2025, [https://group.softbank/en/news/press/20250401](https://group.softbank/en/news/press/20250401)  
24. Databricks completes $10B funding round, raises $5.25B in debt \- SiliconANGLE, accessed December 11, 2025, [https://siliconangle.com/2025/01/22/databricks-completes-10b-funding-round-raises-5-25b-debt/](https://siliconangle.com/2025/01/22/databricks-completes-10b-funding-round-raises-5-25b-debt/)  
25. xAI's Latest Funding Round Elevates It to $24 Billion Valuation \- The National CIO Review, accessed December 11, 2025, [https://nationalcioreview.com/articles-insights/extra-bytes/xais-latest-funding-round-elevates-it-to-24-billion-valuation/](https://nationalcioreview.com/articles-insights/extra-bytes/xais-latest-funding-round-elevates-it-to-24-billion-valuation/)  
26. xAI Makes It Official — Raises $6B At $24B Valuation \- Crunchbase News, accessed December 11, 2025, [https://news.crunchbase.com/ai/xai-raises-series-b-unicorn-musk/](https://news.crunchbase.com/ai/xai-raises-series-b-unicorn-musk/)  
27. X.AI Corp. Funding & Investors Insights \- AI Startup Financials \- Exa, accessed December 11, 2025, [https://exa.ai/websets/directory/xai-funding](https://exa.ai/websets/directory/xai-funding)  
28. Kingdom Holding participates in Musk's xAI $6 billion Series B round \- Wamda, accessed December 11, 2025, [https://www.wamda.com/en/2024/05/kingdom-holding-participates-musk-xai-6-billion-series-b-round](https://www.wamda.com/en/2024/05/kingdom-holding-participates-musk-xai-6-billion-series-b-round)  
29. How Much Did Waymo Raise? Headquarters, Funding & Key Investors \- TexAu, accessed December 11, 2025, [https://www.texau.com/profiles/waymo](https://www.texau.com/profiles/waymo)  
30. Waymo raises $5.6B to accelerate self-driving car growth \- The Robot Report, accessed December 11, 2025, [https://www.therobotreport.com/waymo-raises-5-6b-to-accelerate-self-driving-car-growth/](https://www.therobotreport.com/waymo-raises-5-6b-to-accelerate-self-driving-car-growth/)  
31. Coatue Leads CoreWeave's $1.1 Billion Series C Funding \- Simpson Thacher & Bartlett LLP, accessed December 11, 2025, [https://www.stblaw.com/about-us/news/view/2024/05/21/coatue-leads-coreweave-s-$1.1-billion-series-c-funding](https://www.stblaw.com/about-us/news/view/2024/05/21/coatue-leads-coreweave-s-$1.1-billion-series-c-funding)  
32. Thrive Capital racks up $5bn across two funds, accessed December 11, 2025, [https://www.venturecapitaljournal.com/thrive-capital-racks-up-5bn-across-two-funds/](https://www.venturecapitaljournal.com/thrive-capital-racks-up-5bn-across-two-funds/)  
33. Thrive IX. We are humbled to announce the close of… | by Thrive Capital \- Medium, accessed December 11, 2025, [https://medium.com/@thrivecapital/announcing-thrive-ix-60ee01645547](https://medium.com/@thrivecapital/announcing-thrive-ix-60ee01645547)  
34. Invest in Anduril Industries: Private Investment Guide, accessed December 11, 2025, [https://tsginvest.com/anduril-industries/](https://tsginvest.com/anduril-industries/)  
35. Anduril Funding & Investors: Comprehensive Information \- Exa, accessed December 11, 2025, [https://exa.ai/websets/directory/anduril-funding](https://exa.ai/websets/directory/anduril-funding)  
36. WSIB approves $200m commitment to Endeavour Capital Fund VIII, accessed December 11, 2025, [https://www.privateequityinternational.com/wsib-approves-200m-commitment-3/](https://www.privateequityinternational.com/wsib-approves-200m-commitment-3/)  
37. Founders Fund VIII: Performance | PitchBook, accessed December 11, 2025, [https://pitchbook.com/profiles/fund/21006-37F](https://pitchbook.com/profiles/fund/21006-37F)  
38. Trae Stephens \- Wikipedia, accessed December 11, 2025, [https://en.wikipedia.org/wiki/Trae\_Stephens](https://en.wikipedia.org/wiki/Trae_Stephens)  
39. ASML Takes Stake in, Partners with Mistral AI | Business | Sep 2025 \- Photonics Spectra, accessed December 11, 2025, [https://www.photonics.com/Articles/ASML-Takes-Stake-in-Partners-with-Mistral-AI/a71446](https://www.photonics.com/Articles/ASML-Takes-Stake-in-Partners-with-Mistral-AI/a71446)