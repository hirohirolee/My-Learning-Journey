# HW3: Cosmos3-Super-Text2Image Text-to-Image Web App

<!-- 
作業要求摘要 (README 必須包含)：
1. Project Goal
2. Model Information
3. How to Run Locally
4. API Key Handling Instructions
5. Deployment Instructions
6. Links (GitHub & Streamlit Demo)
7. Screenshots
-->

## 🎯 Project Goal

This project was developed as part of **[cite: Your Course Name, e.g., AI Application Development]** Homework 3. 

The primary objective is to build and deploy a functional, user-friendly text-to-image generation web application. This project demonstrates the integration of modern AI development tools and practices, including:
*   Using **Gemini Canvas** for rapid application prototyping and code generation.
*   Integrating the **NVIDIA Cosmos3-Super-Text2Image** model via the Hugging Face Inference API.
*   Developing the frontend and logic using **Streamlit**.
*   Implementing **secure API key handling**.
*   Managing the project version control with **GitHub**.
*   Deploying the live application to **Streamlit Community Cloud**.

## 🤖 Model Information

*   **Model Name:** `nvidia/Cosmos3-Super-Text2Image`
*   **Description:** A text-to-image specialization model within the NVIDIA Cosmos3-Super family. It is designed to generate high-quality images based on text prompts.
*   **Specialization:** As described in official resources, this is a 64B parameter model optimized for text-to-image specialization, capable of producing detailed and realistic visuals.

## 📸 Screenshots

<!-- 
重要提示：
請在您的專案中建立一個名為 `screenshots` 的資料夾。
將您的 App 介面截圖命名為 `app_home.png` 並放入該資料夾。
將產生的圖片結果截圖命名為 `generated_result.png` 並放入該資料夾。
下方的代碼會自動引用這些圖片。
-->

### App Home Page (Desktop/Mobile View)
![App Home Screen](screenshots/app_home.png)

### Generated Result
![Generated Image Result](screenshots/generated_result.png)

## ✨ Features

*   **Text Prompt Input:** Users can describe the image they want to generate.
*   **Optional Controls:**
    *   **Image Style:** Choose from various visual styles (e.g., Photo, Artistic, Cinematic).
    *   **Aspect Ratio:** select the desired image dimensions (e.g., 16:9, 1:1, 9:16).
    *   **Seed:** set a specific random seed for reproducible results.
    *   **Number of Images:** Choose how many variations to generate (depending on API limits).
    *   **Negative Prompt:** Specify elements you do *not* want to appear in the image.
*   **Dynamic Image Display:** The generated image(s) are displayed directly on the web page.
*   **API Key Protection:** Implements a fallback mechanism for secure key entry.

## 🚀 How to Run Locally

Follow these steps to set up and run the application on your local machine.

### Prerequisites

*   Python 3.8 or higher installed.
*   A Hugging Face account and an API Token (HF Token).

### Step-by-Step Setup

1.  **Clone the Repository:**
```bash
    git clone [https://github.com/](https://github.com/)[cite: Your GitHub Username]/[cite: Your Repo Name, e.g., hw3-cosmos-text2image].git
    cd [cite: Your Repo Name]
    ```

2.  **Install Dependencies:**
It is recommended to use a virtual environment.
```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key (Optional for Local):**
    You have two options for providing your Hugging Face Token when running locally:

    *   **Option A (Web Input):** Run the app directly. It will detect the missing key and provide a password input field on the web page.
    *   **Option B (Local Secret):** Create a file at `.streamlit/secrets.toml` (do *not* upload this file to GitHub) and add your key:
```toml
        # .streamlit/secrets.toml
        HF_TOKEN = "your_huggingface_token_here"
        ```

4.  **Run the App:**
```bash
    streamlit run app.py
    ```
    The application should automatically open in your default web browser.

## 🔐 API Key Security (Crucial)

**Never hardcode your API keys directly in the `app.py` file!** This is a critical security risk and a requirement for this assignment.

This application is designed to handle API keys securely using a dual-method approach:

1.  **Streamlit Secrets (Preferred for Deployment):** The app first attempts to retrieve the key from the environment/platform secrets using `st.secrets.get("HF_TOKEN")`. This is how the key is managed on the live Streamlit Cloud deployment.
2.  **Web Input Fallback:** If no secret is found, the app displays a secure password input field (`st.text_input(..., type="password")`) on the page, allowing users to safely paste their own Hugging Face Token.

**.gitignore Configuration:**
Make sure your `.gitignore` file includes the following to prevent sensitive files from being pushed to GitHub:
```bash
# .gitignore
.env
.streamlit/secrets.toml
__pycache__/
*.png
*.jpg
*.jpeg
