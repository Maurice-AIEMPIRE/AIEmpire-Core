# 02 INSTALLING OLLAMA PYTHON.MD

# Course Module: Installing Ollama Python

Welcome to the second module of our comprehensive course on AI Setup Blueprint. In today's lesson, we will dive into installing Ollama with its dedicated python environment.

## Prerequisites
Before proceeding further:

1. Basic knowledge in using terminal and command prompt is mandatory.
2. Ensure you have sudo privileges or are operating as an administrator/root user to install software packages at your system level.


Let's get started!

### Step 1: Install Python (if not installed)

First, verify if Python has been successfully added on your machine by typing:

```bash
python3 --version
```

If the response is something like `Python 3.x.y`, you're good to go. Otherwise, install it following these steps.

#### Installing via Terminal

For Ubuntu/Debian-based systems:
1. Open terminal and run: 

    ```sh
    sudo apt update && \
        sudo apt upgrade -y; \ 
        sudo apt-get dist-upgrade;
    ```

2. Install Python using the command:

   ```
   sudo apt install python3-pip -y;
   ```

For CentOS/RHEL-based systems:
1. Open terminal and run: 

    ```sh
    yum update && \
      yum upgrade; \ 
      yum repolist all;

    sudo rpm --import https://dl.fedoraproject.org/pub/epel/rpm-sign/key-E0138031023FD93A;
    
    sudo dnf install python3-pip -y;
    ```

### Step 2: Install Ollama using Pip

Next up, we'll set up the Python environment for installing ollama.

1. Open terminal and run:

   ```sh
   pip install --upgrade pip setuptools wheel; \
       wget https://raw.githubusercontent.com/ollama-community/base/main/install.sh -O ./install_ollama.sh;
   
   chmod +x ./install_ollama.sh && \
    sudo bash ./install_ollama.sh;

   # Verify installation:
   ollama version
   ```

### Step 3: Setting Up Virtual Environment

Now, we'll set up a virtual environment for our project to avoid any conflicts with other packages.

1. Open terminal and run:

   ```bash
   python3 -m venv /path/to/new/virtual/environment/directory
   source /path/to/new/virtual/environment/directory/bin/activate;
   
   pip install ollama==x.y.z; # replace x.y.z by the version you want to use.
   ```

### Step 4: Validate Your Installation

1. Run a test command:

    ```bash
    ollama --help
    ```
2. You should see an output indicating Ollama has been installed correctly.

Congratulations! You've successfully set up your Python environment for using OLLAMA by following the steps mentioned above meticulously.


In this module, we have covered how to install python3-pip and pip setuptools wheel packages; also installing ollama with a virtual environment from its official repository. The installation of Ollama is an integral part in building AI models that will help us make better predictions using machine learning techniques.

Keep practicing these steps until you're confident about your proficiency level before moving on to our next lesson.


Happy Learning!