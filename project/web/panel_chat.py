import os
import datetime
import panel as pn
import asyncio
from dotenv import load_dotenv
from crewai import Agent, Process, Task, Crew


from project.RL.db_feedback import summarize_analysis
from project.conversational import GenerateKubernetesConfigTool, GenerateTerraformConfigTool, GetChangeLogsTool, GetLatestAnalysisTool, SummarizeAnalysisTool
from project.main import analyzer_main

load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")
llm_api_key = os.getenv("OPENAI_API_KEY")

pn.extension()

def create_analysis_agent():
    return Agent(
        role="Analyser",
        goal="Assist users by answering queries about repository analysis results and generating cloud configurations.",
        backstory=(
            "You are a DevOps assistant specialized in analyzing software repositories to estimate resource requirements "
            "and generate cloud configurations. You can query a database to retrieve analysis results, explain changes, "
            "and generate Kubernetes or Terraform configurations on demand."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[
            GetLatestAnalysisTool(),
            GetChangeLogsTool(),
            GenerateKubernetesConfigTool(),
            GenerateTerraformConfigTool(),
            SummarizeAnalysisTool(),
        ],
    )

# Create a Panel chat interface
class ChatInterface:
    def __init__(self):
        self.agent = create_analysis_agent()
        self.repo_url = None
        self.analysis_result = None
        
        # Create Panel widgets
        self.repo_input = pn.widgets.TextInput(
            name="GitHub Repository URL", 
            placeholder="Enter the GitHub repository .git URL"
        )
        self.analyze_button = pn.widgets.Button(
            name="Analyze Repository", 
            button_type="primary",
            width=200
            
        )
        self.analyze_button.on_click(self.analyze_repository)
        
        self.chat_interface = pn.chat.ChatInterface(
            callback=self.callback,
            show_rerun=True,
            show_undo=False,
            show_clear=True,
            sizing_mode="stretch_width",
            min_height=500,
            disabled=True
        )
        
        self.status = pn.indicators.LoadingSpinner(value=False, width=20, height=20)
        self.status_text = pn.pane.Markdown("", width=400)
        
        # Layout
        self.layout = pn.Column(
            pn.pane.Markdown("# Code Analyzer Assistant 🖐", sizing_mode="stretch_width"),
            pn.pane.Markdown(
                "This tool analyzes GitHub repositories to estimate resource requirements and generate cloud configurations. "
                "You can ask questions about the analysis results or request specific configurations.",
                sizing_mode="stretch_width"
            ),
            pn.Row(self.repo_input, self.analyze_button),
            pn.Row(self.status, self.status_text),
            pn.layout.Divider(),
            self.chat_interface,
            sizing_mode="stretch_width"
        )
    
    async def callback(self, contents, user, instance):
        """Callback for the chat interface"""
        if not self.repo_url:
            return "Please analyze a repository first."
        
        self.status.value = True
        self.status_text.object = "Processing your query..."
        
        try:
            # Create a dynamic task based on user input
            task = Task(
                description=(
                    f"Answer the user's query: '{contents}' for repository: '{self.repo_url}'. "
                    "Use the available tools to retrieve analysis results, change logs, or generate Kubernetes or Terraform configurations. "
                    "Provide a clear, short and concise response in natural language."
                ),
                agent=self.agent,
                expected_output="A specific natural language response answering the user's query",
            )
            
            # Execute the task
            crew = Crew(
                agents=[self.agent], 
                tasks=[task], 
                process=Process.sequential,
                verbose=True,

            )
            
            result = await asyncio.to_thread(crew.kickoff)
            
            self.status.value = False
            self.status_text.object = ""
            return result
        except Exception as e:
            self.status.value = False
            self.status_text.object = f"Error: {str(e)}"
            return f"Error processing query: {str(e)}"
    
    def analyze_repository(self, event):
        """Analyze the repository and enable the chat interface"""
        self.repo_url = self.repo_input.value.strip()
        if not self.repo_url:
            self.status_text.object = "Error: No URL provided or wrong url format."
            return
        
        self.status.value = True
        self.status_text.object = "Analyzing repository..."
        
        try:
            self.analysis_result = analyzer_main(self.repo_url, github_token, llm_api_key)
            
            if "error" in self.analysis_result:
                self.status.value = False
                self.status_text.object = f"Error: {self.analysis_result['error']}"
                return
            
            estimated = self.analysis_result["estimated"]
            
            self.status.value = False
            self.status_text.object = "Analysis complete! You can now ask questions about the repository."
            self.chat_interface.disabled = False
            
            summary = summarize_analysis(self.repo_url)
            welcome_message = f"""
            ## Analysis Complete!
            
            Repository: `{self.repo_url}`
            
            ### Summary:
            {summary}
            
            ### Example questions you can ask:
            - Show me the memory requirements for this repository
            - Why did CPU usage change for this repository?
            - Generate Kubernetes config for this repository
            - Generate Terraform config for this repository
            """
            
            self.chat_interface.send(
                welcome_message, 
                user="System", 
                respond=False
            )
            
        except Exception as e:
            self.status.value = False
            self.status_text.object = f"Error analyzing repository: {str(e)}"

def run_panel_interface():
    """Run the Panel interface"""
    chat_app = ChatInterface()
    return chat_app.layout

app = run_panel_interface()