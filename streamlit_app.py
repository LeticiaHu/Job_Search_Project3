import os
import requests
from dotenv import load_dotenv
import streamlit as st

# ----------------- ENV & CONFIG -----------------

load_dotenv()

USAJOBS_USER_AGENT = os.getenv("USAJOBS_USER_AGENT")
NYC_JOBS_API = os.getenv("NYC_JOBS_API")  # API key for USAJobs

if not USAJOBS_USER_AGENT or not NYC_JOBS_API:
    print("Warning: USAJOBS_USER_AGENT and/or NYC_JOBS_API not found in environment variables.")
    print("Please create a .env file or set Streamlit secrets with these values.")


# ----------------- USAJOBS API FUNCTION -----------------

def get_top_jobs(section: str, results_per_page: int = 5):
    """
    Fetch top job postings from the USAJobs API.

    Returns:
        dict: {"jobs": [MatchedObjectDescriptor, ...]} or {"error": "..."}.
    """
    if not USAJOBS_USER_AGENT or not NYC_JOBS_API:
        return {"error": "Missing USAJOBS_USER_AGENT or NYC_JOBS_API in environment variables."}

    if not section:
        return {"error": "Please enter a job category or keyword."}

    params = {
        "ResultsPerPage": results_per_page,
        "Keyword": section,
    }

    base_url = "https://data.usajobs.gov/api/Search"

    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": USAJOBS_USER_AGENT,
        "Authorization-Key": NYC_JOBS_API,
    }

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        search_result = data.get("SearchResult", {})
        items = search_result.get("SearchResultItems", [])

        jobs_list = []
        for item in items:
            descriptor = item.get("MatchedObjectDescriptor", {})
            jobs_list.append(descriptor)

        if not jobs_list:
            return {"error": "No jobs found for that keyword."}

        return {"jobs": jobs_list}

    except Exception as e:
        return {"error": f"Error fetching jobs: {str(e)}"}


# ----------------- SIMPLE "AI-LIKE" HELPERS (NO LLM) -----------------

def recommend_jobs_from_skills(skills: str) -> str:
    """
    Generate simple rule-based job title suggestions from skills text.
    No external LLM – just pattern-based.
    """
    if not skills:
        return "⚠️ Please enter some skills or interests."

    text = skills.lower()

    suggestions = []

    if any(k in text for k in ["python", "sql", "excel", "data", "pandas", "power bi"]):
        suggestions.append("• Data Analyst / Data Scientist – strong match with your data and analytics skills.")
    if any(k in text for k in ["finance", "budget", "accounting", "valuation"]):
        suggestions.append("• Financial Analyst – your finance background fits analytical and modeling roles.")
    if any(k in text for k in ["access", "database", "sql server", "oracle"]):
        suggestions.append("• Database / Reporting Analyst – experience with databases and reporting tools.")
    if any(k in text for k in ["adobe", "powerpoint", "presentations", "communication"]):
        suggestions.append("• Business Analyst – mix of analysis and communication / presentation skills.")
    if any(k in text for k in ["health", "medicaid", "medicare", "healthcare"]):
        suggestions.append("• Health Insurance / Healthcare Analyst – your healthcare-related skills are valuable here.")

    if not suggestions:
        suggestions.append("• Operations / Business Analyst – your skills are broadly useful in analytical roles.")
        suggestions.append("• Project Coordinator – especially if you have organizational and communication strengths.")

    result = "### Recommended Job Directions\n\n"
    for s in suggestions:
        result += f"{s}\n"
    result += "\n_These are rule-based suggestions derived from your skills, not from an LLM._"

    return result


def analyze_job_descriptor(descriptor: dict, analysis_type: str) -> str:
    """
    Do a simple, rule-based “analysis” of a job based on the descriptor fields.
    """
    title = descriptor.get("PositionTitle", "N/A")
    summary = (
        descriptor.get("UserArea", {})
        .get("Details", {})
        .get("JobSummary", "No summary available.")
    )
    qualifications = (
        descriptor.get("QualificationSummary")
        or descriptor.get("UserArea", {}).get("Details", {}).get("QualificationSummary")
        or "No specific qualifications summary provided in the posting."
    )

    remuneration = descriptor.get("PositionRemuneration", [{}])[0]
    salary_min = remuneration.get("MinimumRange", "N/A")
    salary_max = remuneration.get("MaximumRange", "N/A")
    pay_interval = remuneration.get("RateIntervalCode", "per year")

    if analysis_type == "summary":
        text = f"""**Job Summary (Rule-Based)**

- **Title:** {title}
- **Salary Range:** {salary_min} – {salary_max} {pay_interval}

**Summary from posting:**
{summary}
"""
    elif analysis_type == "qualifications":
        text = f"""**Qualifications & Requirements (From Posting)**

{qualifications}

_This is taken directly (or closely) from the USAJobs posting, not generated by a model._
"""
    elif analysis_type == "salary":
        text = f"""**Salary Analysis (Rule-Based)**

- **Title:** {title}
- **Posted Range:** {salary_min} – {salary_max} {pay_interval}

**Interpretation:**
- This range comes directly from the job posting.
- Higher end of the range often reflects more experience or specialized skills.
- You can look for similar positions on USAJobs to compare whether this range is typical.
"""
    else:
        text = "❌ Invalid analysis type."

    return text


