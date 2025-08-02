import os
from dotenv import load_dotenv
import requests
import sys

def check_environment():
	"""Check that the environment is correctly set up"""

	# Check Python version
	print(f"Python version: {sys.version}")

	# Check virtual environment
	if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
		print("✅ Virtual environment is active")
	else:
		print("❌ Virtual environment is NOT active")
		# Check required packages
	try:
		import gradio
		print(f"✅ Gradio installed (version {gradio.__version__})")
	except ImportError:
		print("❌ Gradio not installed")
	try:
		import ollama
		print(f"✅ Ollama client installed")
	except ImportError:
		print("❌ Ollama client not installed")

	# Check .env file
	load_dotenv()
	nyc_job_api = os.getenv("NYC_JOBS_API")
	if nyc_job_api:
		print("✅ NYC_JOBS_API found in .env file")
	else:
		print("❌ NYC_JOBS_API API key not found in .env file")
	# Check Ollama availability
	try:
		response = requests.post(
			"http://localhost:11434/api/generate",
			json={
				"model": "mistral",
				"prompt": "Hello",
				"stream": False
			}
		)
		if response.status_code == 200:
			print("✅ Ollama is running and responding")
		else:
			print(f"❌ Ollama returned status code: {response.status_code}")
	except Exception as e:
		print(f"❌ Ollama not available: {str(e)}")
		print("Make sure Ollama is installed and running.")
if __name__ == "__main__":
	check_environment()