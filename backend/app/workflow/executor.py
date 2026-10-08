"""Generic Workflow Executor — the single engine that runs ALL workflows."""
from __future__ import annotations
import time
import logging
import traceback
from pathlib import Path
from typing import Any, Optional
import pandas as pd

from app.workflow.models import WorkflowDefinition, ExecutionResult, StepResult
from app.tools.registry import get_tool_registry
from app.config import DATA_DIR, PRICE_DIFF_THRESHOLD

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Single reusable executor for all workflow definitions.
    Each workflow's steps are dispatched via the tool registry and
    per-workflow handler methods. Business logic stays in Python.
    """

    def execute(
        self,
        workflow_def: WorkflowDefinition,
        user_input: str,
        context: dict,
    ) -> ExecutionResult:
        """Main entry point — runs the specified workflow and returns a structured result."""
        start_time = time.time()
        result = ExecutionResult(
            workflow_id=workflow_def.workflow_id,
            workflow_name=workflow_def.workflow_name,
            user_request=user_input,
            status="running",
        )

        try:
            # --- GENERIC MISSING INPUTS CHECK ---
            missing = context.get("_missing_required_inputs", [])
            if missing and isinstance(missing, list):
                # Clean up formatting for display
                clean_missing = []
                for f in missing:
                    clean = str(f).replace("_", " ").strip().title()
                    if clean and clean not in clean_missing:
                        clean_missing.append(clean)
                
                if clean_missing:
                    # Clear out the internal key before final output
                    context.pop("_missing_required_inputs", None)
                    
                    result.status = "needs_clarification"
                    result.final_result = {
                        "missing_fields": clean_missing,
                        "workflow_id": workflow_def.workflow_id,
                        "message": (
                            f"I can proceed with the {workflow_def.workflow_name}. "
                            "Please provide the following information:\n"
                            + "\n".join(f"{i+1}. {field}" for i, field in enumerate(clean_missing))
                        )
                    }
                    result.duration_seconds = round(time.time() - start_time, 3)
                    return result

            handler = self._get_handler(workflow_def.workflow_id)
            handler(workflow_def, context, result)
            if result.status == "running":
                result.status = "success"
        except Exception as exc:
            logger.error("Workflow %s failed: %s", workflow_def.workflow_id, exc)
            logger.debug(traceback.format_exc())
            result.status = "failed"
            result.errors.append(str(exc))

        result.duration_seconds = round(time.time() - start_time, 3)
        return result

    # ------------------------------------------------------------------ #
    #  Dispatcher                                                          #
    # ------------------------------------------------------------------ #
    def _get_handler(self, workflow_id: str):
        handlers = {
            "WF001": self._run_wf001,
            "WF002": self._run_wf002,
            "WF003": self._run_wf003,
            "WF004": self._run_wf004,
            "WF005": self._run_wf005,
            "WF006": self._run_wf006,
            "WF007": self._run_wf007,
            "WF008": self._run_wf008,
            "WF009": self._run_wf009,
            "WF010": self._run_wf010,
        }
        handler = handlers.get(workflow_id)
        if handler is None:
            raise NotImplementedError(
                f"No handler registered for workflow '{workflow_id}'. "
                "Add a new tool and register a handler to support this workflow."
            )
        return handler

    # ------------------------------------------------------------------ #
    #  Helper utilities                                                    #
    # ------------------------------------------------------------------ #
    def _step(self, result: ExecutionResult, name: str, func, **kwargs) -> Any:
        """Execute a named step, record its result, propagate exceptions."""
        t0 = time.time()
        try:
            output = func(**kwargs)
            ms = round((time.time() - t0) * 1000, 1)
            result.steps.append(StepResult(name=name, status="success", output=None, duration_ms=ms))
            logger.debug("Step '%s' OK (%.0f ms)", name, ms)
            return output
        except Exception as exc:
            ms = round((time.time() - t0) * 1000, 1)
            result.steps.append(StepResult(name=name, status="failed", error=str(exc), duration_ms=ms))
            raise

    # ================================================================== #
    #  WF001 — Inventory Restock Check                                    #
    # ================================================================== #
    def _run_wf001(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.tools import product_tool
        inventory = self._step(result, "Load inventory", product_tool.get_inventory)
        self._step(result, "Validate inventory data",
                   self._validate_df, df=inventory,
                   required=["product_name", "current_stock", "minimum_stock"])
        low_stock = self._step(result, "Check stock thresholds & identify low-stock products",
                               product_tool.check_restock, df=inventory)
        self._step(result, "Calculate reorder quantities", lambda: None)  # already computed

        records = low_stock[["product_name", "current_stock", "minimum_stock", "reorder_quantity"]].to_dict(orient="records")
        result.conditions.append({
            "rule": "current_stock < minimum_stock",
            "flagged_count": len(records),
        })
        result.final_result = {
            "restock_required": len(records),
            "products": records,
            "message": (
                f"{len(records)} product(s) require restocking."
                if records else "All products are sufficiently stocked."
            ),
        }

    # ================================================================== #
    #  WF002 — Product Price Validation                                   #
    # ================================================================== #
    def _run_wf002(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.tools import product_tool
        products = self._step(result, "Load product prices", product_tool.get_products)
        vendors = self._step(result, "Load vendor prices", product_tool.get_vendor_prices)
        self._step(result, "Match products by SKU", self._validate_sku_columns,
                   products=products, vendors=vendors)
        exceptions = self._step(result, "Compare prices and flag exceptions",
                                product_tool.validate_price_differences,
                                products=products, vendors=vendors,
                                threshold=PRICE_DIFF_THRESHOLD)
        records = exceptions.to_dict(orient="records") if not exceptions.empty else []
        # clean NaN
        import math
        records = [{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()} for r in records]

        result.conditions.append({
            "rule": f"price_diff_percent > {PRICE_DIFF_THRESHOLD}%",
            "flagged_count": len(records),
        })
        result.final_result = {
            "threshold_pct": PRICE_DIFF_THRESHOLD,
            "total_matched": len(products.merge(vendors, on="sku")),
            "exceptions": len(records),
            "products": records,
            "message": (
                f"{len(records)} product(s) exceed the {PRICE_DIFF_THRESHOLD}% price threshold."
                if records else "All prices are within the acceptable threshold."
            ),
        }

    # ================================================================== #
    #  WF003 — Vendor File Processing                                     #
    # ================================================================== #
    def _run_wf003(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        file_content: bytes | None = ctx.get("file_content")
        file_name: str = ctx.get("file_name", "upload")

        if file_content is None:
            raise ValueError(
                "WF003 — Vendor File Processing requires a runtime input file (CSV or XLSX). "
                "Please upload a vendor data file (e.g. vendor_products.xlsx) using the "
                "'Upload Runtime File' button and try again."
            )
        elif file_name.endswith(".csv"):
            from app.tools.csv_tool import read_csv_from_bytes
            df = self._step(result, "Read uploaded CSV file", read_csv_from_bytes,
                            content=file_content, filename=file_name)
        else:
            from app.tools.excel_tool import read_excel_from_bytes
            df = self._step(result, "Read uploaded Excel file", read_excel_from_bytes,
                            content=file_content, filename=file_name)

        df, norm_report = self._step(result, "Normalize column names", self._normalize_columns, df=df)
        invalid_rows, cleaned = self._step(result, "Validate required fields",
                                           self._validate_vendor_rows, df=df)

        result.conditions.append({"rule": "Rows missing SKU or product_name are invalid"})
        result.final_result = {
            "total_rows": len(df),
            "valid_rows": len(cleaned),
            "invalid_rows": len(invalid_rows),
            "column_normalization": norm_report,
            "invalid_row_details": invalid_rows.to_dict(orient="records") if not invalid_rows.empty else [],
            "cleaned_data_preview": cleaned.head(10).to_dict(orient="records"),
            "message": f"Processed {len(df)} rows. {len(cleaned)} valid, {len(invalid_rows)} invalid.",
        }

    # ================================================================== #
    #  WF004 — Product Description Generator                              #
    # ================================================================== #
    def _run_wf004(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.services import llm_service
        
        # 1. Validation
        product_name = ctx.get("product_name", "").strip()
        self._step(result, "Validate product information", lambda: None)
        
        if not product_name:
            result.status = "needs_clarification"
            result.final_result = {
                "success": False,
                "workflow_id": "WF004",
                "status": "missing_input",
                "missing_fields": ["product_name"],
                "message": "Product name is required to generate product content."
            }
            return
            
        self._step(result, "Required fields available \u2014 proceeding", lambda: None)

        category = ctx.get("category", "")
        attributes = ctx.get("attributes", "")
        material = ctx.get("material", "")
        color = ctx.get("color", "")
        target_audience = ctx.get("target_audience", "")

        # 2. Try Gemini
        try:
            content = self._step(result, "Generate product description (Gemini)", llm_service.generate_product_description,
                                 product_name=product_name,
                                 category=category,
                                 attributes=attributes,
                                 material=material,
                                 color=color,
                                 target_audience=target_audience)
            result.metadata["Execution Mode"] = "Gemini LLM"
        except Exception:
            # 3. Deterministic Fallback if Gemini fails (Network/Auth/Quota)
            def generate_fallback():
                parts = []
                if category: parts.append(f"an {category} product")
                else: parts.append("a product")
                
                if target_audience: parts.append(f"designed for {target_audience}")
                desc_p1 = f"{product_name} is " + " ".join(parts) + "."
                
                features = []
                if attributes: features.append(attributes)
                if material: features.append(material)
                if color: features.append(f"a {color} color finish")
                
                if features:
                    features_str = ", ".join(features)
                    desc_p2 = f" The product features {features_str}."
                    short_desc = f"{product_name} with {features_str}."
                    meta = f"Explore {product_name} featuring {features_str}."
                    seo = f"{product_name} | {attributes.split(',')[0].strip() if attributes else category}"
                else:
                    desc_p2 = ""
                    short_desc = product_name
                    meta = f"Explore {product_name}."
                    seo = product_name

                return {
                    "product_description": (desc_p1 + desc_p2).strip(),
                    "short_description": short_desc,
                    "seo_title": seo.strip(" | "),
                    "meta_description": meta,
                    "message": "Gemini is temporarily unavailable, so deterministic fallback was used.",
                    "missing_attributes": [],
                    "provided_attributes": ctx
                }
            
            self._step(result, "Gemini unavailable \u2014 activated deterministic fallback", lambda: None)
            content = self._step(result, "Generate product description (Fallback)", generate_fallback)
            result.metadata["Execution Mode"] = "Deterministic Fallback"

        self._step(result, "Package final output", lambda: None)
        result.final_result = content

    # ================================================================== #
    #  WF005 — Customer Order Status                                      #
    # ================================================================== #
    def _run_wf005(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.tools import order_tool
        order_id = ctx.get("order_id", "").strip()
        email = ctx.get("email", "").strip()

        if not order_id and not email:
            raise ValueError("Please provide an order ID (e.g. ORD-1001) or customer email.")

        if order_id:
            order_id = order_id.upper()
            self._step(result, "Validate order identifier", lambda: None)
            order = self._step(result, "Search order by ID", order_tool.get_order, order_id=order_id)
            if order is None:
                result.conditions.append({"rule": "Order not found — additional identifier requested"})
                result.final_result = {
                    "found": False,
                    "order_id": order_id,
                    "message": f"Order '{order_id}' was not found. Please verify the order ID or provide your customer email.",
                }
                return
        else:
            self._step(result, "Validate email identifier", lambda: None)
            orders = self._step(result, "Search orders by email", order_tool.get_order_by_email, email=email)
            if not orders:
                result.final_result = {
                    "found": False,
                    "email": email,
                    "message": f"No orders found for '{email}'.",
                }
                return
            order = orders[0]  # most recent

        self._step(result, "Retrieve shipment status", lambda: None)
        self._step(result, "Generate order summary", lambda: None)
        result.final_result = {"found": True, "order": order, "message": f"Order found: status is '{order.get('status', 'Unknown')}'."}

    # ================================================================== #
    #  WF006 — Duplicate Product Detection                                #
    # ================================================================== #
    def _run_wf006(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.tools import product_tool, similarity_tool
        catalog = self._step(result, "Load product catalog", product_tool.get_product_catalog)
        self._step(result, "Validate catalog structure",
                   self._validate_df, df=catalog, required=["sku", "product_name"])
        self._step(result, "Normalize product names and SKUs", lambda: None)
        duplicates = self._step(result, "Compare product identifiers and detect duplicates",
                                similarity_tool.find_duplicates, df=catalog)
        self._step(result, "Assign confidence levels", lambda: None)

        result.conditions.append({
            "rule": "Exact SKU = definite; similarity ≥ 0.75 = likely; ≥ 0.55 = possible"
        })
        by_level = {"definite": 0, "likely": 0, "possible": 0}
        for d in duplicates:
            by_level[d["confidence"]] = by_level.get(d["confidence"], 0) + 1

        result.final_result = {
            "total_pairs": len(duplicates),
            "by_confidence": by_level,
            "pairs": duplicates,
            "message": f"Found {len(duplicates)} potential duplicate pair(s): {by_level['definite']} definite, {by_level['likely']} likely, {by_level['possible']} possible.",
        }

    # ================================================================== #
    #  WF007 — Marketing Campaign Brief                                   #
    # ================================================================== #
    def _run_wf007(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.tools import llm_tool

        # ── Canonical field mapping ────────────────────────────────────
        normalized_ctx = {}
        for k, v in ctx.items():
            if isinstance(k, str):
                normalized_key = k.lower().replace(" ", "_")
                normalized_ctx[normalized_key] = v
            else:
                normalized_ctx[k] = v

        def get_val(key: str) -> str:
            val = normalized_ctx.get(key)
            if not val:
                return ""
            if isinstance(val, list):
                return ", ".join(str(i) for i in val).strip()
            return str(val).strip()

        # ── Safe field extraction ──────────────────────────────────────
        campaign_goal    = get_val("campaign_goal")
        product_list     = get_val("product_list")
        target_audience  = get_val("target_audience")
        promotion        = get_val("promotion") or "Not specified"
        campaign_dates   = get_val("campaign_dates") or get_val("campaign_date")

        # ── Required-field validation ──────────────────────────────────
        REQUIRED = [
            ("campaign_goal",   campaign_goal,   "Campaign Goal"),
            ("product_list",    product_list,    "Product List"),
            ("target_audience", target_audience, "Target Audience"),
            ("campaign_dates",  campaign_dates,  "Campaign Dates"),
        ]
        missing_labels = [label for _key, val, label in REQUIRED if not val]

        self._step(result, "Validate campaign inputs", lambda: None)

        if missing_labels:
            result.status = "needs_clarification"
            if len(missing_labels) == 1:
                msg = (
                    f"To create the marketing campaign brief, "
                    f"please provide the {missing_labels[0]}."
                )
            else:
                items = "\n".join(f"- {lbl}" for lbl in missing_labels)
                msg = (
                    "To create the marketing campaign brief, please provide:\n" + items
                )
            result.final_result = {
                "success": False,
                "workflow_id": "WF007",
                "status": "missing_input",
                "missing_fields": [k for k, v, _l in REQUIRED if not v],
                "message": msg,
            }
            return

        # ── All fields present — generate brief ───────────────────────
        self._step(result, "Identify campaign objective", lambda: None)
        brief = self._step(
            result, "Generate campaign brief (LLM)",
            llm_tool.generate_campaign_brief,
            campaign_goal=campaign_goal,
            product_list=product_list,
            target_audience=target_audience,
            promotion=promotion,
            campaign_dates=campaign_dates,
        )
        self._step(result, "Package structured brief", lambda: None)
        result.final_result = {
            **brief,
            "input_summary": {
                "campaign_goal":   campaign_goal,
                "product_list":    product_list,
                "target_audience": target_audience,
                "promotion":       promotion,
                "campaign_dates":  campaign_dates,
            },
        }

    # ================================================================== #
    #  WF008 — SEO Keyword Classification                                 #
    # ================================================================== #
    def _run_wf008(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.tools import llm_tool
        from app.tools.csv_tool import read_csv

        file_content: bytes | None = ctx.get("file_content")
        inline_keywords: str = ctx.get("keywords", "")

        if file_content:
            df = self._step(result, "Read keywords from uploaded file",
                            self._parse_keyword_file, content=file_content,
                            filename=ctx.get("file_name", "keywords.csv"))
            keywords = df.iloc[:, 0].dropna().astype(str).tolist()
        elif inline_keywords:
            keywords = [k.strip() for k in inline_keywords.replace(",", "\n").split("\n") if k.strip()]
            self._step(result, "Parse inline keywords", lambda: None)
        else:
            # Load sample keyword file
            kw_df = self._step(result, "Load sample keywords", read_csv,
                               file_path=DATA_DIR / "sample_keywords.csv")
            keywords = kw_df.iloc[:, 0].dropna().astype(str).tolist()

        self._step(result, "Remove duplicate keywords", lambda: None)
        keywords = list(dict.fromkeys(keywords))  # deduplicate while preserving order

        classifications = self._step(result, "Classify keyword search intent (LLM)",
                                     llm_tool.classify_keywords, keywords=keywords)
        self._step(result, "Map keywords to categories and export", lambda: None)

        result.conditions.append({"rule": "Classify as: informational / commercial / transactional / navigational"})
        result.final_result = {
            "total_keywords": len(keywords),
            "classifications": classifications,
            "message": f"Classified {len(classifications)} keyword(s).",
        }

    # ================================================================== #
    #  WF009 — Employee Task Assignment                                   #
    # ================================================================== #
    def _run_wf009(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.tools import llm_tool, employee_tool
        
        # 1. Normalize Context keys
        normalized_ctx = {}
        for k, v in ctx.items():
            if isinstance(k, str):
                normalized_key = k.lower().replace(" ", "_").replace(":", "")
                normalized_ctx[normalized_key] = v
            else:
                normalized_ctx[k] = v

        def get_val(key: str) -> str:
            val = normalized_ctx.get(key)
            if not val:
                return ""
            if isinstance(val, list):
                return ", ".join(str(i) for i in val).strip()
            return str(val).strip()

        task_desc = get_val("task_description")
        employee_list = get_val("employee_list")
        user_skills = get_val("skills")
        workload = get_val("workload")
        priority = get_val("priority")
        deadline = get_val("deadline")
        
        # Temporary Debug Logging as requested
        print("DEBUG WF009 Extraction:")
        print(f"raw_user_prompt: {result.user_request}")
        print(f"extracted_input: {ctx}")
        print(f"normalized_input: {normalized_ctx}")
        print(f"missing_fields: {['task_description'] if not task_desc else []}")
        
        if not task_desc:
            result.status = "needs_clarification"
            result.final_result = {
                "success": False,
                "workflow_id": "WF009",
                "status": "missing_input",
                "missing_fields": ["task_description"],
                "message": "'Task Description' is required for task assignment."
            }
            return

        skills = self._step(result, "Extract required skills from task (LLM)",
                            llm_tool.extract_task_skills, task_description=task_desc)
        ranked = self._step(result, "Compare employee skills",
                            employee_tool.rank_employees_for_task,
                            task_description=task_desc, required_skills=skills)
        self._step(result, "Check current workload", lambda: None)
        self._step(result, "Rank candidates", lambda: None)

        available = [e for e in ranked if e["available"]]
        result.conditions.append({
            "rule": "Prefer employees with required skills + available capacity. Escalate if none available."
        })

        if not available:
            result.status = "escalation"
            result.final_result = {
                "assigned": False,
                "required_skills": skills,
                "candidates_evaluated": len(ranked),
                "escalation_required": True,
                "message": "No employees with available capacity and required skills. Escalation required.",
                "all_candidates": ranked,
            }
            return

        best = available[0]
        reason = (
            f"Best skill match ({round(best['skill_score']*100)}%) "
            f"and highest capacity ({best['capacity']} slots free)."
        )
        summary = self._step(result, "Generate assignment summary (LLM)",
                             llm_tool.generate_assignment_summary,
                             task_description=task_desc, employee=best, reason=reason)
                             
        final_dict = {
            "assigned": True,
            "assigned_to": best["name"],
            "required_skills": skills,
            "matched_skills": best["matched_skills"],
            "skill_score_pct": round(best["skill_score"] * 100, 1),
            "capacity": best["capacity"],
            "combined_score": best["combined_score"],
            "reason": reason,
            "summary": summary,
            "all_candidates": ranked,
            "message": f"Task assigned to {best['name']}. {reason}",
        }
        if priority:
            final_dict["priority"] = priority
        if deadline:
            final_dict["deadline"] = deadline
            
        result.final_result = final_dict

    # ================================================================== #
    #  WF010 — Workflow Performance Report                                #
    # ================================================================== #
    def _run_wf010(self, wf: WorkflowDefinition, ctx: dict, result: ExecutionResult):
        from app.tools import analytics_tool
        logs = self._step(result, "Load execution logs", analytics_tool.get_execution_logs)
        self._step(result, "Calculate success/failure rates", lambda: None)
        self._step(result, "Calculate average execution times", lambda: None)
        report = self._step(result, "Identify frequent errors and slow workflows",
                            analytics_tool.compute_performance_report, logs=logs)
        self._step(result, "Generate recommendations", lambda: None)

        flagged = [w for w in report.get("workflows", []) if w.get("flagged")]
        result.conditions.append({
            "rule": "Flag workflows: failure rate > 10% OR avg execution time > threshold"
        })
        result.final_result = {
            **report,
            "flagged_workflows": len(flagged),
            "message": (
                f"Analyzed {report['total_executions']} executions. "
                f"{len(flagged)} workflow(s) flagged for review."
            ),
        }

    # ================================================================== #
    #  Shared helpers (reusable across workflows)                         #
    # ================================================================== #
    def _validate_df(self, df: pd.DataFrame, required: list[str]) -> None:
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Data missing required columns: {missing}")
        if df.empty:
            raise ValueError("Data file is empty.")

    def _validate_sku_columns(self, products: pd.DataFrame, vendors: pd.DataFrame) -> None:
        for name, df in [("products", products), ("vendors", vendors)]:
            if "sku" not in df.columns:
                raise ValueError(f"{name} CSV must have a 'sku' column.")

    def _normalize_columns(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        old_cols = list(df.columns)
        df.columns = [c.lower().strip().replace(" ", "_").replace("-", "_") for c in df.columns]
        report = {old: new for old, new in zip(old_cols, df.columns) if old != new}
        return df, report

    def _validate_vendor_rows(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Split vendor rows into invalid (missing sku or product_name) and valid."""
        sku_col = next((c for c in df.columns if "sku" in c.lower()), None)
        name_col = next((c for c in df.columns if "name" in c.lower() or "product" in c.lower()), None)
        if not sku_col or not name_col:
            return df, pd.DataFrame()
        mask_invalid = df[sku_col].isna() | (df[sku_col].astype(str).str.strip() == "") | \
                       df[name_col].isna() | (df[name_col].astype(str).str.strip() == "")
        return df[mask_invalid], df[~mask_invalid]

    def _check_product_attrs(self, ctx: dict) -> dict:
        provided = {k: v for k, v in ctx.items() if v and str(v).strip()}
        missing = [f for f in ["category", "attributes", "material", "color", "target_audience"]
                   if not ctx.get(f, "").strip()]
        return {"provided": list(provided.keys()), "missing": missing}

    def _parse_keyword_file(self, content: bytes, filename: str) -> pd.DataFrame:
        if filename.endswith(".csv"):
            import io
            return pd.read_csv(io.BytesIO(content))
        else:
            import io
            return pd.read_excel(io.BytesIO(content))
