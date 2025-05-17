# EOTRH Watch – Early Diagnostic Assistant

This tool is a website you can run on your own computer. It's designed to help veterinarians (or anyone working with horses under veterinary guidance) get an early idea if a horse might have a dental problem called Equine Odontoclastic Tooth Resorption and Hypercementosis (EOTRH).

It's built using a modern tool called **FastAPI** (FastAPI is like a set of pre-made building blocks that helps developers create websites and web applications quickly). This EOTRH Watch tool looks at three types of information to help make a guess:

1.  **Automated Image Analysis:** (This part is made simpler in this version). The tool can look at pictures you upload and do a basic check.
2.  **Manual Clinical Signs:** You can tell the tool about any signs of illness you've seen in the horse.
3.  **Manual Radiological Signs:** If you have X-rays (radiographs), you can tell the tool what you see in them.

---

### ⚠️ Medical Disclaimer

Please understand: This tool is **only meant to help you think about possibilities**. It is **NOT** a substitute for a real veterinarian looking at the horse and making a professional diagnosis. **Always, always, always talk to a qualified veterinarian** if you think a horse has a health problem.

---

## 🛠️ Getting Prerequisite Tools

Before you begin setting up the EOTRH Watch application, you'll need a few essential tools on your computer. This section guides you through installing Git (for downloading the project code), Python (the programming language for the tool, which includes pip for managing software packages), and Cursor (a code editor associated with `cursor.sh`).

### 1. Installing Git

*   **What is Git?** Git is a version control system. For our purposes, you'll use it to download (or "clone") the EOTRH Watch project files from the internet to your computer.

**How to install Git:**

