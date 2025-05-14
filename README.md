# AI-Powered Computational Infrastructure Configuration Tool

## Overview

Accessing computational infrastructures is becoming increasingly complex, requiring manual effort to configure and deploy platforms efficiently. This project introduces an AI-powered tool that automates the configuration of computing platforms, by analyzing the codes and predicting the required resource requirements with the LLM (gpt-4) by passing the source of the project (github repository link).

!["The architecture of the project"](/project/llm-analyzer_arch.png)

### Key Features

- the estimated memory usage, CPU usage, and network bandwidth.

- loop feedback loop to adjust the configurated resources if there is a change in the source code and for agent analysis references.

- Source Code Integration extracting: prompting the user to provide the source code of the project (github repository link) and extracting the required resources.

- generate a configuration file: generating a configuration file based on the extracted information.

- User-friendly interface: providing a simple and intuitive interface for users to interact with the tool by asking agent.

### Technical Requirements

The project is built using the following technologies:

- Python verion above 3.9.


### Getting Started

#### Prerequisites:

- Install Python (>=3.9)

#### Usage

- create a virtual environment (optional but recommended) to avoid dependency conflicts:

    ``` python -m venv envpyAi ```

- Clone the repository:

    ``` git clone https://github.com/your-repo/ai-computing-tool.git ```

- Navigate to the project directory:

    ``` cd ai-computing-tool ```

- Install the dependecies from the requirements file:

    ``` pip install -r requirements.txt ```

- Set up your OpenAI API key in .env file (create it if it doesn't exist):

    - assign the keys variable OPEN_api_KEYS

- Start the AI-powered configuration tool:

    ``` python -m main ```

#### Contributing

###### Kindly do the following: 
- Fork the repository

- Create a feature branch (git checkout -b feature-branch)

- Commit your changes (git commit -m 'Add new feature')

- Push to the branch (git push origin feature-branch)

- Submit a Pull Request

