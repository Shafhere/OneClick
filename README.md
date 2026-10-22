# OneClick – AI-Powered Company Research Platform

## 📌 Project Overview

OneClick is an AI-powered company research platform that collects publicly accessible website content, analyzes it using Large Language Models (LLMs), and organizes the results into a structured company research report.

The goal is to help users understand a company's products, services, business information, and other important details without manually browsing multiple pages.

## 🎯 Main Features

- **Website Crawling:** Collects readable content from company websites.
- **AI-Powered Analysis:** Uses an LLM to extract and summarize relevant business information.
- **Products and Services:** Organizes information about products and services.
- **Company Details:** Presents company information in a structured format.
- **Evidence and Sources:** Displays collected sources to help users verify extracted information.
- **RAG Chatbot:** Allows users to ask questions based on the collected company information.
- **Interactive Dashboard:** Presents research findings through a Streamlit interface.
- **Crawling Diagnostics:** Provides more useful feedback when a website cannot be analyzed.

## 🛠️ Technology Stack

- Python
- FastAPI – Backend API
- Streamlit – Frontend dashboard
- Groq API – LLM inference
- ChromaDB – Vector storage for retrieval-augmented generation (RAG)
- Requests – HTTP requests
- Beautiful Soup – HTML parsing and content extraction
- lxml – HTML/XML parsing
- Playwright – Optional JavaScript-rendering fallback

## 🏗️ Architecture

The general workflow is:

1. User submits a company website.
2. The backend validates the URL.
3. The crawler discovers accessible pages and extracts readable content.
4. The collected content is processed and analyzed by an LLM.
5. Relevant content is stored and retrieved for RAG-based question answering.
6. The frontend displays the company research report and supporting sources.
7. Users can ask follow-up questions through the RAG chatbot.

## 📁 Project Structure

The expected structure includes:

```text
OneClick/
├── backend/
│   └── app/
│       ├── core/
│       │   └── crawler.py
│       └── main.py
├── frontend/
│   └── app.py
├── requirements.txt
├── README.md
└── .env
```

The actual structure may contain additional modules for analysis, embeddings, database operations, configuration, and API routes.

## ⚙️ Environment Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd OneClick
```

Replace the placeholder with the actual repository URL.

### 2. Create and activate a virtual environment

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If Playwright is used for JavaScript-rendered websites, install its browser separately:

```bash
pip install playwright
python -m playwright install chromium
```

Playwright is optional unless the application configuration or dependency setup requires it.

### 4. Configure environment variables

Create a `.env` file using the variables required by the application.

For example:

```env
GROQ_API_KEY=your_groq_api_key
```

Use the exact variable names expected by the project's configuration. Never commit API keys, passwords, or other secrets to GitHub.

## ▶️ Running the Application

Start the FastAPI backend from the project root using the entry point configured in the repository.

For example, if the application is exposed as `app` in `backend/app/main.py`:

```bash
uvicorn backend.app.main:app --reload
```

Start the Streamlit frontend in a separate terminal:

```bash
streamlit run frontend/app.py
```

The actual commands may need adjustment depending on the repository's Python package structure and current configuration.

## 🕷️ Website Crawling and Limitations

Some websites may fail to provide readable content because of:

- JavaScript-rendered pages
- Bot protection or rate limiting
- Authentication requirements
- Network errors or timeouts
- Website-specific crawling restrictions
- Empty or inaccessible pages

The updated crawler is intended to improve handling of robots.txt responses, redirects between `www` and non-`www` hosts, and pages that require JavaScript rendering.

However, not every website can be crawled successfully. Explicit website restrictions must be respected, and inaccessible or protected content should not be treated as successfully collected.

## 📊 Dashboard

The improved dashboard is organized into the following sections:

1. **Overview** – Company summary and research coverage.
2. **Products & Services** – Extracted products and service information.
3. **Company Details** – Additional company information and identified gaps.
4. **Evidence & Sources** – Source pages and supporting evidence.
5. **RAG Chat** – Questions and answers grounded in collected company content.

The dashboard aims to improve readability, spacing, navigation, and the presentation of detailed research findings.

## 🧪 Testing Checklist

Before considering the application ready for release, test:

- [ ] Backend starts without errors.
- [ ] Streamlit frontend starts successfully.
- [ ] A normal company website can be analyzed.
- [ ] Redirects between `www` and non-`www` hosts work correctly.
- [ ] Websites with limited readable HTML return useful diagnostics.
- [ ] JavaScript-rendered pages are tested when Playwright is enabled.
- [ ] Products and services are displayed correctly.
- [ ] Company details and source evidence are visible.
- [ ] RAG answers are grounded in collected content.
- [ ] Missing or inaccessible content is handled gracefully.
- [ ] API keys and secrets are excluded from Git commits.

## 🚀 Current Development Status

The recent update includes an improved crawler implementation and a redesigned Streamlit dashboard.

The next steps are to integrate the files into the actual repository, verify dependencies, run the application, and test the complete workflow.

The following items still need verification:

- The final `requirements.txt` dependency list.
- Compatibility between the updated frontend and the actual backend endpoints.
- End-to-end crawling, analysis, and RAG functionality.
- Git status, commit history, and whether the latest changes have been pushed to GitHub.

## 🔒 Security

- Keep `.env` and API keys private.
- Do not upload virtual environments or unnecessary generated files.
- Validate submitted URLs before crawling.
- Avoid accessing private network resources or restricted website content.
- Follow applicable website crawling policies and restrictions.

## 📌 Project Goal

Build a reliable, easy-to-use AI company research assistant that converts publicly accessible website information into structured reports, verifiable evidence, and conversational insights.
