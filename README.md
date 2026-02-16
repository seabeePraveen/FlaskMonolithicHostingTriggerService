# 🚀 SelfHoster

**SelfHoster** is a lightweight, dynamic hosting service designed to deploy and manage multiple Flask applications from GitHub repositories instantly. It features a modern web dashboard and a dynamic request dispatcher that allows multiple standalone Flask apps to run concurrently under a single host.

---

## ✨ Key Features

*   **Instant Clone & Deploy**: Provide a GitHub URL, and SelfHoster handles the rest—cloning, dependency installation, and routing.
*   **Dynamic Request Dispatching**: Uses a custom WSGI dispatcher (Werkzeug-based) to route traffic to independent sub-projects without restarting the main server.
*   **Built-in Environment Management**: Support for custom `.env` variables and `requirements.txt` for every project.
*   **Modern UI/UX**: Premium dashboard built with a sleek glassmorphism aesthetic, real-time status updates, and a dedicated project management interface.
*   **Full CRUD Support**: Effortlessly clone, configure, update, and delete deployed projects.

---

## 🛠️ Tech Stack

*   **Backend**: Python, Flask, Werkzeug (Dynamic Dispatcher)
*   **Frontend**: HTML5, Vanilla CSS, Javascript (ES6+)
*   **Process Management**: Subprocess-based git operations and pip management.
*   **Data Store**: JSON-based configuration database for lightweight persistence.

---

## 🚀 Getting Started

### Prerequisites

*   Python 3.8+
*   Git installed on the host system.

### Installation

1.  **Clone the dashboard:**
    ```bash
    git clone https://github.com/seabeePraveen/FlaskMonolithicHostingTriggerService-.git
    cd FlaskMonolithicHostingTriggerService-
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the service:**
    ```bash
    python app.py
    ```

The dashboard will be available at `http://localhost:5000`.

---

## 📖 Usage Guide

1.  **Deploy a Project**: Paste a GitHub repository URL into the "Repository URL" field.
2.  **Specify Entry File**: Tell SelfHoster which file contains the Flask `app` object (e.g., `app.py`).
3.  **Configure Environment**: Add any required environment variables (e.g., `API_KEY=12345`) and extra dependencies.
4.  **Access your App**: Once cloned, your app is available at `http://localhost:5000/your-repo-name/`.

---

## 🏗️ Architecture

SelfHoster utilizes a **Dynamic Project Dispatcher**. Unlike traditional reverse proxies, it dynamically mounts sub-applications onto the WSGI stack. Each project is treated as an independent module with its own scope, allowing for a monolithic-like experience with microservices-like flexibility.

---

## 📂 Project Structure

```text
├── app.py                      # Main service entrance
├── dynamicProjectDispatcher.py # Core routing logic
├── projects/                   # Storage for deployed repositories
├── static/                     # External CSS & JS assets
├── templates/                  # UI components
└── projects_db.json            # Deployment configuration store
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the platform.

---

## 📜 License

This project is licensed under the MIT License.
