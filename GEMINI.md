# Ullr's Secret - Agent Instructions

## Agent Workflow Rules
- **No Concurrent Executions:** Do NOT execute subagents concurrently. Do NOT issue concurrent tool calls that modify files (e.g., `replace`, `write_file`) in a single turn to prevent race conditions. Always execute modifying actions sequentially.
