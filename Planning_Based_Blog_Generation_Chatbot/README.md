# 🧠 Planning-Based AI Blog Generation Agent

## 🚀 Overview

This project is an advanced AI-powered system that generates high-quality technical blogs using a **planning-based workflow** instead of a single LLM call.

It leverages a structured pipeline with components like **router, orchestrator, workers, and reducer** to create well-organized, research-backed blog content with relevant images.

---

## 🎯 Key Features

* 🧭 **Dynamic Routing**

  * Uses an LLM-based router to decide whether external research is required

* 🔍 **Research-Driven Generation (Agentic RAG)**

  * Integrates external knowledge using Tavily API for accurate and up-to-date content

* 🧩 **Planning-Based Architecture**

  * Breaks blog into multiple structured tasks before generation

* ⚡ **Parallel Section Generation**

  * Uses multiple workers to generate sections concurrently (fan-out pattern)

* 🧠 **Structured Output (Pydantic)**

  * Ensures reliable and consistent data flow across all stages

* 🖼️ **Automated Image Generation**

  * Generates and inserts relevant diagrams using Google Gemini

* 🔗 **Citation-Based Content**

  * Ensures factual correctness with proper source linking

---

## 🏗️ System Architecture

```
User Input (Topic)
        ↓
     Router
        ↓
 (Research Optional)
        ↓
  Orchestrator (Planner)
        ↓
   Parallel Workers
        ↓
      Reducer
 (Merge + Images)
        ↓
   Final Blog Output
```

---

## ⚙️ Tech Stack

* **Language:** Python
* **Frameworks:** LangGraph, LangChain
* **LLM:** OpenAI (GPT-4.1-mini)
* **Search API:** Tavily
* **Image Generation:** Google Gemini
* **Validation:** Pydantic
* **Deployment:** Docker, AWS ECS

---

## 🧠 Core Concepts

* Agentic Workflows
* Planning-Based AI Systems
* Retrieval-Augmented Generation (RAG)
* Parallel Processing (Fan-out / Fan-in)
* Structured Output Validation
* Dynamic Decision Making

---

## 🔄 How It Works

1. **Router** analyzes the topic and decides:

   * Whether research is needed
   * Which mode to use (closed_book / hybrid / open_book)

2. **Research Node**

   * Fetches relevant information using Tavily API (if required)

3. **Orchestrator (Planner)**

   * Creates a structured plan with multiple tasks (sections)

4. **Workers**

   * Generate blog sections in parallel based on assigned tasks

5. **Reducer**

   * Merges all sections into a single blog
   * Adds images using placeholder-based insertion

6. **Final Output**

   * A complete, structured, and well-formatted blog with citations and visuals

---

## 📂 Project Structure

```
├── router
├── research
├── orchestrator
├── worker
├── reducer
├── schemas (Pydantic models)
├── main graph (LangGraph pipeline)
```

---

## 🚀 Setup Instructions

### 1. Clone Repository

```
git clone https://github.com/your-username/repo-name.git
cd repo-name
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

### 3. Set Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your_key
TAVILY_API_KEY=your_key
GOOGLE_API_KEY=your_key
```

### 4. Run the Project

```
python main.py
```

---

## 📈 Use Cases

* Automated blog generation
* AI content pipelines
* Developer documentation
* Technical writing automation

---

## ⚠️ Limitations

* Dependent on external APIs (OpenAI, Tavily, Gemini)
* LLM latency can affect performance
* Recency filtering may not handle historical queries perfectly

---

## 🔥 Highlights

* Not a simple LLM call — uses **multi-step reasoning pipeline**
* Supports **dynamic routing and decision-making**
* Designed for **scalability and modularity**

---

## 👨‍💻 Author

**Gaurav**
