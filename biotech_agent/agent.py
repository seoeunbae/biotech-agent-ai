from google.adk.agents import Agent, LoopAgent
from .subagents.normalization.agent import create_agent as create_normalization_agent
from .subagents.gene_analysis.agent import create_agent as create_gene_analysis_agent
from .subagents.insight_synthesis.agent import create_agent as create_insight_agent



def create_root_agent(model: str = "gemini-2.5-pro") -> Agent:
    normalization_agent = create_normalization_agent(model)
    gene_analysis_agent = create_gene_analysis_agent(model)
    insight_agent = create_insight_agent(model)
    refinement_loop = LoopAgent(
        name="RefinementLoop",
        # Agent order is crucial: Critique first, then Refine/Exit
        sub_agents=[
            normalization_agent, gene_analysis_agent, insight_agent
        ],
        max_iterations=5
    )

    return Agent(
        name="biotech_root_agent",
        model=model,
        sub_agents=[refinement_loop],
        instruction="""
    You are a sophisticated BioTech Research Assistant.
    Your mission is to assist users with drug discovery tasks by orchestrating a team of specialized subagents.

    Your workflow generally follows these steps:
    1.  **Normalization**: If the user mentions a disease or drug, first delegate to the `normalization_agent` to get standard IDs.
    2.  **Gene Analysis**: Use the `gene_analysis_agent` to find target genes associated with the normalized disease or to analyze specific genes.
    3.  **Insight Synthesis**: Use the `insight_synthesis_agent` to check for regulatory information (FDA approvals, etc.) for the identified drugs or targets.

    Always coordinate the flow of information between these agents.
    For example, if Normalization returns an EFO ID, pass that ID to Gene Analysis.
    If Gene Analysis returns a list of genes, you might ask Insight Synthesis to check if there are existing drugs targeting those genes.

    Provide a comprehensive final answer to the user based on the combined findings.
    """,
        description="Root agent for BioTech Drug Discovery that orchestrates specialized subagents."
    )


# Expose the agent instance for ADK to pick up if needed, though usually ADK runs via a script or adk web pointing to the file.
# We'll instantiate it here.
root_agent = create_root_agent()


