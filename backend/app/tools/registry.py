"""ToolRegistry — centralized registry mapping tool names to callable functions."""
from __future__ import annotations
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Stores and provides access to reusable tool functions."""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable) -> None:
        self._tools[name] = func
        logger.debug("Registered tool: %s", name)

    def get(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def call(self, name: str, **kwargs: Any) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found in registry.")
        return tool(**kwargs)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        return name in self._tools


def build_tool_registry() -> ToolRegistry:
    """Build and return the default tool registry with all registered tools."""
    from app.tools import (
        csv_tool, excel_tool, calculator, product_tool,
        order_tool, similarity_tool, llm_tool, employee_tool, analytics_tool,
    )

    registry = ToolRegistry()

    # CSV / Excel readers
    registry.register("csv_reader", csv_tool.read_csv)
    registry.register("excel_reader", excel_tool.read_excel)

    # Product / inventory tools
    registry.register("get_inventory", product_tool.get_inventory)
    registry.register("get_products", product_tool.get_products)
    registry.register("get_vendor_prices", product_tool.get_vendor_prices)
    registry.register("check_restock", product_tool.check_restock)
    registry.register("validate_price_differences", product_tool.validate_price_differences)
    registry.register("get_product_catalog", product_tool.get_product_catalog)

    # Order tools
    registry.register("get_order", order_tool.get_order)
    registry.register("get_order_by_email", order_tool.get_order_by_email)

    # Similarity / duplicate detection
    registry.register("find_duplicates", similarity_tool.find_duplicates)

    # LLM tools (language understanding + generation)
    registry.register("generate_product_description", llm_tool.generate_product_description)
    registry.register("classify_keywords", llm_tool.classify_keywords)
    registry.register("generate_campaign_brief", llm_tool.generate_campaign_brief)
    registry.register("extract_task_skills", llm_tool.extract_task_skills)
    registry.register("generate_assignment_summary", llm_tool.generate_assignment_summary)

    # Employee / task tools
    registry.register("get_employees", employee_tool.get_employees)
    registry.register("rank_employees_for_task", employee_tool.rank_employees_for_task)

    # Analytics / logging
    registry.register("get_execution_logs", analytics_tool.get_execution_logs)
    registry.register("compute_performance_report", analytics_tool.compute_performance_report)

    # Calculator
    registry.register("reorder_quantity", calculator.reorder_quantity)
    registry.register("price_diff_percent", calculator.price_diff_percent)
    registry.register("success_rate", calculator.success_rate)
    registry.register("average", calculator.average)

    return registry


# Module-level singleton (initialized at app startup)
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = build_tool_registry()
    return _tool_registry
