*Copyright Google LLC. Supported by Google LLC and/or its affiliate(s). This solution, including any related sample code or data, is made available on an “as is,” “as available,” and “with all faults” basis, solely for illustrative purposes, and without warranty or representation of any kind. This solution is experimental, unsupported and provided solely for your convenience. Your use of it is subject to your agreements with Google, as applicable, and may constitute a beta feature as defined under those agreements. To the extent that you make any data available to Google in connection with your use of the solution, you represent and warrant that you have all necessary and appropriate rights, consents and permissions to permit Google to use and process that data. By using any portion of this solution, you acknowledge, assume and accept all risks, known and unknown, associated with its usage and any processing of data by Google, including with respect to your deployment of any portion of this solution in your systems, or usage in connection with your business, if at all. With respect to the entrustment of personal information to Google, you will verify that the established system is sufficient by checking Google's privacy policy and other public information, and you agree that no further information will be provided by Google.*

# Advanced Verification Assistant

## 🚀 Overview

The Advanced Verification Assistant is a web application designed to help users prepare and pre-screen their business verification data before submitting it for official processes like Google's Advanced Verfication. It provides a multi-step form to collect business details and required documentation, then leverages an AI-powered agent to analyze the submitted information and provide actionable feedback.

The primary goal is to identify potential issues, inconsistencies, or missing information early, increasing the likelihood of a successful official verification.

**Key Features:**
* **Multi-Step Data Submission:** Guides users through providing business details and uploading necessary documents/images.
* **AI-Powered Analysis:** Utilizes an LLM agent to review submissions against common verification criteria.
* **Structured Feedback:** Presents analysis results with a high-level summary and detailed, aspect-by-aspect feedback (Green/Yellow/Red status, justification, and evidence).
* **Secure Cloud Storage for Processing:** Files uploaded for analysis are temporarily stored in Google Cloud Storage (GCS). This storage is fully encrypted at rest and configured with strict access controls to ensure data security and privacy during the analysis workflow. Once the analysis transaction is complete, these temporary files are securely deleted from GCS.
* **Python-Powered Frontend:** Built with [Mesop](https://google.github.io/mesop/), allowing for UI development purely in Python.


## ✨ Features & Functionality

* **User Interface:**
    * **Step 1: Business Details:** Collects primary business name, address, and mailing addresses.
    * **Step 2: Upload Required Items:** A unified section for all document and image uploads with clear instructions for each item.
    * **Step 3: Review & Submit:** Allows users to review all entered information and the list of uploaded files before submitting for AI analysis.
    * **Step 4: Analysis Feedback:** Displays the structured feedback from the AI agent, including an overall summary and detailed RYG status for various verification aspects.
* **Backend Analysis:**
    * Receives business details and file data (bytes) from the frontend.
    * Utilizes an LLM Agent to perform a comprehensive review.
    * The agent analyzes text, image content (multimodal), and consistency across provided information.
    * Returns a structured JSON response detailing the findings.


## 🛠️ Technology Stack

* **Frontend:**
    * [Mesop](https://google.github.io/mesop/): Python-based web UI framework.
* **Backend:**
    * Python with FastAPI.
    * Agent Development Kit (ADK) for LLM agent interaction.
    * Underlying LLM: Google Gemini via the ADK.
* **Data Handling (for analysis transaction):**
    * Files are uploaded in the Mesop frontend and their bytes are passed to the backend API for temporary storage.
    * The backend passes these bytes directly to the LLM agent for processing.
* **Authentication:**
    * Uses Google Cloud Identity-Aware Proxy (IAP).


## ⚙️ Getting Started

This section would typically include instructions on how to set up and run the project locally.

### Prerequisites

* Python (e.g., 3.10+)
* A Google Cloud Platform project with billing enabled.
* A Gemini API Key. See [here](https://ai.google.dev/gemini-api/docs/api-key) for details.


### Run Locally

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```
2.  Set up a Python virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Add your required environment variables:
    ```
    export GOOGLE_API_KEY='<your-api-key>'
    export GOOGLE_GENAI_USE_VERTEXAI='FALSE'
    export GOOGLE_MAPS_API_KEY='<your-api-key>'
    export GEMINI_MODEL='gemini-2.5-pro'
    export BUCKET_NAME='<your-google-cloud-storage-bucket>
    ```
5.  Ensure you are logged into google cloud
    ```
    gcloud auth application-default login
    gcloud config set project <your-project-id>
    ```  
6.  Run **Backend (FastAPI/ADK):**
    ```bash
    cd backend-adk
    uvicorn src.main:app --reload --port 8008
    ```
7.  Run **Frontend (Mesop):**
    ```bash
    cd frontend-mesop
    uvicorn app.main:app --reload --port 8000
    ```

### Deploy to Google Cloud

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```
2.  Ensure you are logged into google cloud
    ```
    gcloud auth application-default login
    gcloud config set project <your-project-id>
    ```  
3.  Create a Artifacts Registry remote repository:
    ```bash
    gcloud artifacts repositories create av-assistant-app \
      --repository-format=docker \
      --location=us-central1 \
      --description="Docker repository for AV Assistant."
    ```
4.  Build and push the images for front and backend.
    ```bash
    gcloud builds submit --config ./cloudbuild.yaml .
    ```
5.  Navigate to the terraform directory and create your env/<your-env>.tfvars file.
    ```bash
    cd terraform
    cp env/prod.tfvars env/<your-env>.tfvars
    vi env/<your.env>.tfvars
    ```
6.  Run terraform by providing a backend to store state.
    ```bash
    terraform init -backend-config="bucket=<your-env-bucket-name>"
    terraform apply -var-file=env/<your-env>.tfvars -auto-approve
    ```
    > [!NOTE]  
    > Using a dedicated backend bucket when initializing terraform is
    > highliy recommended to avoid state conflicts.