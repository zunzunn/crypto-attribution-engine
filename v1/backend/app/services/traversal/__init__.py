"""Traversal package: bounded, deterministic BFS traversal over the derived
transaction graph (see engine.py)."""

from app.services.traversal.engine import ExpandFn, TraversalEngine

__all__ = ["ExpandFn", "TraversalEngine"]