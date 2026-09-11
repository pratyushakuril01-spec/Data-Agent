"""
core/langgraph_agent.py
LangGraph Deep ReAct Financial Audit Agent.
Orchestrates multi-turn Reasoning + Action loops using LangGraph,
OpenRouter LLM models, and the E2B Code Interpreter Sandbox.
"""

import os
import json
from typing import Dict, Any, List, Optional, Generator
import pandas as pd

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import tool

# LangGraph imports
try:
    from langgraph.graph import StateGraph, START, END, MessagesState
    from langgraph.prebuilt import ToolNode
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_OPENAI_AVAILABLE = True
except ImportError:
    LANGCHAIN_OPENAI_AVAILABLE = False

from core.e2b_sandbox import E2BSandboxManager
from core.normalizer import MerchantNormalizer
from core.detector import SubscriptionDetector, RecurringItem
from core.parser import StatementParser
from core.email_generator import CancellationEmailGenerator
from core.agent import GhostAuditReActAgent, AuditReport, ReActStep


SYSTEM_PROMPT = """You are the "Ghost Subscription & Spend Leak" Forensic Audit Agent.
Your mission is to rigorously analyze raw bank and credit card statements, unmask cryptic merchant descriptors,
detect recurring billing periodicity (monthly/quarterly/annual), flag silent price hikes, and generate ready-to-send cancellation and refund demand letters.

You have access to:
1. `execute_python_in_e2b_sandbox`: Run Python code with Pandas/Numpy inside an isolated E2B cloud sandbox.
2. `normalize_merchant`: Translate cryptic bank line items (e.g. 'AMZN DIG*2948') to canonical brands ('Amazon Prime').
3. `audit_statement_data`: Run comprehensive periodicity, price hike, and trial rollover algorithms.
4. `draft_cancellation_email`: Draft an FTC Click-to-Cancel and state ARL compliant cancellation or dispute letter.

Follow the ReAct paradigm:
- Think carefully about what to inspect next.
- Use Python data analysis tools to inspect distributions, find recurring frequencies, and compare consecutive amounts.
- Highlight stealth price increases where a vendor hiked rates without affirmative consent.
- Conclude with an executive summary of total monthly burn, annualized waste, and action items.
"""


def build_audit_tools(sandbox_mgr: E2BSandboxManager, normalizer: MerchantNormalizer, detector: SubscriptionDetector):
    """Factory that builds tool functions bound to the current sandbox and detector."""

    @tool
    def execute_python_in_e2b_sandbox(code: str) -> str:
        """
        Executes Python data analysis code in the E2B Code Interpreter sandbox.
        Use this tool to inspect DataFrames, compute rolling price deltas, group by merchant,
        or analyze transaction interval distributions with pandas.
        """
        res = sandbox_mgr.run_code(code)
        output = []
        if res.stdout:
            output.append(f"STDOUT:\n{res.stdout}")
        if res.stderr:
            output.append(f"STDERR:\n{res.stderr}")
        if res.error:
            output.append(f"ERROR:\n{res.error}")
        env_label = "E2B Cloud Sandbox" if res.is_cloud_sandbox else "Local Sandbox Executor"
        return f"[{env_label} ({res.execution_time_seconds}s)]\n" + ("\n".join(output) if output else "Code executed with no output.")

    @tool
    def normalize_merchant(raw_descriptor: str) -> str:
        """
        Normalizes a cryptic bank descriptor (e.g., 'AMZN DIG*2948', 'NETFLIX.COM 866-579-7172 CA')
        into its canonical service name and industry category.
        """
        canonical, category, is_sub, hint = normalizer.normalize(raw_descriptor)
        return json.dumps({
            "canonical_name": canonical,
            "category": category,
            "is_known_subscription": is_sub,
            "cancellation_url": hint
        })

    @tool
    def audit_statement_data(statement_path: str) -> str:
        """
        Parses the statement file, normalizes all line items, and runs periodicity,
        silent price hike, and trial rollover detection algorithms. Returns structured findings.
        """
        df = StatementParser.parse(statement_path)
        items = detector.analyze(df)
        summary = {
            "total_transactions": len(df),
            "detected_recurring_count": len(items),
            "hikes_count": sum(1 for i in items if i.has_price_hike),
            "trial_traps_count": sum(1 for i in items if i.is_trial_rollover),
            "subscriptions": [
                {
                    "merchant": i.merchant,
                    "cadence": i.cadence,
                    "current_rate": i.current_amount,
                    "initial_rate": i.initial_amount,
                    "has_hike": i.has_price_hike,
                    "hike_amount": i.price_hike_amount,
                    "annual_cost": i.annualized_cost,
                    "annual_leak": i.annualized_leak_impact
                }
                for i in items
            ]
        }
        return json.dumps(summary, indent=2)

    @tool
    def draft_cancellation_email(
        merchant: str,
        current_amount: float,
        initial_amount: float = 0.0,
        cadence: str = "Monthly",
        has_price_hike: bool = False,
        user_name: str = "[Your Name]",
        user_email: str = "[Your Email]",
        account_last4: str = "[Last 4]"
    ) -> str:
        """
        Drafts a legally informed, FTC 'Click-to-Cancel' compliant cancellation email
        or a silent price hike dispute letter demanding a refund.
        """
        item = RecurringItem(
            merchant=merchant,
            category="General",
            cadence=cadence,
            current_amount=current_amount,
            initial_amount=initial_amount if initial_amount > 0 else current_amount,
            min_amount=min(initial_amount or current_amount, current_amount),
            max_amount=max(initial_amount or current_amount, current_amount),
            transaction_count=3,
            first_date="Recent",
            last_date="Recent",
            days_between_avg=30.0,
            has_price_hike=has_price_hike,
            price_hike_amount=(current_amount - initial_amount) if (has_price_hike and initial_amount) else 0.0,
            price_hike_pct=(((current_amount - initial_amount) / initial_amount) * 100) if (has_price_hike and initial_amount) else 0.0
        )
        email_data = CancellationEmailGenerator.generate(
            item=item,
            user_name=user_name,
            user_email=user_email,
            account_last4=account_last4
        )
        return json.dumps(email_data, indent=2)

    return [
        execute_python_in_e2b_sandbox,
        normalize_merchant,
        audit_statement_data,
        draft_cancellation_email
    ]


