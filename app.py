import streamlit as st
import requests

# Global data stores
current_postings = []
job_data = {}

# ---------- Skill-based Job Recommendations ----------
st.title("🧠 Job Search Assistant with Ollama")
with st.expander("📘 How to Use This App", expanded=True):
    st.markdown("""
    1. Enter your skills to get job title suggestions.
    2. Enter a job category (e.g. finance) to load real job postings.
    3. Analyze the job or generate resume tips using AI (Ollama).
    """)

st.markdown("### 🎯 Get Job Recommendations Based on Your Skills")
skills = st.text_area("Enter your skills", placeholder="e.g. Python, Excel, data analysis")
if st.button("🔍 Suggest Jobs"):
    prompt = f"""You are a career advisor. Based on these skills, suggest 3–5 job titles:

Skills: {skills}
"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "tinyllama", "prompt": prompt, "stream": False}
        )
        result = response.json().get("response", "⚠️ No response from Ollama.")
        st.markdown("#### 📌 Recommended Jobs")
        st.markdown(result)
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ---------- Job Search ----------
st.markdown("---")
st.markdown("### 📥 Load Job Postings by Category")
section = st.text_input("Enter job category (e.g. finance, tech)")
if st.button("📥 Load Jobs"):
    params = {"ResultsPerPage": 5}
    try:
        result = requests.get(f"https://data.usajobs.gov/api/search?Keyword={section}", params=params).json()
        current_postings.clear()
        job_data.clear()

        current_postings.extend(result.get("SearchResult", {}).get("SearchResultItems", []))

        if not current_postings:
            st.warning("⚠️ No jobs found.")
        else:
            st.markdown("## 🧾 Top Job Listings")
            job_titles = []
            for i, job in enumerate(current_postings, 1):
                descriptor = job["MatchedObjectDescriptor"]
                title = descriptor.get("PositionTitle", "N/A")
                location = descriptor.get("PositionLocationDisplay", "N/A")
                summary = descriptor.get("UserArea", {}).get("Details", {}).get("JobSummary", "No summary")
                url = descriptor.get("PositionURI", "#")

                job_titles.append(title)
                job_data[title] = summary

                st.markdown(f"**{i}. {title}**  \n📍 {location}  \n📄 {summary}  \n🔗 [View Posting]({url})")
    except Exception as e:
        st.error(f"❌ Failed to load jobs: {e}")

# ---------- Job Analysis ----------
if job_data:
    st.markdown("---")
    st.markdown("### 🔎 Analyze a Job Posting")
    selected_job = st.selectbox("Select a Job", list(job_data.keys()))
    analysis_type = st.selectbox("Select Analysis Type", ["summary", "qualifications", "salary"])

    if st.button("Analyze Selected Job"):
        for job in current_postings:
            descriptor = job.get("MatchedObjectDescriptor", {})
            if descriptor.get("PositionTitle") == selected_job:
                try:
                    prompt = f"Give me the {analysis_type} for the following job:\n\n{descriptor}"
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={"model": "tinyllama", "prompt": prompt, "stream": False}
                    )
                    analysis = response.json().get("response", "⚠️ No response from Ollama.")
                    st.markdown(f"### 🧠 {analysis_type.capitalize()} Analysis")
                    st.markdown(analysis)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                break

# ---------- Resume Tips ----------
if job_data:
    st.markdown("---")
    st.markdown("### 📄 Resume Improvement Tips")
    if st.button("💡 Generate Resume Tips"):
        qualifications = job_data.get(selected_job, "No qualifications available.")
        prompt = (
            f"I'm applying for a job titled: '{selected_job}'.\n"
            f"The job qualifications are:\n{qualifications}\n"
            "What can I improve in my resume to increase my chances?"
        )
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "tinyllama", "prompt": prompt, "stream": False}
            )
            tips = response.json().get("response", "⚠️ No tips generated.")
            st.text_area("Recommended Resume Tips", value=tips, height=200)
        except Exception as e:
            st.error(f"❌ Error generating resume tips: {e}")



