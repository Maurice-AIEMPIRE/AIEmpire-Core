# 02 INSTALLING OLLAMA PYTHON.MD

```markdown

# Module 2: Installing Ollama Python for Advanced Machine Learning Tasks


## Prerequisites:

- Basic understanding of command-line operations.

- Existing installation and configuration of a Linux-based operating system (Ubuntu recommended).

- Familiarity with virtual environments in python.


## Objectives:


1. Install necessary dependencies on Ubuntu to set up the environment for ollama.

2. Create an isolated Python 3.x virtual environment specifically tailored for working with Ollama models within your machine learning projects.


### Step-by-Step Guide:

#### A. System Update and Dependency Installation


Begin by updating system packages, ensuring you have access to recent versions of all dependencies:


```bash

sudo apt-get update && sudo apt-get upgrade -y

```

Install essential build tools for compiling Python extensions if not already available on your machine.


```bash

sudo apt install build-essential libssl-dev zlib1g-dev curl ca-certificates

```

#### B. Virtual Environment Setup


Activate a new virtual environment by specifying the desired version of python:


Choose between `python3.x` or use 'python' for Python 2.x compatibility, as needed.


```bash

# Replace with your preferred path and command if you are using an alternative to /usr/bin/python:

cd ~/projects/ai-blueprint/

virtualenv -p python3.9 my_ollama_env # This creates a virtual environment named `my_ollama_env`

source my_ollama_env/bin/activate

```


#### C. Ollama Installation via pip 


Install ollama within the newly created and activated Python 3.x virtual environment:


Ensure you're using up-to-date versions of packages with pip.


```bash

pip install --upgrade pip setuptools wheel # Upgrading to latest tools for future-proof installation

pip list | grep ollama || pip install ollama==0.4.5 # Replace version number as per the current release
```

#### D. Testing Ollama Installation


Confirm that ollama has been installed correctly by invoking it through your Python interpreter:


```bash

python -m ollama --version  # This should output the installed version of Ollama.

# Run a sample command to test if it's working properly:

ollama run example_command
```

Replace `example_command` with an actual command available within the ollama library.


### Conclusion and Next Steps


Once you have successfully completed these steps, your environment will be ready for advanced machine learning tasks leveraging the power of Ollama models. You can now start integrating Ollama into larger projects or continue exploring its capabilities through practical examples.

```