*   **🪟 Windows:**
    1.  Go to the official Git website: [https://git-scm.com/download/win](https://git-scm.com/download/win)
    2.  Download the installer.
    3.  Run the installer. We recommend accepting the default options, especially ensuring "Git Bash Here" is included if you're comfortable with a Linux-like terminal, or that Git is added to your Command Prompt.
*   **🍎 macOS:**
    *   **Option 1 (Xcode Command Line Tools):** Open your Terminal (Applications > Utilities > Terminal) and type `xcode-select --install`. If Git is not already installed, you'll be prompted to install the command line tools, which include Git.
    *   **Option 2 (Homebrew):** If you have Homebrew installed, open Terminal and type `brew install git`.
*   **🐧 Linux:**
    *   Open your terminal.
    *   For Debian/Ubuntu-based systems (like Ubuntu, Mint): `sudo apt update && sudo apt install git`
    *   For Fedora/RHEL-based systems (like Fedora, CentOS): `sudo dnf install git` or `sudo yum install git`

**Verify installation:** Open a new terminal/command prompt and type `git --version`. You should see the installed Git version.

### 2. Installing Python (and pip)

*   **What is Python?** Python is the main programming language that the EOTRH Watch tool is written in.
*   **What is pip?** Pip is the Python package manager. It comes with Python and is used to install other software pieces (called "packages") that EOTRH Watch needs.
*   The EOTRH Watch tool requires **Python version 3.9 or newer**.

**How to install Python (which includes pip):**

*   **🪟 Windows:**
    1.  Go to the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    2.  Download a Python installer for version 3.9 or newer.
    3.  Run the installer. **Very Important:** On the first screen of the installer, make sure to check the box that says **"Add Python to PATH"** or **"Add python.exe to PATH"** before clicking "Install Now".
*   **🍎 macOS:**
    *   macOS often comes with an older version of Python. It's best to install a newer version.
    1.  Go to the official Python website: [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/)
    2.  Download the macOS installer for Python 3.9 or newer.
    3.  Run the installer.
    *   Alternatively, if you use Homebrew: `brew install python`
*   **🐧 Linux:**
    *   Most Linux distributions come with Python 3, but you might need to ensure it's version 3.9+ and install `pip`.
    *   Open your terminal.
    *   For Debian/Ubuntu-based systems: `sudo apt update && sudo apt install python3 python3-pip python3-venv` (ensure `python3` points to 3.9+ or install a specific version).
    *   For Fedora/RHEL-based systems: `sudo dnf install python3 python3-pip` (or `sudo yum...`).
    *   You may need to use `python3` and `pip3` in commands instead of `python` and `pip`.

**Verify installation:**
Open a new terminal/command prompt and type:
```bash
python --version  # or python3 --version on some systems
pip --version     # or pip3 --version on some systems
```
You should see versions reported, with Python being 3.9 or higher.

### 3. Installing Cursor.sh

*   **What is Cursor and `cursor.sh`?** Cursor is an AI-powered code editor. The `cursor.sh` script is typically associated with launching or interacting with the Cursor editor from the command line, though its exact usage can depend on your specific setup and Cursor's features.

If the `cursor.sh` script or the Cursor editor is part of your required workflow for using or developing EOTRH Watch:

**How to install Cursor:**

1.  Go to the official Cursor website: [https://cursor.sh/](https://cursor.sh/)
2.  Download the installer appropriate for your operating system (Windows, macOS, or Linux).
3.  Run the downloaded installer and follow the on-screen instructions to install the Cursor application.
4.  Once installed, Cursor will be available as an application.
    *   For command-line access (which might involve a `cursor.sh` script or a `cursor` command if the editor adds itself to your system's PATH), refer to Cursor's own documentation. This might be necessary if you need to launch it or perform specific actions from the terminal.

**A note on code editors:** While a code editor like Cursor is very useful for viewing or modifying the source code of the EOTRH Watch tool (development), it is **generally not a runtime requirement for simply running the EOTRH Watch application** itself. The primary tools for running the application are Python and the Python packages installed via `pip`.

---

## 📋 System Requirements

Before you start, please make sure your computer has at least these things:

-   **Python:** You need version 3.9 or a newer one.
    *   *What is Python?* It's the main programming language that this EOTRH Watch tool is written in. Think of it as the language the computer needs to understand to run the tool.
-   **pip:** This is the Python package manager.
    *   *What is pip?* It's a helper tool that usually comes with Python. Its job is to download and install other software pieces (called "packages" or "libraries") that our EOTRH Watch tool needs to work.
-   **RAM (Memory):** Your computer needs at least 2 Gigabytes of RAM.
    *   *Why?* RAM is like your computer's short-term memory. The tool needs enough of this to run smoothly.
-   **Disk Space:** You need at least 500 Megabytes of free space on your computer's hard drive.
    *   *Why?* This space is for storing the EOTRH Watch tool's files and all the extra software pieces it depends on.

---

## 🚀 Installation Guide

Please follow these steps **very, very carefully** to get the EOTRH Watch application set up and working on your computer.

### 1. Get the Code: Clone the Repository

First, you need to download all the files that make up the EOTRH Watch tool. These files are stored online in a place called a "repository." We'll use a tool called `git` to do this. (If you haven't installed Git yet, please see the "Getting Prerequisite Tools" section above).

Open your **terminal** or **command prompt**.
*   *What's a terminal/command prompt?* This is a window where you can type commands directly to your computer.
    *   On Windows, you might search for "Command Prompt" or "PowerShell" in your Start Menu.
    *   On macOS or Linux, it's usually called "Terminal" (you can find it in your applications).

Once your terminal is open, type the following commands one by one, pressing Enter after each one:

```bash
# This command tells git to download (clone) the project files from the given internet address.
# It will create a new folder on your computer named 'eotrh' and put all the files inside it.
git clone https://github.com/yago-mendoza/eotrh.git

# This command tells your terminal to move into the 'eotrh' folder that was just created.
# 'cd' stands for 'change directory'.
cd eotrh
```
After running `cd eotrh`, your terminal should now be "inside" that folder.

### 2. Create and Activate a Virtual Environment

A **virtual environment** is a super important step. Think of it like creating a private, clean, and isolated "workspace" or "sandbox" just for this EOTRH Watch project on your computer. It makes sure that all the software pieces (called dependencies) needed for EOTRH Watch don't mess with any other Python projects you might have, or with your computer's main Python setup. And, importantly, other projects won't mess with EOTRH Watch. (Ensure you have Python 3.9+ and pip installed as described in "Getting Prerequisite Tools" and "System Requirements").

*   **Why do this?** It's like giving this project its own dedicated toolbox. This stops different tools from different projects from clashing with each other if they need different versions of the same tool. It also keeps your main computer system clean.

**🪟 If you are using Windows:**
In your terminal (make sure you are still "inside" the `eotrh` folder from the previous step):
```bash
# This command tells Python to create a new virtual environment.
# We're naming this environment 'venv', and it will appear as a new folder called 'venv' inside your 'eotrh' project folder.
python -m venv venv

# This command "turns on" or "activates" the virtual environment you just created.
# After you run this, you should see (venv) written at the very beginning of your terminal's command line prompt.
# This (venv) tells you that the virtual environment is active and ready.
.\venv\Scripts\activate
```

**🐧 If you are using Linux or macOS:**
In your terminal (make sure you are still "inside" the `eotrh` folder):
```bash
# This command tells Python (specifically python3 on these systems) to create a new virtual environment.
# We're naming this environment 'venv', and it will appear as a new folder called 'venv' inside your 'eotrh' project folder.
python3 -m venv venv

# This command "turns on" or "activates" the virtual environment.
# After you run this, you should see (venv) written at the very beginning of your terminal's command line prompt.
# This (venv) tells you that the virtual environment is active.
source venv/bin/activate
```
**Very Important:** Keep this terminal window open! And make sure the virtual environment stays active (you can tell because you'll see `(venv)` at the start of your terminal prompt). If you accidentally close the terminal, you'll need to open it again, navigate back into the `eotrh` folder (using `cd eotrh`), and then reactivate the environment using the activate command for your system.

### 3. Install Required Software Packages (Dependencies)

Now that your special virtual environment "workspace" is active, you need to install all the specific software libraries and tools that EOTRH Watch relies on to work properly. These are all listed in a special file called `requirements.txt` that came with the project files. (This step uses `pip`, which should be available if you installed Python correctly).

Make sure you are still inside the `eotrh` folder in your terminal, and that your virtual environment is active (you must see `(venv)` at the beginning of your terminal prompt).

Run the following command:
```bash
# This command tells 'pip' (the Python package installer) to read the 'requirements.txt' file.
# Pip will then download and install all the software packages listed in that file.
# These packages will be installed ONLY inside your active 'venv' virtual environment, keeping them separate.
pip install -r requirements.txt
```

✅ **What if something goes wrong here? If you see errors, or if later on it seems like some software pieces are missing:**
Sometimes, an automatic installation might hit a snag. You can try installing the main packages one by one. This can help pinpoint if a specific package is causing trouble.
Make sure your virtual environment is still active (`(venv)` is in your prompt), then type:
```bash
pip install fastapi uvicorn jinja2 python-multipart opencv-python scikit-image EntropyHub
```
This command tells `pip` to install each of these specific packages.

---

## ▶️ Running the Application

Once you've successfully completed all the steps above, and your virtual environment is still active (you can see `(venv)` in your terminal prompt):

### 1. Start the Web Server

EOTRH Watch is a web application, which means it works like a mini-website running on your own computer. To make this website "live," it needs a web server program. We use a server called `uvicorn` for this.

In your terminal (remember, you should still be in the `eotrh` folder, and the `(venv)` should be showing in your prompt), run this command:
```bash
# This command starts the Uvicorn web server.
# 'main:app' tells Uvicorn: "Look for a file named 'main.py'. Inside that file, find a thing named 'app' – that's the application you need to run."
# '--reload' is a handy option for developers. It makes the server automatically restart if you change any of the code files.
# For just running the app, --reload is optional, but it doesn't hurt.
uvicorn main:app --reload
```
After you press Enter, you should see some messages pop up in your terminal. This means the server is starting up. Look for a line that says something like:
`INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`
This tells you the server is running and where to find the application. `http://127.0.0.1:8000` is the web address for the application on your local computer.

### 2. Open EOTRH Watch in Your Web Browser

Once the server is running (you'll see the message above in your terminal, and the terminal will seem "busy" running the server), it's time to see the application!

Open your favorite program for browsing the internet (like Google Chrome, Mozilla Firefox, Microsoft Edge, or Apple Safari).

In the **address bar** at the very top of the browser window (this is where you usually type website addresses like `www.google.com`), type the following web address *exactly* as it appears here and then press Enter:
```
http://127.0.0.1:8000
```
You should now see the main page of the EOTRH Watch application load up in your browser window!

---

## 🗂️ Project Structure

If you're curious and want to look at how the project files are organized, here's a map. This can be helpful if you want to understand where different parts of the code live:
```text
eotrh/                      # This is the main folder for the project.
├── main.py                 # The main brain of the application. This is where the FastAPI web server starts, and it defines the different "pages" or "endpoints" of the website.
├── config.py               # Contains settings and configurations for how the application should behave.
├── schemas.py              # Pydantic data models. These define the structure of data that the application expects (e.g., what information should be in a request from your browser).
├── services/               # This folder contains the "thinking" parts of the application – its core logic.
│   ├── image_analysis.py   # The code that handles looking at images (texture analysis, etc.).
│   ├── options.py          # Defines the lists of possible clinical signs and radiological signs you can choose from in the tool.
│   └── scoring.py          # Contains the rules and calculations for how the diagnostic score is determined.
├── utils/                  # A place for small helper tools and functions.
│   └── i18n.py             # A helper for handling different languages (internationalization), like for translations.
├── templates/              # This folder contains the HTML "blueprints" for the web pages.
│   └── index.html          # This is the main HTML file that creates the page you see in your web browser. It's like the skeleton of the webpage, and Jinja2 (a templating engine) fills it with dynamic content.
├── static/                 # This folder holds files that don't change, like CSS files (for styling how the website looks), JavaScript files (for making the website interactive), and any images used by the website itself.
├── locales/                # Contains files for translating the application into different languages.
│   └── ca.json             # For example, this might be a file with translations for the Catalan language.
├── requirements.txt        # The "shopping list" of all the external Python software packages that this project needs to run.
└── README.md               # This very file you are reading right now, which explains the project.
```

---

## 📦 Key Dependencies (Software Packages Used)

Here's a quick look at the most important external Python software packages (like special tools or libraries) that this EOTRH Watch project uses to do its job:

| Package          | Purpose                                                            | *In simpler terms...*                                  |
|------------------|--------------------------------------------------------------------|--------------------------------------------------------|
| `fastapi`        | The core web framework used to build the API and application.      | The main set of tools for building the website itself. |
| `uvicorn`        | An ASGI server that runs the FastAPI application.                  | The "waiter" that serves up the website from your computer. |
| `jinja2`         | A templating engine used to generate HTML pages dynamically.       | Helps create the web pages you see by filling in templates with information. |
| `python-multipart` | Enables handling of file uploads (like images) via HTML forms.   | Lets the website receive files (like your images) that you upload through a form. |
| `opencv-python`  | (OpenCV) A powerful library for computer vision and image processing. | A big toolbox for working with images – analyzing them, changing them, etc. |
| `scikit-image`   | Provides additional tools and algorithms for image analysis.       | More specialized tools for advanced image checking.    |
| `EntropyHub`     | A library for calculating various entropy measures, used here for image texture analysis. | A tool used to measure the "complexity" or "randomness" of textures in the images. |

---

## 🧪 Troubleshooting Common Issues

If you run into problems while setting up or running the application, here are some common issues and how to fix them:

❗ **Error: `uvicorn: command not found` (or you might see this for `python` or `pip` too)**

*   **Possible Cause 1: Your virtual environment is not active.** The commands like `uvicorn`, `python`, and `pip` that you need are often linked to the active virtual environment. If it's not active, your terminal might not know where to find them.
    *   **How to Fix:** Look at your terminal prompt. Do you see `(venv)` at the very beginning? If not, it means your virtual environment isn't active.
        1.  Make sure you are in the `eotrh` project folder in your terminal (use `cd eotrh` if you're not).
        2.  Then, reactivate the environment:
            *   On Windows: `.\venv\Scripts\activate`
            *   On Linux/macOS: `source venv/bin/activate`
        3.  Once `(venv)` appears, try the command again.
*   **Possible Cause 2: `uvicorn` (or another package) didn't install correctly inside the virtual environment.** Or, Git, Python, or pip might not be installed correctly or not be in your system's PATH (see the "Getting Prerequisite Tools" section).
    *   **How to Fix:** Make sure your virtual environment is active (see above). Then, try to install `uvicorn` specifically:
        ```bash
        pip install uvicorn
        ```
        After it installs, try running the `uvicorn main:app --reload` command again. If the issue is with `python`, `pip`, or `git` commands themselves, revisit the "Getting Prerequisite Tools" section to ensure they are installed correctly and accessible from your terminal.

❗ **Error: `fastapi` is missing, or "ModuleNotFoundError: No module named 'fastapi'" (or similar for `jinja2`, `opencv-python`, etc.) when you try to run `uvicorn`**

*   **Possible Cause:** The Python software packages that EOTRH Watch needs were not installed correctly, or they were installed outside of your active virtual environment. The program is trying to find a tool (a 'module') but can't.
    *   **How to Fix 1:** First, double-check that your virtual environment is active (you must see `(venv)` in your terminal prompt). If it is, try running the installation from the `requirements.txt` file again:
        ```bash
        pip install -r requirements.txt
        ```
    *   **How to Fix 2:** If Fix 1 doesn't work, or if you still have problems, try installing the packages one by one (again, make sure the virtual environment is active):
        ```bash
        pip install fastapi uvicorn jinja2 python-multipart opencv-python scikit-image EntropyHub
        ```
    *   After trying these fixes, attempt to run the `uvicorn main:app --reload` command again.

---

## 📄 License

This project is shared under the MIT License. This license basically says you can use, copy, change, and share this software freely, even for commercial purposes, as long as you include the original copyright and license notice. You can find more details in a file named `LICENSE` that should be included with the project files. Original development repo: [https://github.com/yago-mendoza/eotrh](https://github.com/yago-mendoza/eotrh)

---

## 📚 Citation

If you find this tool or the methods it uses helpful for your research or work, please think about mentioning (citing) these publications:

*   Górski, K. (2022). Equine Odontoclastic Tooth Resorption and Hypercementosis: Diagnostic Criteria and Imaging.
*   Tretow, J., et al. (2025). Multimodal Analysis for EOTRH Detection Using Computer-Assisted Tools.
