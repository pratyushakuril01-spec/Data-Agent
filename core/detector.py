"""
core/detector.py
Recurrence & Spend Leak Detection Engine.
Identifies recurring subscription charges, transaction periodicity,
silent price hikes, and trial rollover traps.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

from core.normalizer import MerchantNormalizer


@dataclass
class RecurringItem:
    merchant: str
    category: str
    cadence: str  # "Monthly", "Quarterly", "Annual", "Weekly", "Bi-Weekly"
    current_amount: float
    initial_amount: float
    min_amount: float
    max_amount: float
    transaction_count: int
    first_date: str
    last_date: str
    days_between_avg: float
    has_price_hike: bool = False
    price_hike_amount: float = 0.0
    price_hike_pct: float = 0.0
    hike_detected_date: Optional[str] = None
    is_trial_rollover: bool = False
    annualized_cost: float = 0.0
    annualized_leak_impact: float = 0.0
    confidence_score: float = 0.0  # 0.0 - 1.0
    cancellation_hint: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    raw_descriptors: List[str] = field(default_factory=list)
    history: List[Dict] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class SubscriptionDetector:
    """
    Analyzes normalized transactions across time to identify recurring services,
    cadence consistency, and stealth price inflation.
    """

    def __init__(self, normalizer: Optional[MerchantNormalizer] = None):
        self.normalizer = normalizer or MerchantNormalizer()

    def analyze(self, df: pd.DataFrame) -> List[RecurringItem]:
        """
        Main analysis method. Expects DataFrame with ['date', 'raw_description', 'amount'].
        Returns list of detected RecurringItems sorted by annualized spend.
        """
        if df.empty or len(df) < 2:
            return []

        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['amount'] > 0]  # Only consider outgoing charges
        df = df.sort_values('date').reset_index(drop=True)

        # 1. Normalize merchant descriptions
        norm_results = [self.normalizer.normalize(desc) for desc in df['raw_description']]
        df['norm_merchant'] = [r[0] for r in norm_results]
        df['category'] = [r[1] for r in norm_results]
        df['is_known_sub'] = [r[2] for r in norm_results]
        df['cancellation_hint'] = [r[3] for r in norm_results]

        # 2. Cluster remaining unknown merchants if needed
        unresolved = df[~df['is_known_sub']]['norm_merchant'].tolist()
        if unresolved:
            clusters = self.normalizer.cluster_similar_merchants(unresolved)
            df['norm_merchant'] = df['norm_merchant'].apply(lambda m: clusters.get(m, m))

        # 3. Group by normalized merchant
        recurring_items: List[RecurringItem] = []

        for merchant, group in df.groupby('norm_merchant'):
            group = group.sort_values('date').reset_index(drop=True)
            count = len(group)

            # Need at least 2 transactions to establish periodicity, or a single known subscription provider
            is_known = group['is_known_sub'].iloc[0]
            if count < 2 and not is_known:
                continue

            dates = group['date'].tolist()
            amounts = group['amount'].tolist()
            raw_descs = list(set(group['raw_description'].tolist()))
            cat = group['category'].iloc[0]
            hint = group['cancellation_hint'].iloc[0]

            # Analyze periodicity and gaps
            cadence, avg_days, cadence_confidence = self._detect_periodicity(dates, count)

            # Check if this qualifies as a recurring subscription
            is_recurring, confidence = self._evaluate_recurring_candidate(
                count, cadence, cadence_confidence, is_known, amounts
            )

            if not is_recurring:
                continue

            # Analyze price history & silent price hikes
            hike_info = self._detect_price_hike(dates, amounts)
            
            # Check for trial rollover ($0, $1, $1.99 followed by jump to full tier)
            is_trial = self._detect_trial_rollover(dates, amounts)

            current_amt = amounts[-1]
            initial_amt = amounts[0]
            min_amt = float(min(amounts))
            max_amt = float(max(amounts))

            annualized = self._calculate_annualized_cost(current_amt, cadence)
            
            # Flags and leak calculation
            flags = []
            annualized_leak = 0.0

            if hike_info['has_hike']:
                flags.append(
                    f"Silent Price Hike: Increased by ${hike_info['delta']:.2f} "
                    f"(+{hike_info['pct']:.1f}%) on {hike_info['date']}"
                )
                # Leak impact is the difference annualized
                annualized_leak += self._calculate_annualized_cost(hike_info['delta'], cadence)

            if is_trial:
                flags.append("Intro/Trial Rollover Trap: Nominal trial charge converted to recurring subscription")
                annualized_leak += annualized

            if is_known and count >= 2:
                flags.append(f"Confirmed {cat} subscription")

            # Build history records for sparkline/charting
            history = [
                {
                    'date': d.strftime('%Y-%m-%d'),
                    'amount': round(amt, 2),
                    'raw_desc': raw
                }
                for d, amt, raw in zip(dates, amounts, group['raw_description'])
            ]

            item = RecurringItem(
                merchant=merchant,
                category=cat,
                cadence=cadence,
                current_amount=round(current_amt, 2),
                initial_amount=round(initial_amt, 2),
                min_amount=round(min_amt, 2),
                max_amount=round(max_amt, 2),
                transaction_count=count,
                first_date=dates[0].strftime('%Y-%m-%d'),
                last_date=dates[-1].strftime('%Y-%m-%d'),
                days_between_avg=round(avg_days, 1),
                has_price_hike=hike_info['has_hike'],
                price_hike_amount=round(hike_info['delta'], 2),
                price_hike_pct=round(hike_info['pct'], 1),
                hike_detected_date=hike_info['date'],
                is_trial_rollover=is_trial,
                annualized_cost=round(annualized, 2),
                annualized_leak_impact=round(annualized_leak, 2),
                confidence_score=round(confidence, 2),
                cancellation_hint=hint,
                flags=flags,
                raw_descriptors=raw_descs,
                history=history
            )
            recurring_items.append(item)

        # Sort by annualized cost descending
        recurring_items.sort(key=lambda x: (x.has_price_hike or x.is_trial_rollover, x.annualized_cost), reverse=True)
        return recurring_items

    def _detect_periodicity(self, dates: List[pd.Timestamp], count: int) -> Tuple[str, float, float]:
        """
        Computes day intervals and matches against standard financial billing cycles:
        Monthly (~30d), Weekly (~7d), Bi-Weekly (~14d), Quarterly (~90d), Annual (~365d).
        Returns (cadence_name, average_interval_days, consistency_score).
        """
        if count < 2:
            return "Monthly (Assumed)", 30.0, 0.5

        intervals = [(dates[i] - dates[i - 1]).days for i in range(1, count)]
        avg_days = float(np.mean(intervals))
        std_days = float(np.std(intervals)) if len(intervals) > 1 else 0.0

        # Billing cadence brackets (with tolerance for calendar months and weekend batch posting)
        if 5 <= avg_days <= 9:
            cadence = "Weekly"
            consistency = max(0.2, 1.0 - (std_days / 5.0))
        elif 12 <= avg_days <= 17:
            cadence = "Bi-Weekly"
            consistency = max(0.2, 1.0 - (std_days / 6.0))
        elif 25 <= avg_days <= 36:
            cadence = "Monthly"
            consistency = max(0.3, 1.0 - (std_days / 10.0))
        elif 80 <= avg_days <= 100:
            cadence = "Quarterly"
            consistency = max(0.3, 1.0 - (std_days / 15.0))
        elif 340 <= avg_days <= 390:
            cadence = "Annual"
            consistency = max(0.4, 1.0 - (std_days / 25.0))
        else:
            cadence = "Irregular Recurring"
            consistency = 0.4

        return cadence, avg_days, min(1.0, max(0.1, consistency))

    def _evaluate_recurring_candidate(
        self,
        count: int,
        cadence: str,
        cadence_confidence: float,
        is_known: bool,
        amounts: List[float]
    ) -> Tuple[bool, float]:
        """Determine if transactions form a recurring subscription and compute overall confidence."""
        # Check amount variance (subscriptions usually have identical or very similar base amounts)
        amt_std = np.std(amounts) if len(amounts) > 1 else 0.0
        amt_mean = np.mean(amounts) if len(amounts) > 0 else 1.0
        cv = amt_std / (amt_mean + 1e-6) # Coefficient of variation

        confidence = 0.0

        if is_known:
            confidence += 0.45
        if count >= 3:
            confidence += 0.35
        elif count == 2:
            confidence += 0.20

        if cadence in ["Monthly", "Weekly", "Bi-Weekly", "Quarterly", "Annual"]:
            confidence += 0.25 * cadence_confidence

        if cv < 0.15:  # Consistent amounts
            confidence += 0.15
        elif cv > 0.8:  # Highly erratic amounts (e.g. random Uber trips or grocery shopping)
            confidence -= 0.35

        confidence = min(1.0, max(0.0, confidence))

        # Accept if confidence >= 0.50, or if known vendor with at least 1 charge
        is_recurring = (confidence >= 0.50) or (is_known and count >= 1)
        return is_recurring, confidence

    def _detect_price_hike(self, dates: List[pd.Timestamp], amounts: List[float]) -> Dict:
        """
        Scans chronological charges to detect sudden or silent rate hikes.
        Example: $15.49 for 3 months, then $22.99 onwards.
        """
        if len(amounts) < 2:
            return {'has_hike': False, 'delta': 0.0, 'pct': 0.0, 'date': None}

        # Check latest amount vs baseline previous mode/average
        # We look for price increases >= $1.00 and >= 5%
        for i in range(1, len(amounts)):
            prev_amt = amounts[i - 1]
            curr_amt = amounts[i]

            # Price hike detected if higher than previous
            if curr_amt > prev_amt + 0.50:
                pct = ((curr_amt - prev_amt) / prev_amt) * 100.0
                if pct >= 5.0:
                    return {
                        'has_hike': True,
                        'delta': curr_amt - prev_amt,
                        'pct': pct,
                        'date': dates[i].strftime('%Y-%m-%d')
                    }

        return {'has_hike': False, 'delta': 0.0, 'pct': 0.0, 'date': None}

    def _detect_trial_rollover(self, dates: List[pd.Timestamp], amounts: List[float]) -> bool:
        """Detect initial nominal charge ($0 - $4.99) followed quickly by regular tier."""
        if len(amounts) < 2:
            return False

        first_amt = amounts[0]
        second_amt = amounts[1]
        day_gap = (dates[1] - dates[0]).days

        # Introductory trial signature: first charge <= $5.00, second charge >= $15.00 within 45 days
        if first_amt <= 5.0 and second_amt >= 15.0 and 3 <= day_gap <= 45:
            return True

        return False

    def _calculate_annualized_cost(self, amount: float, cadence: str) -> float:
        """Converts charge amount into projected yearly cost."""
        multipliers = {
            "Weekly": 52.0,
            "Bi-Weekly": 26.0,
            "Monthly": 12.0,
            "Monthly (Assumed)": 12.0,
            "Quarterly": 4.0,
            "Annual": 1.0,
            "Irregular Recurring": 12.0
        }
        mult = multipliers.get(cadence, 12.0)
        return amount * mult