class LangGraphAuditAgent:
    """
    Orchestrates the LangGraph Deep ReAct loop using OpenRouter LLMs and E2B Code Interpreter.
    """

    SUPPORTED_MODELS = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "google/gemini-2.0-flash-001",
        "deepseek/deepseek-chat",
        "meta-llama/llama-3.3-70b-instruct",
        "mistralai/mistral-large-2407"
    ]

    def __init__(
        self,
        openrouter_api_key: Optional[str] = None,
        e2b_api_key: Optional[str] = None,
        model_name: str = "anthropic/claude-3.5-sonnet"
    ):
        self.openrouter_api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
        self.e2b_api_key = e2b_api_key or os.environ.get("E2B_API_KEY")
        self.model_name = model_name

        self.normalizer = MerchantNormalizer()
        self.detector = SubscriptionDetector(normalizer=self.normalizer)
        self.sandbox_mgr = E2BSandboxManager(api_key=self.e2b_api_key)

        # Build tools
        self.tools = build_audit_tools(self.sandbox_mgr, self.normalizer, self.detector)

        # Fallback deterministic agent
        self.deterministic_agent = GhostAuditReActAgent()

    def create_graph(self):
        """Constructs the LangGraph ReAct StateGraph."""
        if not (LANGGRAPH_AVAILABLE and LANGCHAIN_OPENAI_AVAILABLE and self.openrouter_api_key):
            return None

        # Initialize OpenRouter ChatOpenAI model
        llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/ghost-audit-agent",
                "X-Title": "Ghost Subscription & Spend Leak Audit Agent"
            },
            temperature=0.1
        )

        llm_with_tools = llm.bind_tools(self.tools)

        def agent_node(state: MessagesState):
            messages = state["messages"]
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}

        tool_node = ToolNode(self.tools)

        def should_continue(state: MessagesState):
            last_message = state["messages"][-1]
            if last_message.tool_calls:
                return "tools"
            return END

        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue, ["tools", END])
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    def run_audit(
        self,
        statement_path: str,
        filename: Optional[str] = None
    ) -> AuditReport:
        """
        Runs the audit. If OpenRouter API key is available, queries the LangGraph Deep ReAct agent.
        Always executes the Python data analysis pipeline with E2B sandbox.
        """
        # Execute Python data analysis in E2B sandbox environment
        # 1. Read statement content
        with open(statement_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()

        fname = filename or os.path.basename(statement_path)
        self.sandbox_mgr.upload_file(fname, raw_content)

        # Run python data analysis in sandbox
        sandbox_analysis_code = f"""
import pandas as pd
import numpy as np

# Load statement in sandbox
df = pd.read_csv('{fname}')
print(f"Loaded {{len(df)}} rows. Columns: {{list(df.columns)}}")
"""
        sandbox_res = self.sandbox_mgr.run_code(sandbox_analysis_code)

        # Run full deterministic detector to guarantee structured report
        report = self.deterministic_agent.run_audit(statement_path, filename=fname)

        # If OpenRouter is available, run LangGraph Deep ReAct loop to generate rich insights
        graph = self.create_graph()
        if graph:
            try:
                user_msg = (
                    f"Please perform a forensic spend leak audit on the statement at '{statement_path}'. "
                    f"First run Python code in the sandbox to verify the data, unmask merchants, "
                    f"detect recurring charges and silent price hikes, and summarize the total spend leaks."
                )
                initial_state = {
                    "messages": [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=user_msg)
                    ]
                }
                # Run graph stream
                final_state = graph.invoke(initial_state)
                # Map graph messages into ReAct trace steps
                self._enrich_trace_from_langgraph(report, final_state["messages"])
            except Exception as e:
                print(f"[LangGraph Fallback] Error running LangGraph loop: {e}")

        return report

    def _enrich_trace_from_langgraph(self, report: AuditReport, messages: List[BaseMessage]):
        """Translates LangGraph message chain into readable ReAct steps for UI."""
        enriched_steps = []
        step_idx = 1
        for msg in messages:
            if isinstance(msg, AIMessage):
                thought = msg.content if isinstance(msg.content, str) else ""
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        enriched_steps.append(ReActStep(
                            step_number=step_idx,
                            thought=thought or f"Calling tool {tc['name']} to inspect data.",
                            action=tc["name"],
                            action_input=tc["args"],
                            observation="Executing tool..."
                        ))
                        step_idx += 1
                elif thought:
                    enriched_steps.append(ReActStep(
                        step_number=step_idx,
                        thought="Formulating final audit conclusions.",
                        action="conclude_audit",
                        action_input={},
                        observation=thought[:300] + "..." if len(thought) > 300 else thought
                    ))
                    step_idx += 1
            elif isinstance(msg, ToolMessage):
                if enriched_steps:
                    enriched_steps[-1].observation = str(msg.content)[:400]

        if enriched_steps:
            report.react_trace = enriched_steps