def make_resume_tips(job_title: str, qualifications_text: str) -> str:
    """
    Rule-based resume tips using the job title and qualification text.
    No external LLM.
    """
    tips = [
        f"1. **Tailor your summary to '{job_title}'.** Start your resume with a 2–3 sentence summary that mentions the job title and highlights experience that matches the posting.",
        "2. **Mirror the language from the qualifications.** Reuse key phrases from the job's qualifications section in your bullet points (as long as they are true for you).",
        "3. **Add measurable impact.** For each past role, add numbers where possible (e.g. 'improved processing time by 20%').",
        "4. **Highlight relevant tools and technologies.** Make sure tools mentioned in the posting (e.g. Excel, SQL, Access, Power BI) are clearly listed in a 'Skills' section.",
        "5. **Keep the resume focused.** Remove or shorten experience that is not related to the main responsibilities and qualifications of this job.",
        "6. **Align your experience dates and job levels.** Ensure your years of experience match what is typically expected for this type of federal role.",
    ]

    result = "Here are some rule-based resume improvement tips:\n\n"
    for t in tips:
        result += t + "\n"

    result += "\n_These tips are generic but tailored around the selected job title and qualifications text, not generated by an LLM._\n"

    if qualifications_text and qualifications_text.strip():
        result += "\n---\n**Qualifications / Summary from Posting (for reference):**\n"
        result += qualifications_text

    return result


# ----------------- STREAMLIT APP -----------------

