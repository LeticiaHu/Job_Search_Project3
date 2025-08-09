import gradio as gr
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NYC_JOBS_API = os.getenv("NYC_JOBS_API")
if not NYC_JOBS_API:
	print("Warning: NYC_JOBS_API not found in environment variables.")
	print("Please create a .env file with your NYC JOBS API Key.")

# Gloabal variables to store current jobs	
current_postings = []

USAJOBS_USER_AGENT = os.getenv("USAJOBS_USER_AGENT")
NYC_JOBS_API = os.getenv("NYC_JOBS_API")

def get_top_jobs(section, params=None):
    """
    Fetch top job postings from the USAJobs API.

    Args:
        section (str): Used as the keyword for the job search.
        params (dict): Optional query parameters.

    Returns:
        dict: API response data or an error dictionary.
    """
    if params is None:
        params = {"ResultsPerPage": 5}

    # Add the section as a keyword
    params["Keyword"] = section

    base_url = "https://data.usajobs.gov/api/Search"

    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": USAJOBS_USER_AGENT,
        "Authorization-Key": NYC_JOBS_API
    }

    # Debug (optional)
    print("User-Agent:", USAJOBS_USER_AGENT)
    print("API Key:", NYC_JOBS_API[:5] + "..." if NYC_JOBS_API else "MISSING")

    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

        if "fault" in data:
            return {"error": data["fault"].get("faultstring", "API error")}

        if data.get("status") and data["status"] != "OK":
            return {"error": f"API returned status: {data['status']}"}

        jobs_list = []

        for job in data.get("results", [])[:max_jobs]: 
            if not (job.get("title") and job.get("abstract") and job.get("url")):
                continue

            # Try to get image URL with format "superJumbo" if available
            image_url = None
            for media in job.get("multimedia", []):
                if media.get("format") == "superJumbo":
                    image_url = media.get("url")
                    break

            jobs_list.append({
                "title": job.get("title", ""),
                "location": job.get("location", ""),
                "salary": job.get("salary", ""),
                "url": job.get("url", ""),
                "byline": job.get("byline", ""),
                "image_url": image_url
            })

        if not jobs_list:
            return {"error": "No jobs found."}

        return {"jobs": jobs_list}

    except Exception as e:
        return {"error": f"Error fetching top jobs: {str(e)}"}


def check_ollama_availability():
    """
    Check if the Ollama server is available by sending a request to its /api/tags endpoint.
    
    Returns:
        bool: True if available (status code 200), False otherwise.
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


def analyze_with_ollama(job, analysis_type="summary"):
    if not job:
        return "❌ No job provided."

    title = job.get("PositionTitle", "N/A")
    summary = job.get("UserArea", {}).get("Details", {}).get("JobSummary", "N/A")
    salary_range = job.get("PositionRemuneration", [{}])[0].get("MaximumRange", "N/A")

    if analysis_type == "summary":
        prompt = f"""You are a career assistant. Summarize this job posting:

Title: {title}

Summary: {summary}

Return a 3–5 sentence summary with responsibilities and qualifications.
"""
    elif analysis_type == "qualifications":
        prompt = f"""You are an HR assistant. Based on this job posting:

Title: {title}

Summary: {summary}

Return a bullet-point list of:
1. Minimum qualifications
2. Education requirements
3. Benefits (if mentioned)
"""
    elif analysis_type == "salary":
        prompt = f"""You are a compensation analyst. Review this job post:

Title: {title}
Max Salary: {salary_range}

Summary: {summary}

