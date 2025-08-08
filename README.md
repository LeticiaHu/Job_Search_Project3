# Job Search Analyzer

## Project Description

This project is a Job Search Assistant that uses Gradio and Ollama as an interactive  AI-powered web applicationdesigned to help users explore career opportunities in the U.S government job market. 
The app combines public data from the USAJobs API with Ollama's local LLMs, creating a smart, privacy-preserving assistant that enhances the job search experience.

Users can receive personalized job title recommendations based on their skills, browse real-time job postings by category, analyze job descriptions using large language models (LLMs), and even get resume improvement suggestions tailored to the specific role they're targeting.

This project showcases the practical integration of open-source LLMs with government APIs and user-friendly UI frameworks.


## 🎯 Purpose

The primary goals of this project are to:

- Assist users in identifying job opportunities that match their skills and interests

- Simplify access to federal job listings using the USAJobs API

- Leverage AI (Ollama + local LLMs) to generate meaningful job analysis and resume suggestions

- Provide a private, fast, and transparent alternative to cloud-based AI tools

- Demonstrate full-stack AI app development with Gradio, Python, REST APIs, and local LLMs


## Setup

1. Clone this repository
2. Create and activate a virtual environment:
python -m venv venv source venv/bin/activate # On Windows, use: venv\Scripts\activate
3. Install dependencies:
pip install -r requirements.txt
4. Copy `.env.example` to `.env` and add your NYC API key
5. Run the application:
python Job_nyc.py

##  Getting the API Key for USAJOBS

To use this app, you need a free API key from USAJOBS.

1. Go to the official USAJOBS Developer website:
👉 https://developer.usajobs.gov/api-reference/

2. Scroll to the “Get Started” section and click “Request an API Key”.

3. Create an account (or log in if you already have one).

4. Once logged in, navigate to My API Keys.

5. Copy your Authorization-Key and also note your User-Agent (usually your email).

6. Add both values to your .env file 


## Requirements

- Python 3.7+
- Ollama (with mistral model pulled)
- NYC_JOBS_API


## 📘 Credits

Code structure inspired by materials from Prof. Mr. Avinash Jairam, CIS 9660 - Data Mining for Business Analytics course.
ChatGPT by OpenAI was used to clarify Python syntax, assist with implementation strategies, and explore alternatives for data preprocessing and modeling.
All results, analysis, and business interpretations are original and completed independently.