"""Single entry point for LLM calls.

Every Anthropic call in the project must go through `app.llm.client`. The
client handles tracing, JSON cassette replay (`REC=1` to record), the daily
cost cap, and prompt-injection-safe message construction. Importing the
`anthropic` SDK anywhere else is a review-blocking violation.
"""
