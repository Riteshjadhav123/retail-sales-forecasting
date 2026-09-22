"""
RetailMind-X Natural Language Retail Assistant.
Answers operational questions strictly grounded in active session data with zero hallucination.
"""

from typing import Dict, Any, Optional, List
import re

class AskRetailMindAssistant:
    """
    Translates natural language questions about the retail session into
    factual, evidence-grounded responses citing actual metrics.
    """

    @staticmethod
    def answer_query(
        query: str,
        session_summary: Dict[str, Any],
        inventory_items: Optional[List[Dict[str, Any]]] = None,
        forecast_results: Optional[Dict[str, Any]] = None,
        anomalies: Optional[List[Dict[str, Any]]] = None,
        seasonality_data: Optional[Dict[str, Any]] = None,
        cost_data: Optional[Dict[str, Any]] = None,
        decision_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        q = (query or "").strip().lower()
        if not q:
            return {
                "answer": "Please ask a question about your inventory, forecasts, anomalies, or replenishment schedule.",
                "source": "Help Assistant",
                "confidence": "HIGH"
            }

        inventory_items = inventory_items or []
        forecast_results = forecast_results or {}
        anomalies = anomalies or []
        seasonality_data = seasonality_data or {}
        cost_data = cost_data or {}
        decision_data = decision_data or {}

        # 1. Replenishment / Reorder / Stockout Questions
        if any(w in q for w in ["reorder", "replenish", "stockout", "out of stock", "safety stock", "purchase order"]):
            reorders = [i for i in inventory_items if i.get("reorder_needed") or i.get("stockout_risk") in ["CRITICAL", "HIGH"]]
            if not inventory_items:
                return {
                    "answer": "No inventory records are currently processed. Please upload and profile your retail dataset first.",
                    "source": "Session Manager",
                    "confidence": "HIGH"
                }
            if not reorders:
                return {
                    "answer": f"All {len(inventory_items)} evaluated inventory items currently have stock above their reorder thresholds. No immediate replenishment orders are required.",
                    "source": f"Inventory Intelligence ({len(inventory_items)} items evaluated)",
                    "confidence": "HIGH"
                }
            
            top_reorders = reorders[:5]
            items_str = ", ".join([f"**{i.get('sku')}** (Reorder: {int(i.get('reorder_quantity', 0))} units, Stock: {int(i.get('current_stock', 0))})" for i in top_reorders])
            more_str = f" and {len(reorders) - 5} more" if len(reorders) > 5 else ""
            
            return {
                "answer": f"There are **{len(reorders)} items** requiring replenishment action:\n\n{items_str}{more_str}.\n\nThese items have depleted below their required safety buffer.",
                "source": f"Inventory Engine ({len(reorders)} critical/high-risk items flagged)",
                "confidence": "HIGH"
            }

        # 2. Accuracy / Best Model / MAPE Questions
        if any(w in q for w in ["accuracy", "mape", "best model", "rmse", "performance", "model", "forecast error"]):
            best_model = forecast_results.get("best_model") or session_summary.get("best_model")
            mape = forecast_results.get("mape")
            if mape is None and best_model:
                mape = session_summary.get("forecast_metrics", {}).get("mape")

            if best_model:
                mape_str = f"{mape:.1f}%" if mape is not None else "evaluated"
                acc_str = f"{100.0 - mape:.1f}%" if mape is not None else "N/A"
                vaidsys_target = ">= 90.0%"
                status = "meets" if (mape is not None and (100.0 - mape) >= 90.0) else "is working toward"
                
                return {
                    "answer": f"The top performing model is **{best_model}** with a MAPE of **{mape_str}** (implied accuracy ~**{acc_str}**). The platform {status} the Vaidsys project benchmark of {vaidsys_target}.",
                    "source": f"Forecasting Model Suite ({best_model})",
                    "confidence": "HIGH"
                }
            return {
                "answer": "Forecasting has not been run for this session yet. Run forecasting from the Forecasting tab to evaluate model accuracy.",
                "source": "Forecasting Engine",
                "confidence": "HIGH"
            }

        # 3. Anomaly / Spike / Drop Questions
        if any(w in q for w in ["anomaly", "anomalies", "spike", "drop", "outlier", "irregular"]):
            if anomalies:
                spikes = [a for a in anomalies if a.get("type") == "SPIKE"]
                drops = [a for a in anomalies if a.get("type") == "DROP"]
                high = [a for a in anomalies if a.get("severity") == "HIGH"]
                sample = anomalies[0]
                return {
                    "answer": f"Detected **{len(anomalies)} demand anomalies** ({len(spikes)} spikes, {len(drops)} drops), including {len(high)} high-severity events. For example, a {sample.get('type', '').lower()} occurred on {sample.get('date')} ({sample.get('causal_attribution')}).",
                    "source": f"Demand Anomaly Engine ({len(anomalies)} anomalies identified)",
                    "confidence": "HIGH"
                }
            return {
                "answer": "No historical demand anomalies exceeding statistical thresholds (Z-score > 2.5 or deviation > 50%) were detected in this dataset.",
                "source": "Demand Anomaly Engine",
                "confidence": "HIGH"
            }

        # 4. Seasonality / Day of week / Month Questions
        if any(w in q for w in ["seasonality", "season", "day of week", "weekday", "weekend", "busiest", "month"]):
            dow = seasonality_data.get("day_of_week", [])
            monthly = seasonality_data.get("monthly", [])
            if dow:
                peak_dow = max(dow, key=lambda x: x.get("lift_vs_baseline_pct", 0))
                peak_m = max(monthly, key=lambda x: x.get("lift_vs_baseline_pct", 0)) if monthly else None
                m_str = f" and peak month is **{peak_m.get('month_name')}** ({'+' if peak_m.get('lift_vs_baseline_pct',0)>0 else ''}{peak_m.get('lift_vs_baseline_pct',0):.1f}% lift)" if peak_m else ""
                
                return {
                    "answer": f"Seasonality analysis indicates the highest demand occurs on **{peak_dow.get('day_name')}** with a **{'+' if peak_dow.get('lift_vs_baseline_pct',0)>0 else ''}{peak_dow.get('lift_vs_baseline_pct',0):.1f}%** lift over average demand{m_str}.",
                    "source": "Seasonality Engine (Day-of-Week & Monthly Lift)",
                    "confidence": "HIGH"
                }
            return {
                "answer": "Seasonality analysis is not available for this dataset or requires date-indexed temporal records.",
                "source": "Seasonality Engine",
                "confidence": "HIGH"
            }

        # 5. Cost Optimization / Savings Questions
        if any(w in q for w in ["cost", "saving", "holding", "carrying", "expense", "dollar"]):
            if cost_data.get("available"):
                savings = cost_data.get("projected_savings", {})
                curr = cost_data.get("current_strategy", {}).get("total_cost", 0)
                rec = cost_data.get("recommended_strategy", {}).get("total_cost", 0)
                return {
                    "answer": f"Adopting RetailMind-X buffer recommendations is projected to reduce total carrying and stockout costs from **${curr:,.2f}** to **${rec:,.2f}**, saving **${savings.get('amount', 0):,.2f}** ({savings.get('percentage', 0):.1f}%). All cost calculations use declared configurable industry assumptions.",
                    "source": "Inventory Cost Optimizer (Configurable Industry Assumptions)",
                    "confidence": "HIGH"
                }
            return {
                "answer": "Inventory cost optimization requires processed inventory items. Navigate to the Inventory tab to compute carrying cost reductions.",
                "source": "Inventory Cost Optimizer",
                "confidence": "HIGH"
            }

        # 6. Priorities / Actions / Today Questions
        if any(w in q for w in ["priority", "priorities", "today", "action", "recommendation", "what should i do"]):
            if decision_data.get("top_actions"):
                top = decision_data["top_actions"][0]
                prios = decision_data.get("priorities", {})
                return {
                    "answer": f"Today's top operational priority is **{top.get('title')}**: {top.get('action')}. System status: {prios.get('critical_stockouts', 0)} critical stockouts, {prios.get('reorders_needed', 0)} reorders recommended.",
                    "source": "AI Decision Center",
                    "confidence": "HIGH"
                }
            return {
                "answer": "No pending critical priorities detected for this dataset.",
                "source": "AI Decision Center",
                "confidence": "HIGH"
            }

        # 7. Dataset / Session / Target Questions
        if any(w in q for w in ["dataset", "frequency", "target", "unit", "monetary", "file", "rows"]):
            rows = session_summary.get("row_count", 0)
            target = session_summary.get("target_column", "Target")
            freq = session_summary.get("detected_frequency", "Daily")
            unit_disp = session_summary.get("target_display", "Units")
            return {
                "answer": f"Active dataset: **{session_summary.get('dataset_name', 'Current Session')}** ({rows:,} rows). Target column: **{target}** ({unit_disp}). Temporal cadence: **{freq}**.",
                "source": "Dataset Session Manager",
                "confidence": "HIGH"
            }

        return {
            "answer": "I don't have enough specific information in the current dataset to answer that question. You can ask me about:\n- Stockouts and items requiring replenishment\n- Best forecasting model and accuracy (MAPE)\n- Demand anomalies and sudden spikes\n- Day-of-week and monthly seasonality\n- Inventory cost savings and holding costs\n- Today's operational priorities",
            "source": "RetailMind-X Knowledge Assistant",
            "confidence": "MEDIUM"
        }
