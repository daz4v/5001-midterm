"""Paper 2 use case development: Multi-Agent Orchestration (Section 8.2.1).

Selected use case:
- Hierarchical coordination where a manager agent delegates to specialized workers.
"""

from orchestral import Agent, define_tool
from orchestral.llm import Ollama

MODEL_NAME = "devstral-small-2:24b-cloud"


@define_tool()
def literature_search_tool(topic: str) -> str:
    """Return a small, structured candidate-paper list for a topic."""
    # In a production system this would call arXiv, Semantic Scholar, or CrossRef.
    papers = [
        {
            "title": "A Survey of Multi-Agent LLM Systems",
            "year": 2024,
            "focus": "Architectures, communication patterns, and coordination",
        },
        {
            "title": "Role-Based Agent Collaboration in Research Automation",
            "year": 2024,
            "focus": "Task decomposition and manager-worker orchestration",
        },
        {
            "title": "Evaluation of Agent Tool-Use Reliability",
            "year": 2025,
            "focus": "Tool-calling accuracy and reproducibility",
        },
    ]
    lines = [f"Topic: {topic}", "Candidate papers:"]
    for idx, paper in enumerate(papers, start=1):
        lines.append(
            f"{idx}. {paper['title']} ({paper['year']}) - {paper['focus']}"
        )
    return "\n".join(lines)


@define_tool()
def paper_analysis_tool(paper_list_text: str) -> str:
    """Extract findings from the candidate-paper list text."""
    analysis = [
        "Main findings:",
        "1. Manager-worker coordination is the dominant multi-agent pattern.",
        "2. Specialized tool sets improve quality and reduce prompt ambiguity.",
        "3. Reproducibility improves when tool calls are explicit and logged.",
        "4. Cost and context limits remain key constraints in long workflows.",
        "Evidence source text:",
        paper_list_text,
    ]
    return "\n".join(analysis)


@define_tool()
def summary_writer_tool(analysis_text: str) -> str:
    """Generate a short final report from analysis output."""
    return "\n".join(
        [
            "Final report:",
            "This multi-agent workflow uses hierarchical orchestration.",
            "A manager agent delegates literature search and analysis to specialized worker agents.",
            "The manager then composes a final summary with explicit traceable steps.",
            "",
            "Detailed analysis:",
            analysis_text,
        ]
    )


search_agent = Agent(
    llm=Ollama(model=MODEL_NAME),
    tools=[literature_search_tool],
    system_prompt=(
        "You are a literature search specialist. "
        "Use literature_search_tool to provide candidate papers and scope coverage."
    ),
)

analysis_agent = Agent(
    llm=Ollama(model=MODEL_NAME),
    tools=[paper_analysis_tool],
    system_prompt=(
        "You are an analysis specialist. "
        "Use paper_analysis_tool to extract clear findings and limitations."
    ),
)

summary_agent = Agent(
    llm=Ollama(model=MODEL_NAME),
    tools=[summary_writer_tool],
    system_prompt=(
        "You are a scientific writing specialist. "
        "Use summary_writer_tool to produce a concise, submission-ready report."
    ),
)


@define_tool()
def run_search_agent(topic: str) -> str:
    """Invoke the search worker agent."""
    return search_agent.run(f"Find candidate papers for: {topic}")


@define_tool()
def run_analysis_agent(search_output: str) -> str:
    """Invoke the analysis worker agent."""
    return analysis_agent.run(
        "Analyze this candidate paper list and extract findings:\n" + search_output
    )


@define_tool()
def run_summary_agent(analysis_output: str) -> str:
    """Invoke the summary worker agent."""
    return summary_agent.run(
        "Write a final report from this analysis:\n" + analysis_output
    )


manager_agent = Agent(
    llm=Ollama(model=MODEL_NAME),
    tools=[run_search_agent, run_analysis_agent, run_summary_agent],
    system_prompt=(
        "You are the manager agent in a hierarchical multi-agent system. "
        "Follow this order strictly: \n"
        "1) run_search_agent \n"
        "2) run_analysis_agent \n"
        "3) run_summary_agent \n"
        "Return the final report plus a short delegation trace."
    ),
)


def develop_use_case(topic: str) -> str:
    """Execute the selected Paper 2 multi-agent use case end-to-end."""
    return manager_agent.run(
        f"Develop the selected use case for topic: {topic}. "
        "Show the final report and brief trace of worker delegation."
    )


if __name__ == "__main__":
    selected_topic = "AI multi-agent systems for scientific research workflows"
    output = develop_use_case(selected_topic)
    print(output)