Return salary insights: typical range, experience required, and bonuses if applicable.
"""
    else:
        return "❌ Invalid analysis type."

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3
            }
        )

        if response.status_code == 200:
            return response.json().get("response", "⚠️ No analysis returned.")
        else:
            return f"❌ Ollama error: {response.status_code}"

    except Exception as e:
        return f"❌ Failed to contact Ollama: {str(e)}"


job_data = {}  # Global dictionary to store job summaries for resume tips

#  Creating get_jobs function to return dropdow

def get_jobs(section):
    global current_postings, job_data

    if not section:
        return "❌ Please enter a section.", gr.update(choices=[])

    result = get_top_jobs(section, {"ResultsPerPage": 5})

    if "error" in result:
        return f"❌ {result['error']}", gr.update(choices=[])

    current_postings = result.get("SearchResult", {}).get("SearchResultItems", [])

    if not current_postings:
        return "⚠️ No jobs found.", gr.update(choices=[])

    output = "# 🧭 Top Jobs\n\n"
    job_titles = []

    job_data.clear()

    for i, job in enumerate(current_postings, 1):
        descriptor = job.get("MatchedObjectDescriptor", {})
        title = descriptor.get("PositionTitle", "N/A")
        location = descriptor.get("PositionLocationDisplay", "N/A")
        summary = descriptor.get("UserArea", {}).get("Details", {}).get("JobSummary", "No summary")
        url = descriptor.get("PositionURI", "#")

        output += f"### {i}. {title}\n"
        output += f"- 📍 **Location:** {location}\n"
        output += f"- 📄 {summary}\n"
        output += f"- 🔗 [View Posting]({url})\n\n---\n\n"

        job_titles.append(title)
        job_data[title] = summary

    return output, gr.update(choices=job_titles, value=None)


def analyze_jobs(job_title, analysis_type):
    """
    Analyze the selected job by title.
    """
    if not job_title:
        return "⚠️ Please select a job to analyze."

    if not analysis_type:
        return "❌ No analysis type selected."

    global current_postings
    if not current_postings:
        return "❌ No job data loaded."

    # Debug info
    print("🔍 job_title selected:", job_title)
    print("📦 total postings:", len(current_postings))

    # Find job by title match
    match = None
    for job in current_postings:
        descriptor = job.get("MatchedObjectDescriptor", {})
        title = descriptor.get("PositionTitle", "")
        if title == job_title:
            match = job
            break

    if not match:
        return f"❌ Could not find the selected job: {job_title}"

    descriptor = match.get("MatchedObjectDescriptor", {})
    title = descriptor.get("PositionTitle", "N/A")
    url = descriptor.get("PositionURI", "#")
    summary = descriptor.get("UserArea", {}).get("Details", {}).get("JobSummary", "")

    # Run LLM analysis (e.g., summary, qualifications, salary)
    analysis = analyze_with_ollama(descriptor, analysis_type)

    output = f"# Analysis of: {title}\n\n"
    output += f"## {analysis_type.capitalize()} Analysis\n\n{analysis}\n\n"
    output += f"[🔗 View Full Job Posting]({url})\n\n"

    return output


def recommend_jobs_from_skills(skills):
    if not skills:
        return "⚠️ Please enter some skills or interests."

    prompt = f"""You are a career advisor. Based on the following user-provided skills, recommend 3–5 suitable job titles or roles and explain why.

Skills: {skills}

Return the recommendations in bullet point format with brief explanations.
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.4
            }
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "⚠️ No recommendations generated.")
        else:
            return f"❌ Ollama error: {response.status_code}"

    except Exception as e:
        return f"❌ Error generating recommendations: {str(e)}"



def get_resume(job_title, qualifications):
    prompt = (
        f"I'm applying for a job titled: '{job_title}'.\n"
        f"The job qualifications are:\n{qualifications}\n"
        "What can I add or improve in my resume to increase my chances of getting this job?"
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False
            }
        )
        data = response.json()
        return data.get("response", "⚠️ No response from Ollama.")
    except Exception as e:
        return f"❌ Error generating resume tips: {e}"

def fetch_resume_tips(job_title):
    qualifications = job_data.get(job_title, "No qualifications available.")
    return get_resume(job_title, qualifications)


