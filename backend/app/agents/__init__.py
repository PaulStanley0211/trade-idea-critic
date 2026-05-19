"""LangGraph node implementations.

Each node is a pure function of `app.models.state.CritiqueState`. Side effects
only through `app.memory` or `app.tools`. No direct HTTP or DB calls in here.
"""
