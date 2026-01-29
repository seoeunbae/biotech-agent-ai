from typing import Any, AsyncGenerator
from google.adk.agents import Agent, LoopAgent
from biotech_agent.subagents.normalization.agent import create_agent as create_normalization_agent
from biotech_agent.subagents.gene_analysis.agent import create_agent as create_gene_analysis_agent
from biotech_agent.subagents.insight_synthesis.agent import create_agent as create_insight_agent

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

    Provide a comprehensive final answer to the combined findings.
    """,
        description="Root agent for BioTech Drug Discovery that orchestrates specialized subagents."
    )


# Expose the agent instance for ADK to pick up if needed, though usually ADK runs via a script or adk web pointing to the file.
# We'll instantiate it here.
# root_agent = create_root_agent()

# class BioTechAgent:
    # def __init__(self, model: str = "gemini-2.5-pro"):
        # 초기화 시점에 ADK 에이전트를 생성하여 들고 있습니다.
root_agent = create_root_agent(model="gemini-2.5-pro")

def query(self, input: str) -> dict:
    """
    [표준 메서드] 
    클라이언트에서 remote_agent.query(input="...") 호출 시 
    실제로 엔진 내부에서 실행되는 진입점입니다.
    """
    # 1. 입력 값 전처리 (필요시)
    print(f"받은 질문: {input}")

    # 2. 실제 비즈니스 로직 실행 
    # (비동기 에이전트라면 여기서 asyncio.run 등으로 호출)
    import asyncio
    response = asyncio.run(self.root_agent.run(input))


    # 3. 결과 반환 (JSON 직렬화가 가능한 형태 권장)
    return {
        "answer": response,
        "status": "success",
        "model_used": self.model
    }

# 비동기 단일 질의 함수 추가
async def async_query(self, input: str, **kwargs) -> Any:
    """
    SDK에서 await deployed_agent.async_query(input="...")로 호출 가능하게 함
    """
    # ADK Agent의 비동기 실행 메서드 (보통 .run 또는 .arun)
    return await self.root_agent.run(input)

# 비동기 스트리밍 함수 추가
async def async_stream_query(self, input: str, **kwargs) -> AsyncGenerator[Any, None]:
    """
    SDK에서 async for chunk in deployed_agent.async_stream_query(...)로 호출 가능하게 함
    """
    async for chunk in self.root_agent.stream(input):
        yield chunk

# 배포용 인스턴스 생성
#  = BioTechAgent()