# Create the Gradio interface
with gr.Blocks(
    title="AI Job Search Assistant",
    css="""
        .gr-button { 
            font-size: 16px; 
            font-weight: bold; 
            background-color: #0b7285;
            color: white;
            border-radius: 8px;
        }
        .gr-textbox textarea {
            font-family: monospace;
            font-size: 14px;
            background-color: #f8f9fa;
        }
        .gr-markdown {
            font-size: 15px;
            line-height: 1.6;
        }
    """
) as demo:

    gr.HTML("""
    <h1 style='font-size: 36px; color: #2E86C1; text-align: center;'>
        💼 AI Job Search Assistant
    </h1>
""")
    with gr.Accordion("📘 How to Use This App", open=True):
        gr.Markdown("""
    ### 👋 Welcome to the Job Search Assistant!

    This app helps you:
    - 🔍 Get job title recommendations based on your **skills**
    - 📥 Browse **real-time job postings** from USAJobs
    - 🤖 Analyze jobs using **Ollama LLM**
    - 📄 Get **resume improvement tips** tailored to each job

    ### 💡 Steps to Use:
    1. **Enter your skills** (e.g. Python, Excel) and click **"Suggest Jobs"**
    2. Enter a **job category** (e.g. finance, tech) and click **"Load Job Postings"**
    3. Select a job from the dropdown and choose an analysis type
    4. Click **"Analyze Selected Job"** to get AI-powered insights
    5. Click **"Generate Resume Tips"** for personalized resume advice

    ---
    """)


    gr.Markdown("## A demonstration of using public job APIs and Ollama LLM with Gradio")

    # Recommendation section based on skills
    with gr.Group():
        gr.Markdown("### 🎯 Get Job Recommendations Based on Your Skills")
        skill_input = gr.Textbox(
            label="Enter your skills",
            placeholder="e.g. Python, Excel, data analysis, marketing",
            lines=3
        )
        recommend_btn = gr.Button("🔍 Suggest Jobs")
        analysis_output = gr.Markdown()

    #  Job search section (underneath)
    gr.Markdown("---")  # Divider line

    with gr.Row():
        with gr.Column():
            section_input = gr.Textbox(label="Enter Job Category (e.g., finance, technology)")
            gr.Markdown("💡 Tip: Selecting a job from the recommended list may increase your chances of getting a response.")
            get_jobs_btn = gr.Button("📥 Load Job Postings")

        with gr.Column():
            job_dropdown = gr.Dropdown(
                choices=[],
                label="Select a Job to Analyze",
                interactive=True
            )
            analysis_type_selector = gr.Dropdown(
                choices=["summary", "qualifications", "salary"],
                value="summary",
                label="Select Analysis Type",
                interactive=True
            )
            analyze_btn = gr.Button("Analyze Selected Job")

    with gr.Row():
        with gr.Column():
            jobs_display = gr.Markdown(label="🧾 Job Listings")
        with gr.Column():
            job_analysis_display = gr.Markdown(label="🔎 Job Analysis")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📄 Resume Improvement Tips")
            get_resume_btn = gr.Button("💡 Generate Resume Tips")
            resume_tips_output = gr.Textbox(label="Resume Tips", lines=8, interactive=False)


    # Button actions
    recommend_btn.click(
        fn=recommend_jobs_from_skills,
        inputs=skill_input,
        outputs=analysis_output
    )

    get_jobs_btn.click(
        fn=get_jobs,
        inputs=section_input,
        outputs=[jobs_display, job_dropdown]
    )

    analyze_btn.click(
        fn=analyze_jobs,
        inputs=[job_dropdown, analysis_type_selector],
        outputs=job_analysis_display
    )


    get_resume_btn.click(
        fn=fetch_resume_tips,
        inputs=job_dropdown,
        outputs=resume_tips_output
    )


# Launch the interface
if __name__ == "__main__":
	if not check_ollama_availability():
		print("Warnings: Ollama is not available.")
		print("Analysis functionality will not work.")
		print("Please make sure Ollama is running with the mistral model.")

demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
    #demo.launch(share=True) # include share=True for live link