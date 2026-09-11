"""
core/email_generator.py
Generates ready-to-send cancellation letters and refund demand notices
tailored to specific subscription leak types (silent hikes, trial traps, standard cancellations).
Compliant with FTC "Click to Cancel" regulations and State Automatic Renewal Laws (ARL).
"""

import urllib.parse
from typing import Dict, Optional
from core.detector import RecurringItem


class CancellationEmailGenerator:
    """Produces customized cancellation and dispute email templates."""

    @classmethod
    def generate(
        cls,
        item: RecurringItem,
        user_name: str = "[Your Full Name]",
        user_email: str = "[Your Account Email]",
        account_last4: str = "[Last 4 digits of card/account]",
        template_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generates email text based on the detected item state:
        - 'price_hike': if price hike flagged
        - 'trial_rollover': if trial rollover detected
        - 'gym': if fitness/gym category
        - 'standard': standard cancellation
        """
        # Determine appropriate template if not explicitly requested
        if not template_type:
            if item.has_price_hike:
                template_type = 'price_hike'
            elif item.is_trial_rollover:
                template_type = 'trial_rollover'
            elif 'Gym' in item.category or 'Fitness' in item.category:
                template_type = 'gym'
            else:
                template_type = 'standard'

        generators = {
            'price_hike': cls._template_price_hike,
            'trial_rollover': cls._template_trial_rollover,
            'gym': cls._template_gym,
            'standard': cls._template_standard
        }

        gen_func = generators.get(template_type, cls._template_standard)
        result = gen_func(item, user_name, user_email, account_last4)

        # Build mailto url
        subject_enc = urllib.parse.quote(result['subject'])
        body_enc = urllib.parse.quote(result['body'])
        result['mailto_link'] = f"mailto:?subject={subject_enc}&body={body_enc}"
        result['template_type'] = template_type
        return result

    @classmethod
    def _template_standard(
        cls, item: RecurringItem, user_name: str, user_email: str, account_last4: str
    ) -> Dict[str, str]:
        subject = f"URGENT: Request for Immediate Cancellation - Account {user_email}"
        body = f"""Dear Support / Billing Team at {item.merchant},

I am writing to formally request the immediate cancellation of my recurring {item.merchant} subscription and the cessation of all recurring billing to my payment method ending in {account_last4}.

Account Details:
- Subscriber Name: {user_name}
- Registered Email: {user_email}
- Most Recent Billing Amount: ${item.current_amount:.2f} ({item.cadence})
- Last Transaction Date: {item.last_date}
- Statement Descriptor: {item.raw_descriptors[0] if item.raw_descriptors else item.merchant}

Pursuant to the Federal Trade Commission's (FTC) "Click-to-Cancel" rule and applicable state Automatic Renewal Laws, please process this cancellation immediately without requiring phone calls, surveys, or retention obstacles.

Furthermore, please ensure:
1. All recurring billing authorizations for this account are revoked.
2. My stored payment credentials are deleted from your active billing systems.
3. Written email confirmation of this cancellation and effective date is provided in reply to this message.

Thank you for your prompt assistance.

Sincerely,
{user_name}
{user_email}
"""
        return {'subject': subject, 'body': body}

    @classmethod
    def _template_price_hike(
        cls, item: RecurringItem, user_name: str, user_email: str, account_last4: str
    ) -> Dict[str, str]:
        diff = item.price_hike_amount
        pct = item.price_hike_pct
        hike_date = item.hike_detected_date or item.last_date
        
        subject = f"Billing Dispute & Immediate Cancellation Notice - {item.merchant} (Acct: {user_email})"
        body = f"""Dear {item.merchant} Billing & Customer Relations,

I am writing to dispute an unauthorized/unnoticed price increase on my subscription and request an immediate cancellation of my account along with a refund for unnotified overcharges.

Transaction Audit Details:
- Subscriber Name: {user_name}
- Associated Email: {user_email}
- Initial / Prior Rate: ${item.initial_amount:.2f}
- New Billed Rate: ${item.current_amount:.2f} (an increase of ${diff:.2f} or +{pct:.1f}%)
- Date Increase First Appeared: {hike_date}
- Payment Method Ending in: {account_last4}
- Statement Line Item: {item.raw_descriptors[0] if item.raw_descriptors else item.merchant}

Under the FTC's Restore Online Shoppers' Confidence Act (ROSCA) and applicable state automatic renewal statutes (e.g., California ARL § 17602), vendors must provide clear, conspicuous, and affirmative advance notice prior to any material changes in billing terms or pricing.

Because I was not provided clear prior notice with an affirmative option to cancel before this rate increase took effect:
1. Please cancel my subscription effective immediately.
2. Please refund the difference (${diff:.2f}) or the full amount charged at the unauthorized rate.
3. Revoke all auto-debit authorizations for card ending in {account_last4}.
4. Provide written email confirmation of the cancellation and refund transaction.

If this matter cannot be resolved promptly, I will be forced to dispute the charges with my financial institution and report the undisclosed rate increase to consumer regulatory bodies.

I look forward to your prompt resolution.

Sincerely,
{user_name}
{user_email}
"""
        return {'subject': subject, 'body': body}

    @classmethod
    def _template_trial_rollover(
        cls, item: RecurringItem, user_name: str, user_email: str, account_last4: str
    ) -> Dict[str, str]:
        subject = f"Dispute & Cancellation: Unintended Trial Rollover - {item.merchant} ({user_email})"
        body = f"""Dear {item.merchant} Billing Support,

I am writing regarding an unexpected full-subscription charge on my account that rolled over from an introductory trial.

Account & Billing Information:
- Name: {user_name}
- Email: {user_email}
- Trial Charge: ${item.initial_amount:.2f} on {item.first_date}
- Subsequent Renewal Charge: ${item.current_amount:.2f} on {item.last_date}
- Card Ending In: {account_last4}

I did not intend to renew into a continuous recurring paid plan at ${item.current_amount:.2f}. I have not actively utilized the service since the rollover date.

Under statutory consumer guidelines requiring clear reminders prior to converting trial terms into recurring commitments:
1. I request the immediate cancellation of this account.
2. I request a full refund of the ${item.current_amount:.2f} rollover charge.
3. Please confirm that my payment details have been removed and no future charges will occur.

Thank you for your understanding and prompt confirmation.

Sincerely,
{user_name}
{user_email}
"""
        return {'subject': subject, 'body': body}

    @classmethod
    def _template_gym(
        cls, item: RecurringItem, user_name: str, user_email: str, account_last4: str
    ) -> Dict[str, str]:
        subject = f"Formal Written Notice of Membership Cancellation - {user_name} (Card ending {account_last4})"
        body = f"""To the Membership & Billing Department at {item.merchant},

Please accept this written correspondence as formal, binding notice of cancellation of my membership with {item.merchant}, effective immediately.

Member Identification:
- Member Name: {user_name}
- Email Address: {user_email}
- Recurring Dues: ${item.current_amount:.2f} ({item.cadence})
- Payment Method on File: Ending in {account_last4}
- Statement Record: {item.raw_descriptors[0] if item.raw_descriptors else item.merchant}

Please cease all automated recurring debits, annual maintenance fees, or additional club assessments to my bank account or credit card. I am providing this notice electronically and am retaining a timestamped copy for my records.

Pursuant to consumer protection standards regarding continuous service contracts:
1. Process this cancellation upon receipt without requiring in-person attendance or registered physical mail.
2. Remove my banking / payment card details from your automated recurring billing terminal.
3. Issue a formal cancellation confirmation number and zero-balance statement via return email.

If any further charges are drafted from my account after receipt of this notice, I will instruct my bank to reject the debit and initiate a formal merchant dispute under Nacha / card network rules.

Thank you for your prompt confirmation.

Sincerely,
{user_name}
{user_email}
"""
        return {'subject': subject, 'body': body}
