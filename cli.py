"""
cli.py
Command-line interface for the Ghost Subscription & Spend Leak Audit Agent.
Run audits directly from terminal and generate cancellation emails.
"""

import argparse
import sys
import json
import os
from typing import Optional

from core.agent import GhostAuditReActAgent
from core.email_generator import CancellationEmailGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Ghost Subscription & Spend Leak Audit Agent - CLI"
    )
    parser.add_argument(
        "--statement", "-s",
        type=str,
        default="sample_data/personal_chase_sample.csv",
        help="Path to statement CSV or PDF file"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to save audit findings as JSON"
    )
    parser.add_argument(
        "--draft-email", "-e",
        type=str,
        default=None,
        help="Merchant name to generate ready-to-send cancellation email for"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Alex Morgan",
        help="Your full name for cancellation letters"
    )
    parser.add_argument(
        "--user-email",
        type=str,
        default="alex.morgan@example.com",
        help="Your email address for cancellation letters"
    )
    parser.add_argument(
        "--last4",
        type=str,
        default="4321",
        help="Last 4 digits of card on file"
    )

    args = parser.parse_args()

    if not os.path.exists(args.statement):
        print(f"Error: Statement file not found at '{args.statement}'")
        sys.exit(1)

    print("=" * 70)
    print("🕵️  GHOST SUBSCRIPTION & SPEND LEAK AUDIT AGENT")
    print("=" * 70)
    print(f"Auditing statement: {args.statement}\n")

    agent = GhostAuditReActAgent()
    report = agent.run_audit(args.statement)

    print("--- ReAct Agent Execution Trace ---")
    for step in report.react_trace:
        print(f"\n[Step {step.step_number}]")
        print(f"💭 Thought:     {step.thought}")
        print(f"⚡ Action:      {step.action}({step.action_input})")
        print(f"👁️ Observation: {step.observation}")

    print("\n" + "=" * 70)
    print("📊 EXECUTIVE AUDIT SUMMARY")
    print("=" * 70)
    print(f"Total Transactions Parsed:    {report.total_transactions}")
    print(f"Audit Statement Period:       {report.date_range}")
    print(f"Total Period Expenditure:     ${report.total_spend:,.2f}")
    print(f"Monthly Subscription Burn:    ${report.recurring_monthly_burn:,.2f} / month")
    print(f"Annualized Recurring Spend:   ${report.total_annualized_recurring:,.2f} / year")
    print(f"🚨 Annual Spend Leak Waste:    ${report.annualized_leak_waste:,.2f} / year")
    print(f"Silent Price Hikes Flagged:   {report.price_hikes_count}")
    print(f"Trial Rollover Traps:         {report.trial_traps_count}")

    print("\n" + "-" * 70)
    print("DETECTED RECURRING COMMITMENTS & LEAKS")
    print("-" * 70)
    header = f"{'Merchant':<25} {'Cadence':<10} {'Current':<9} {'Annual':<10} {'Status / Flags'}"
    print(header)
    print("-" * len(header))

    for item in report.detected_subscriptions:
        flag_str = ""
        if item.has_price_hike:
            flag_str = f"⚠️ HIKE: +${item.price_hike_amount:.2f} (+{item.price_hike_pct:.0f}%)"
        elif item.is_trial_rollover:
            flag_str = "⚠️ TRIAL ROLLOVER TRAP"
        else:
            flag_str = "✓ Active Plan"

        row = (
            f"{item.merchant[:24]:<25} "
            f"{item.cadence:<10} "
            f"${item.current_amount:<8.2f} "
            f"${item.annualized_cost:<9.2f} "
            f"{flag_str}"
        )
        print(row)

    # If email requested
    if args.draft_email:
        target_merchant = args.draft_email.lower()
        matched = next(
            (s for s in report.detected_subscriptions if target_merchant in s.merchant.lower()),
            None
        )
        if matched:
            print("\n" + "=" * 70)
            print(f"✉️  CANCELLATION & DISPUTE LETTER: {matched.merchant.upper()}")
            print("=" * 70)
            email_data = agent.draft_cancellation_email(
                item=matched,
                user_name=args.name,
                user_email=args.user_email,
                account_last4=args.last4
            )
            print(f"SUBJECT: {email_data['subject']}\n")
            print(email_data['body'])
            print("-" * 70)
            print(f"One-click mailto: {email_data['mailto_link'][:90]}...")
        else:
            print(f"\nWarning: Could not find detected subscription matching '{args.draft_email}'.")

    # Export to JSON if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\nAudit findings successfully saved to: {args.output}")


if __name__ == "__main__":
    main()
