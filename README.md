# 🌊 Diluvium
**AI-Integrated Early Warning System for Hydrometeorological Disasters in Jakarta**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastMCP](https://img.shields.io/badge/MCP-FastMCP-purple)
![Gemini](https://img.shields.io/badge/AI-Gemini%203%20Flash-orange)
![Status](https://img.shields.io/badge/Status-Prototype%20In%20Progress-green)

## 📖 Overview
**Diluvium** is an automated, intelligent early warning system designed for civilians living in flood-prone areas of DKI Jakarta. Instead of relying on static water-level thresholds or a single monolithic LLM that risks hallucinating numbers, Diluvium uses a **Modular Multi-Agent Pipeline** built on the **Model Context Protocol (MCP)** and **FastMCP**.

The system continuously aggregates real-time rainfall telemetry from **BMKG** and river water levels from **BPBD DKI Jakarta (Pantau Banjir AWLR)**, computes hyper-localized flood arrival times and inundation radii using deterministic & ML models alongside **GeoPandas**, and audits every prediction against Jakarta's official **Siaga 1–4 thresholds** before dispatching verified alerts via **Telegram** and **Discord**.

---

## 🏗️ System Architecture (Helicopter View)

```mermaid
flowchart LR
    subgraph S1["1. Data Ingestion"]
        BMKG["Data Terbuka BMKG"] --> IngestAgent["Ingestion Agent"]
        BPBD["BPBD DKI AWLR"] --> IngestAgent
    end

    subgraph S2["2. AI Orchestration"]
        IngestAgent --> FastMCP["FastMCP Server"]
        FastMCP <--> GeminiOrch["Gemini 3 Flash"]
    end

    subgraph S3["3. Calculation Engine"]
        GeminiOrch <--> CalcAgent["Calculation Agent<br/>(GeoPandas + ML)"]
        GeoData[("InaRISK & Jakarta<br/>Open Data")] --- CalcAgent
    end

    subgraph S4["4. Verification & Critic"]
        GeminiOrch --> VerifyAgent["Verification Agent<br/>(Siaga 1-4 Audit)"]
        GeminiOrch -.-> Fallback["Non-AI Fallback"]
    end

    subgraph S5["5. Alert Delivery"]
        VerifyAgent --> Gateways["Telegram & Discord"]
        Fallback -.-> Gateways
        Gateways --> Civilians["Jakarta Civilians"]
    end
```

---

## 📂 Project Structure

```text
Diluvium/
├── data/
│   ├── raw/                  # Raw Jakarta Open Data & InaRISK datasets
│   └── processed/            # Cleaned GeoJSON / Parquet spatial caches
├── models/                   # Saved ML model weights (.joblib / .pt)
├── src/
│   ├── config.py             # Environment variables & API configuration
│   ├── schemas.py            # Shared Pydantic data validation contracts
│   ├── mcp_server.py         # Central FastMCP server exposing agent tools
│   ├── ingestion/            # Agent 1: BMKG & BPBD API clients + retry logic
│   ├── calculation/          # Agent 2: GeoPandas spatial susceptibility & ML models
│   ├── verification/         # Agent 3: Siaga 1-4 threshold critic & bot notifiers
│   ├── orchestrator/         # Gemini 3 Flash orchestrator & non-AI fallback script
│   └── gui/                  # Internal Admin/Developer Monitoring Web GUI
├── tests/                    # Unit & End-to-End (E2E) test suites
├── .env.example              # Template for API keys and secrets
├── requirements.txt          # Locked Python dependencies
└── README.md
```

---


---

## 👥 Team & Responsibilities (RPL)
| Member | Role | Owned Epics |
| :--- | :--- | :--- |
| **Radya Gardian Pranoto** | DevOps, FastMCP & QA | *Project & Environment Prep*, *Quality Control & Deployment*, FastMCP Integration (`KAN-20`) |
| **Sutan** | Data Pipeline & AI Infrastructure | *Data Ingestion* (`KAN-12`), *AI Orchestration* |
| **Irgy** | Core Logic & Verification | *Calculation & Integration*, *Verification & Alert System* |