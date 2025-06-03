# Academic Advisor Assistant 🤖🎓

This is an AI-powered academic advising tool built with [FastAPI + React + LLM API]. It simulates a helpful academic advisor assistant who offers students guidance on:

- 📚 Course planning and degree progress
- 🧠 Study techniques and time management
- 🏫 University rules, deadlines, and policies
- 🎯 Career and academic goal alignment

## Features
- Natural language interaction
- Personalized responses based on student context
- Follow-up questions for more tailored advice

## Prompt Design
The system prompt used:
> "You are a helpful academic advisor assistant. Your job is to provide clear, accurate, and student-friendly advice on academic planning, course selection, degree requirements, study tips, and related university policies. Always be supportive, informative, and concise. When answering, consider the student's background, goals, and any specific constraints they mention. If more information is needed, ask thoughtful follow-up questions to better assist them."

## 🚀 Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

* **Python:** Version 3.x is recommended. You can download it from [python.org](https://www.python.org/downloads/).
* **Node.js and npm:** Node.js (which includes npm, the Node Package Manager) is required for the frontend. You can download it from [nodejs.org](https://nodejs.org/).
* **Git:** For cloning the repository. You can download it from [git-scm.com](https://git-scm.com/downloads).

---

### ⚙️ Setting Up the Project

1.  **Clone the Repository:**
    Open your terminal or command prompt and run the following command:
    ```bash
    git clone https://github.com/DahalRojan/university_advising_chatbot.git
    ```

2.  **Navigate to the Project Directory:**
    ```bash
    cd university_advising_chatbot
    ```

---

### 🔌 Backend Setup

1.  **Navigate to the Backend Directory:**
    From the project's root directory, change into the `backend` folder:
    ```bash
    cd backend
    ```

2.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project-specific dependencies.
    * Create the virtual environment:
        ```bash
        python -m venv env
        ```
    * Activate the virtual environment:
        * **On Windows:**
            ```bash
            .\env\Scripts\activate
            ```
        * **On macOS/Linux:**
            ```bash
            source env/bin/activate
            ```
    You should see `(env)` at the beginning of your terminal prompt, indicating the virtual environment is active.

3.  **Install Backend Dependencies:**
    With the virtual environment still active, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    * Inside the `backend` directory, create a new folder named `configs` if it doesn't already exist.
    * Inside the `configs` folder, create a file named `.env`.
    * Open the `.env` file and add the following lines, replacing the placeholder values with your actual Groq API credentials:
        ```env
        GROQ_API_URL=your_groq_api_url_here
        GROQ_API_KEY=your_groq_api_key_here
        GROQ_MODEL=your_groq_model_name_here
        ```



5.  **Run the Backend Server:**
    ```bash
    python run_chatbot.py
    ```
    Your backend application should now be running. Check your terminal for output indicating the server has started and on which port it's listening (e.g., `http://127.0.0.1:8000`).
    To access the swagger and test the API ( `http://127.0.0.1:8000/docs`)

---

### 🖥️ Frontend Setup

1.  **Navigate to the Frontend Directory:**
    From the project's root directory (you might need to go back one level if you are still in `backend` using `cd ..`), change into the `frontend` folder:
    ```bash
    cd frontend
    ```

2.  **Install Frontend Dependencies:**
    ```bash
    npm install
    ```
    This command will download and install all the necessary Node.js packages defined in your `package.json` file.

3.  **Run the Frontend Development Server:**
    ```bash
    npm run dev
    ```
    This will start the frontend application. Your terminal will likely display a local URL (commonly `http://localhost:3000` or a similar port) where you can access the frontend in your web browser.

---

You should now have both the backend and frontend services running locally!

## License
MIT

