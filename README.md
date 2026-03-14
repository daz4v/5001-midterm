# 5001-midterm

## Selected Paper 2 Use Case

Use case selected from the midterm paper:
- `8.2.1 Multi-Agent Orchestration` -> `Hierarchical Coordination`

This project develops that use case as a manager worker multi agent system:
- `Manager agent`: coordinates the workflow and delegates subtasks.
- `Search agent`: finds candidate papers for the topic.
- `Analysis agent`: extracts key findings from search output.
- `Summary agent`: writes the final report.

The design follows the paper principle that multi-agent behavior can be built
with normal tool calls and specialized agents, without complex framework-level
message broker patterns.

This system takes a topic you can it where implemented in the code and it will find papers realated to the topic. Then summarizes them and give you a report with strength and weakness. lastly it outputs the links to the papers it used to show they are real. 

## Run

```powershell
c:/1Code/cs5001/5001-midterm/.venv/Scripts/python.exe main.py
```