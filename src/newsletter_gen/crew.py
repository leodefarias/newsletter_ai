from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from newsletter_gen.tools.research import SearchAndContents, FindSimilar, GetContents
from datetime import datetime
import streamlit as st
from typing import Union, List, Tuple, Dict
from langchain_core.agents import AgentFinish
import json
import os
from dotenv import load_dotenv

# Import AgentAction
from crewai.agents.parser import AgentAction

# Load environment variables from the .env file
load_dotenv()

@CrewBase
class NewsletterGenCrew:
    """NewsletterGen crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        # Initialize the attribute to store the newsletter file path
        self.newsletter_output_file = ""

    def step_callback(self, agent_output: Union[str, List[Tuple[Dict, str]], AgentFinish, AgentAction], agent_name: str, *args):
        """Callback function to handle agent output and display results in Streamlit."""
        
        with st.chat_message("AI"):
            # If the output is a string, possibly JSON
            if isinstance(agent_output, str):
                try:
                    agent_output = json.loads(agent_output)
                except json.JSONDecodeError:
                    st.write(agent_output)
                    return

            # If the output is an instance of AgentAction
            if isinstance(agent_output, AgentAction):
                st.write(f"**Agent Name:** {agent_name}")
                st.write(f"**Thought Process:** {agent_output.thought}")
                st.write(f"**Tool Used:** {agent_output.tool}")
                st.write(f"**Tool Input:** {agent_output.tool_input}")
                with st.expander("Show Observation"):
                    st.write(f"**Text:** {agent_output.text}")

            # If the output is a list of actions and descriptions
            elif isinstance(agent_output, list) and all(isinstance(item, tuple) for item in agent_output):
                for action, description in agent_output:
                    tool = getattr(action, 'tool', 'Unknown')
                    tool_input = getattr(action, 'tool_input', 'Unknown')
                    log = getattr(action, 'log', 'No log available')
                    
                    st.write(f"**Agent Name:** {agent_name}")
                    st.write(f"**Tool Used:** {tool}")
                    st.write(f"**Tool Input:** {tool_input}")
                    st.write(f"**Log:** {log}")
                    if hasattr(agent_output, 'observation') and agent_output.observation:
                        with st.expander("Show Observation"):
                            st.markdown(f"**Observation:**\n\n{description}")

            # If the output is AgentFinish (task completed)
            elif isinstance(agent_output, AgentFinish):
                st.write(f"**Agent Name:** {agent_name}")
                output = agent_output.return_values
                st.write(f"**Task Completed!**\n\n{output.get('output', 'No output available')}")

            # Default handling for unexpected formats
            else:
                st.write(f"Unexpected output format: {type(agent_output)}")
                st.write(agent_output)

    @agent
    def researcher(self) -> Agent:
        """Creates a research agent using the specified tools."""
        return Agent(
            config=self.agents_config["researcher"],
            tools=[SearchAndContents(), FindSimilar(), GetContents()],
            verbose=True,
            step_callback=lambda step: self.step_callback(step, "Research Agent"),
        )

    @agent
    def editor(self) -> Agent:
        """Creates an editor agent using the specified tools."""
        return Agent(
            config=self.agents_config["editor"],
            verbose=True,
            tools=[SearchAndContents(), FindSimilar(), GetContents()],
            step_callback=lambda step: self.step_callback(step, "Chief Editor"),
        )

    @agent
    def designer(self) -> Agent:
        """Creates a designer agent to write content in HTML."""
        return Agent(
            config=self.agents_config["designer"],
            verbose=True,
            allow_delegation=False,
            step_callback=lambda step: self.step_callback(step, "HTML Writer"),
        )

    @task
    def research_task(self) -> Task:
        """Task for the research agent to gather content."""
        return Task(
            config=self.tasks_config["research_task"],
            agent=self.researcher(),
            output_file=f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_research_task.md",
        )

    @task
    def edit_task(self) -> Task:
        """Task for the editor agent to refine the content."""
        return Task(
            config=self.tasks_config["edit_task"],
            agent=self.editor(),
            output_file=f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_edit_task.md",
        )

    @task
    def newsletter_task(self) -> Task:
        """Task for the designer agent to create the newsletter in HTML format."""
        output_file = f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_newsletter_task.html"
        self.newsletter_output_file = output_file  # Store the generated file path
        return Task(
            config=self.tasks_config["newsletter_task"],
            agent=self.designer(),
            output_file=output_file,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the team to manage tasks and agents."""
        return Crew(
            agents=self.agents,  # Automatically created by @agent decorator
            tasks=self.tasks,  # Automatically created by @task decorator
            process=Process.sequential,  # Sequential process (one task after another)
            verbose=True,
        )
