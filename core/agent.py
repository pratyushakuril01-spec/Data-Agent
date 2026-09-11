"""
core/agent.py
ReAct (Reasoning + Action) Subscription & Spend Leak Audit Agent.
Executes an iterative Thought -> Action -> Observation cycle using Python/Pandas tools.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, BinaryIO
import pandas as pd
import json

from core.parser import StatementParser
from core.normalizer import MerchantNormalizer
from core.detector import SubscriptionDetector, RecurringItem
from core.email_generator import CancellationEmailGenerator


@dataclass
class ReActStep:
    step_number: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str


@dataclass
class AuditReport:
    total_transactions: int
    date_range: str
    total_spend: float
    recurring_monthly_burn: float
    total_annualized_recurring: float
    annualized_leak_waste: float
    detected_subscriptions: List[RecurringItem]
    price_hikes_count: int
    trial_traps_count: int
    categories_breakdown: Dict[str, float]
    react_trace: List[ReActStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_transactions': self.total_transactions,
            'date_range': self.date_range,
            'total_spend': round(self.total_spend, 2),
            'recurring_monthly_burn': round(self.recurring_monthly_burn, 2),
            'total_annualized_recurring': round(self.total_annualized_recurring, 2),
            'annualized_leak_waste': round(self.annualized_leak_waste, 2),
            'price_hikes_count': self.price_hikes_count,
            'trial_traps_count': self.trial_traps_count,
            'categories_breakdown': self.categories_breakdown,
            'detected_subscriptions': [s.to_dict() for s in self.detected_subscriptions],
            'react_trace': [
                {
                    'step': t.step_number,
                    'thought': t.thought,
                    'action': t.action,
                    'action_input': t.action_input,
                    'observation': t.observation
                }
                for t in self.react_trace
            ]
        }


class GhostAuditReActAgent:
    """
    Autonomous ReAct Agent for auditing bank statements, unmasking cryptic descriptors,
    quantifying recurring spend, catching stealth price hikes, and drafting cancellation notices.
    """

    def __init__(self):
        self.parser = StatementParser()
        self.normalizer = MerchantNormalizer()
        self.detector = SubscriptionDetector(normalizer=self.normalizer)
        self.email_gen = CancellationEmailGenerator()
        self.trace: List[ReActStep] = []

    def _log_step(self, thought: str, action: str, action_input: Dict[str, Any], observation: str):
        step = ReActStep(
            step_number=len(self.trace) + 1,
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation
        )
        self.trace.append(step)

    def run_audit(
        self,
        file_source: Union[str, BinaryIO, pd.DataFrame],
        filename: Optional[str] = None
    ) -> AuditReport:
        """
        Executes the ReAct Audit loop across the provided statement source.
        """
        self.trace = []

        # =========================================================================
        # STEP 1: PARSE STATEMENT
        # =========================================================================
        source_name = filename or getattr(file_source, 'name', None) or "input_statement"
        self._log_step(
            thought=(
                f"I need to inspect the raw file format of '{source_name}' and parse all transactions "
                "into a clean, standardized chronological DataFrame (handling date formats and debit/credit polarities)."
            ),
            action="parse_statement",
            action_input={"source": str(source_name)},
            observation=""  # to be updated
        )

        df = self.parser.parse(file_source, filename=filename)
        tx_count = len(df)
        if tx_count == 0:
            self.trace[-1].observation = "Warning: No valid transactions detected in statement."
            return AuditReport(0, "N/A", 0.0, 0.0, 0.0, 0.0, [], 0, 0, {}, self.trace)

        min_d = df['date'].min().strftime('%Y-%m-%d')
        max_d = df['date'].max().strftime('%Y-%m-%d')
        total_spend = float(df[df['amount'] > 0]['amount'].sum())

        self.trace[-1].observation = (
            f"Successfully ingested {tx_count} transactions spanning {min_d} to {max_d}. "
            f"Total expenditure across period: ${total_spend:,.2f}."
        )

        # =========================================================================
        # STEP 2: NORMALIZE CRYPTIC DESCRIPTORS
        # =========================================================================
        sample_descs = df['raw_description'].head(3).tolist()
        self._log_step(
            thought=(
                f"Bank statements contain cryptic terminal codes, ACH headers, and phone numbers "
                f"(e.g., {sample_descs[:2]}). I will use pattern matching, directory lookup, "
                "and fuzzy clustering to map them to canonical merchant names."
            ),
            action="normalize_merchant_descriptors",
            action_input={"total_rows": tx_count},
            observation=""
        )

        # Run normalizer
        norm_map = {}
        for desc in df['raw_description'].unique():
            norm_name, cat, is_sub, _ = self.normalizer.normalize(desc)
            norm_map[desc] = norm_name

        sample_norm = [f"'{k}' -> '{norm_map[k]}'" for k in list(norm_map.keys())[:3]]
        self.trace[-1].observation = (
            f"Normalized {len(norm_map)} unique merchant descriptors. "
            f"Examples: {'; '.join(sample_norm)}."
        )

        # =========================================================================
        # STEP 3: DETECT PERIODICITY & RECURRING CHARGES
        # =========================================================================
        self._log_step(
            thought=(
                "Now I must group transactions by normalized merchant and measure day intervals "
                "between consecutive charges to determine cadence (Monthly, Weekly, Quarterly, Annual) "
                "and filter out non-recurring one-off purchases."
            ),
            action="detect_periodicity_and_cadence",
            action_input={"method": "interval_variance_analysis"},
            observation=""
        )

        detected_subs = self.detector.analyze(df)
        sub_count = len(detected_subs)
        sub_names = [s.merchant for s in detected_subs]

        self.trace[-1].observation = (
            f"Found {sub_count} recurring subscription services: {', '.join(sub_names[:6])}"
            + (f" and {sub_count - 6} more." if sub_count > 6 else ".")
        )

        # =========================================================================
        # STEP 4: AUDIT FOR SILENT PRICE HIKES & TRIAL ROLLOVERS
        # =========================================================================
        self._log_step(
            thought=(
                "I need to audit each recurring service chronologically to catch silent price hikes "
                "(where the bill jumped without warning) and trial rollover traps."
            ),
            action="audit_price_hikes_and_traps",
            action_input={"candidates_to_audit": sub_count},
            observation=""
        )

        hikes = [s for s in detected_subs if s.has_price_hike]
        trials = [s for s in detected_subs if s.is_trial_rollover]
        hike_details = [
            f"{h.merchant} (+${h.price_hike_amount:.2f} / +{h.price_hike_pct:.0f}%)"
            for h in hikes
        ]

        obs_hikes = f"Flagged {len(hikes)} silent price hike(s): {', '.join(hike_details) if hikes else 'None'}."
        obs_trials = f" Flagged {len(trials)} trial rollover trap(s)." if trials else ""
        self.trace[-1].observation = obs_hikes + obs_trials

        # =========================================================================
        # STEP 5: CALCULATE SPEND LEAKAGE & ANNUAL WASTE
        # =========================================================================
        self._log_step(
            thought=(
                "I will now aggregate the monthly recurring burn, annualized subscription commitment, "
                "and calculate the total financial leakage from unmonitored charges and price hikes."
            ),
            action="calculate_leakage_and_savings",
            action_input={"subscriptions_count": sub_count},
            observation=""
        )

        monthly_burn = sum(
            s.current_amount if "Monthly" in s.cadence else (s.annualized_cost / 12.0)
            for s in detected_subs
        )
        total_annual = sum(s.annualized_cost for s in detected_subs)
        total_leak = sum(s.annualized_leak_impact for s in detected_subs)

        # Spending by category
        cat_breakdown = {}
        for s in detected_subs:
            cat_breakdown[s.category] = cat_breakdown.get(s.category, 0.0) + s.annualized_cost
        cat_breakdown = {k: round(v, 2) for k, v in sorted(cat_breakdown.items(), key=lambda x: x[1], reverse=True)}

        self.trace[-1].observation = (
            f"Monthly recurring run-rate is ${monthly_burn:,.2f}/mo "
            f"(${total_annual:,.2f}/year). Identified ${total_leak:,.2f} in immediate annual leak waste."
        )

        return AuditReport(
            total_transactions=tx_count,
            date_range=f"{min_d} to {max_d}",
            total_spend=total_spend,
            recurring_monthly_burn=monthly_burn,
            total_annualized_recurring=total_annual,
            annualized_leak_waste=total_leak,
            detected_subscriptions=detected_subs,
            price_hikes_count=len(hikes),
            trial_traps_count=len(trials),
            categories_breakdown=cat_breakdown,
            react_trace=self.trace
        )

    def draft_cancellation_email(
        self,
        item: RecurringItem,
        user_name: str = "[Your Full Name]",
        user_email: str = "[Your Account Email]",
        account_last4: str = "[Card Last 4]"
    ) -> Dict[str, str]:
        """Tool to draft targeted cancellation / refund notices for any detected item."""
        return self.email_gen.generate(
            item=item,
            user_name=user_name,
            user_email=user_email,
            account_last4=account_last4
        )
