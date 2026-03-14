"""Paper 2 use case development: Multi-Agent Orchestration (Section 8.2.1).

Selected use case:
Hierarchical coordination where a manager agent delegates to specialized workers.
"""

from orchestral import Agent, define_tool
from orchestral.llm import Ollama
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET

MODEL_NAME = "devstral-small-2:24b-cloud"


def as_text(value: object) -> str:
    """Convert agent/tool responses to plain text for safe composition."""
    if isinstance(value, str):
        return value
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return content
    return str(value)


def fetch_arxiv_papers(topic: str, max_results: int = 5) -> str:
    """Fetch real paper metadata from the public arXiv API."""
    query = quote_plus(topic)
    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query=all:{query}&start=0&max_results={max_results}"
    )

    try:
        with urlopen(url, timeout=20) as response:
            raw_xml = response.read()
    except Exception as exc:
        return (
            "arXiv API error: unable to fetch papers right now. "
            f"Details: {exc}"
        )

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        return f"arXiv API parse error: {exc}"

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)

    lines = [f"Topic: {topic}", "Candidate papers from arXiv API:"]
    if not entries:
        lines.append("No results found.")
        return "\n".join(lines)

    for idx, entry in enumerate(entries, start=1):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        summary = (
            entry.findtext("atom:summary", default="", namespaces=ns) or ""
        ).strip()
        published = (
            entry.findtext("atom:published", default="", namespaces=ns) or ""
        ).strip()
        year = published[:4] if len(published) >= 4 else "Unknown"

        authors = [
            (author.findtext("atom:name", default="", namespaces=ns) or "").strip()
            for author in entry.findall("atom:author", ns)
        ]
        authors_text = ", ".join(a for a in authors if a) or "Unknown authors"

        link = ""
        for candidate in entry.findall("atom:link", ns):
            href = candidate.attrib.get("href", "")
            if "arxiv.org/abs/" in href:
                link = href
                break
        if not link:
            link = (
                entry.findtext("atom:id", default="", namespaces=ns) or ""
            ).strip()

        lines.append(f"{idx}. {title} ({year})")
        lines.append(f"   Authors: {authors_text}")
        lines.append(f"   Link: {link}")
        lines.append(f"   Abstract: {summary[:280]}...")

    return "\n".join(lines)


@define_tool()
def literature_search_tool(topic: str) -> str:
    """Fetch real candidate papers from arXiv for a topic."""
    return fetch_arxiv_papers(topic=topic, max_results=5)


@define_tool()
def paper_analysis_tool(paper_list_text: str) -> str:
    """Pass the real paper list to the LLM for analysis."""
    return paper_list_text


@define_tool()
def summary_writer_tool(analysis_text: str) -> str:
    """Pass the analysis to the LLM to write a final report."""
    return analysis_text


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
        "You are a research analysis specialist. "
        "Call paper_analysis_tool to retrieve the paper list, then write a "
        "detailed analysis of those specific papers: key themes, findings, "
        "strengths, and limitations. Base everything on the actual papers provided."
    ),
)

summary_agent = Agent(
    llm=Ollama(model=MODEL_NAME),
    tools=[summary_writer_tool],
    system_prompt=(
        "You are a scientific writing specialist. "
        "Call summary_writer_tool to retrieve the analysis, then write a concise "
        "final report covering: what the papers say, key strengths, key weaknesses, "
        "and open questions in the field. Base everything on the actual analysis provided."
    ),
)


@define_tool()
def run_search_agent(topic: str) -> str:
    """Runs the search worker agent."""
    return run_search_worker(topic)


def run_search_worker(topic: str) -> str:
    """Search worker implementation."""
    # Deterministic path: always fetch real citations from arXiv API.
    return fetch_arxiv_papers(topic=topic, max_results=5)


@define_tool()
def run_analysis_agent(search_output: str) -> str:
    """Runs the analysis worker agent."""
    return run_analysis_worker(search_output)


def run_analysis_worker(search_output: str) -> str:
    """Analysis worker implementation."""
    return as_text(
        analysis_agent.run(
            "Analyze this candidate paper list and extract findings:\n"
            + as_text(search_output)
        )
    )


@define_tool()
def run_summary_agent(analysis_output: str) -> str:
    """Runs the summary worker agent."""
    return run_summary_worker(analysis_output)


def run_summary_worker(analysis_output: str) -> str:
    """Summary worker implementation."""
    return as_text(
        summary_agent.run(
            "Write a final report from this analysis:\n" + as_text(analysis_output)
        )
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
    """Execute the full multi agent workflow for the given topic and return the final report."""
    search_output = as_text(run_search_worker(topic))
    analysis_output = as_text(run_analysis_worker(search_output))
    summary_output = as_text(run_summary_worker(analysis_output))

    return (
        "Final report and trace\n"
        "======================\n"
        f"{summary_output}\n\n"
        "Delegation trace:\n"
        "1) Search worker -> arXiv API\n"
        "2) Analysis worker -> findings extraction\n"
        "3) Summary worker -> final synthesis\n\n"
        "Raw search evidence:\n"
        f"{search_output}"
    )


if __name__ == "__main__":
    selected_topic = "large language model hallucination detection" # Change this topic to explore different areas and get different results
    output = develop_use_case(selected_topic)
    print(output)