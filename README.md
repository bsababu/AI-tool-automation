# AI-Powered Computational Infrastructure Configuration Tool

## Overview

Accessing computational infrastructures is becoming increasingly complex, requiring manual effort to configure and deploy platforms efficiently. This project introduces an AI-powered tool that automates the configuration of computing platforms, by analyzing the codes and predicting the required resource requirements with the LLM (gpt-4) by passing the source of the project (github repository link).

!["The architecture of the project"](/architecture.png)

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

1. create a virtual environment (optional but recommended) to avoid dependency conflicts:

    ``` python -m venv envpyAi ```

2. Clone the repository:

    ``` git clone https://github.com/your-repo/ai-computing-tool.git ```

3. Navigate to the project directory:

    ``` cd ai-computing-tool ```

4. Install the dependecies from the requirements file:

    ``` pip install -r requirements.txt ```

5. Set up your OpenAI API key in .env file (create it if it doesn't exist):

    - assign the keys variable OPEN_api_KEYS

6. Start the AI-powered configuration tool:

    ``` python -m main ```


#### For Web Interface

After step 5 from above ☝️, navigate to project/web directory:

``` cd project/web ```

Then run the following command to start the web server:

``` python -m run_panel_server```

!["The chat interface"](project/web/crewAI.png)


#### For Test Cases
To run the test cases, navigate to the project directory and run:

``` python -m unittest project/test/ ```

#### Contributing

###### Kindly do the following: 
- Fork the repository

- Create a feature branch (git checkout -b feature-branch)

- Commit your changes (git commit -m 'Add new feature')

- Push to the branch (git push origin feature-branch)

- Submit a Pull Request