def main():
    st.set_page_config(page_title="AI Job Search Assistant", page_icon="💼", layout="wide")

    # 🔹 Session state for jobs and job data
    if "current_postings" not in st.session_state:
        st.session_state.current_postings = []
    if "job_titles" not in st.session_state:
        st.session_state.job_titles = []
    if "jobs_markdown" not in st.session_state:
        st.session_state.jobs_markdown = "⚠️ No jobs loaded yet."
    if "job_data" not in st.session_state:
        # store summary/qualifications per title
        st.session_state.job_data = {}

    # ----- Header -----
    st.markdown(
        "<h1 style='font-size: 36px; color: #2E86C1; text-align: center;'>"
        "💼 AI Job Search Assistant"
        "</h1>",
        unsafe_allow_html=True,
    )

    # ----- How to use (expander) -----
    with st.expander("📘 How to Use This App", expanded=True):
        st.markdown(
            """
### 👋 Welcome to the Job Search Assistant!

This app helps you:

- 🔍 Get simple job title recommendations based on your **skills**
- 📥 Browse **real-time job postings** from USAJobs
- 🔎 View **job qualification / summary / salary** info with analysis options
- 📄 Get **resume improvement tips** tailored to the selected job (rule-based)

### 💡 Steps to Use:
1. **Enter your skills** (e.g. Python, Excel) and click **"🔍 Suggest Jobs"**
2. Enter a **job category** (e.g. finance, tech) and click **"📥 Load Job Postings"**
3. Select a job from the dropdown and choose an **analysis type**
4. Click **"Analyze Selected Job"** to see details
5. Click **"💡 Generate Resume Tips"** for personalized resume advice

---
            """
        )

    st.markdown("## A demonstration of using the public USAJobs API with Streamlit")

    # ================== SECTION 1: SKILLS → RECOMMENDED JOBS ==================
    st.markdown("### 🎯 Get Job Recommendations Based on Your Skills")

    col_skills_left, col_skills_right = st.columns([1, 1])

    with col_skills_left:
        skills_text = st.text_area(
            "Enter your skills",
            placeholder="e.g. Python, Excel, CUNYBuy, SQL, Microsoft Access, Adobe, modeling in Solver, analytical skills, finance",
            height=100,
        )
        suggest_btn = st.button("🔍 Suggest Jobs")

    with col_skills_right:
        if suggest_btn:
            rec_text = recommend_jobs_from_skills(skills_text)
            st.markdown(rec_text)
        else:
            st.info("Enter your skills and click **🔍 Suggest Jobs** to see suggestions.")

    st.markdown("---")

    # ================== SECTION 2: JOB SEARCH + ANALYSIS CONTROLS ==================
    st.markdown("### 📥 Browse & Analyze USAJobs Postings")

    top_left, top_right = st.columns([1, 1])

    # ------ LEFT: load job postings ------
    with top_left:
        section_input = st.text_input(
            "Enter Job Category (e.g., finance, technology, data analysis)",
            value="data analysis",
        )
        st.markdown(
            "💡 Tip: Selecting a job from the recommended list may increase your chances of getting a response."
        )

        results_per_page = st.slider(
            "Results per page",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
        )

        load_jobs_btn = st.button("📥 Load Job Postings")

        if load_jobs_btn:
            with st.spinner("Loading job postings from USAJobs..."):
                result = get_top_jobs(section_input.strip(), results_per_page)

            if "error" in result:
                st.error(f"❌ {result['error']}")
                st.session_state.current_postings = []
                st.session_state.job_titles = []
                st.session_state.jobs_markdown = "⚠️ No jobs loaded."
                st.session_state.job_data = {}
            else:
                postings = result["jobs"]
                st.session_state.current_postings = postings
                st.session_state.job_titles = []
                st.session_state.job_data = {}

                md = "# 🧭 Top Jobs\n\n"

                for i, descriptor in enumerate(postings, 1):
                    title = descriptor.get("PositionTitle", "N/A")
                    location = descriptor.get("PositionLocationDisplay", "N/A")
                    summary = (
                        descriptor.get("UserArea", {})
                        .get("Details", {})
                        .get("JobSummary", "No summary available.")
                    )
                    url = descriptor.get("PositionURI", "#")

                    md += f"### {i}. {title}\n"
                    md += f"- 📍 **Location:** {location}\n"
                    md += f"- 📄 {summary}\n"
                    md += f"- 🔗 [View Posting]({url})\n\n---\n\n"

                    st.session_state.job_titles.append(title)
                    st.session_state.job_data[title] = summary

                st.session_state.jobs_markdown = md
                st.success(f"Loaded {len(st.session_state.job_titles)} job(s).")

    # ------ RIGHT: select job + analysis type ------
    with top_right:
        st.markdown("### 🔎 Analyze Selected Job")

        selected_job_title = st.selectbox(
            "Select a Job to Analyze",
            options=st.session_state.job_titles,
            index=0 if st.session_state.job_titles else -1,
            placeholder="Load job postings first",
        )

        analysis_type = st.selectbox(
            "Select Analysis Type",
            options=["summary", "qualifications", "salary"],
            index=0,
        )

        analyze_btn = st.button("Analyze Selected Job")
        analysis_output_area = st.empty()

        if analyze_btn:
            if not selected_job_title:
                analysis_output_area.markdown("⚠️ Please select a job to analyze.")
            elif not st.session_state.current_postings:
                analysis_output_area.markdown("❌ No job data loaded. Load postings first.")
            else:
                # find descriptor by title
                match = None
                for descriptor in st.session_state.current_postings:
                    if descriptor.get("PositionTitle") == selected_job_title:
                        match = descriptor
                        break

                if not match:
                    analysis_output_area.markdown(
                        f"❌ Could not find the selected job: {selected_job_title}"
                    )
                else:
                    url = match.get("PositionURI", "#")
                    analysis_text = analyze_job_descriptor(match, analysis_type)

                    out_md = f"# Analysis of: {selected_job_title}\n\n"
                    out_md += f"## {analysis_type.capitalize()} Analysis\n\n{analysis_text}\n\n"
                    if url and url != "#":
                        out_md += f"[🔗 View Full Job Posting]({url})\n"
                    analysis_output_area.markdown(out_md)

    st.markdown("---")

    # ================== SECTION 3: JOB LISTINGS ==================
    st.markdown("### 🧾 Job Listings")
    st.markdown(st.session_state.jobs_markdown)

    # ================== SECTION 4: RESUME TIPS (BELOW JOB LISTINGS) ==================
    st.markdown("### 📄 Resume Improvement Tips")

    selected_for_resume = st.selectbox(
        "Select a job for resume tips",
        options=st.session_state.job_titles,
        index=0 if st.session_state.job_titles else -1,
        placeholder="Load job postings first",
    )

    if st.button("💡 Generate Resume Tips"):
        if not selected_for_resume:
            st.warning("Please select a job first.")
        else:
            qualifications_text = st.session_state.job_data.get(
                selected_for_resume, "No qualifications/summary available."
            )
            tips = make_resume_tips(selected_for_resume, qualifications_text)

            st.text_area(
                "Resume Tips",
                value=tips,
                height=320,
            )
    else:
        st.info("Select a job and click **💡 Generate Resume Tips** to see suggestions.")

if __name__ == "__main__":
    main()
