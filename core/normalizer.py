"""
core/normalizer.py
Intelligent Merchant Normalization Engine for financial statements.
Converts cryptic bank descriptors (e.g., "AMZN DIG*2948 866-216-1072 CA")
into canonical merchant identities (e.g., "Amazon Prime") with industry categorization.
"""

import re
from typing import Dict, Tuple, Optional
import difflib

# Known subscription service directory:
# Pattern regex -> (Canonical Name, Category, Support/Cancellation Hint)
KNOWN_MERCHANTS = [
    # Streaming & Entertainment
    (r'amzn\s*(?:dig|digital|prime|video)', "Amazon Prime", "E-Commerce & Media", "amazon.com/mc/manage"),
    (r'netflix', "Netflix", "Streaming & Media", "netflix.com/youraccount"),
    (r'spotify', "Spotify", "Streaming & Media", "spotify.com/account/subscription"),
    (r'disney\s*(?:plus|\+)', "Disney+", "Streaming & Media", "disneyplus.com/account"),
    (r'hulu', "Hulu", "Streaming & Media", "hulu.com/account"),
    (r'hbo\s*max|max\.com', "Max (HBO)", "Streaming & Media", "max.com/subscription"),
    (r'apple\.com/bill|itunes', "Apple Services / Subscriptions", "Software & Media", "reportaproblem.apple.com"),
    (r'youtube\s*(?:premium|tv|member)', "YouTube Premium", "Streaming & Media", "youtube.com/paid_memberships"),
    (r'audible', "Audible", "Audio & Books", "audible.com/account/overview"),
    (r'crunchyroll', "Crunchyroll", "Streaming & Media", "crunchyroll.com/account"),
    (r'paramount\s*\+?', "Paramount+", "Streaming & Media", "paramountplus.com/account"),
    (r'peacock', "Peacock TV", "Streaming & Media", "peacocktv.com/account"),

    # SaaS & Productivity
    (r'openai|chatgpt', "OpenAI / ChatGPT", "AI & Dev Tools", "help.openai.com"),
    (r'anthropic|claude\.ai', "Anthropic Claude", "AI & Dev Tools", "support.anthropic.com"),
    (r'adobe\s*(?:\*|creative|cloud|acrobat|systems)?', "Adobe Creative Cloud", "Design & Software", "account.adobe.com/plans"),
    (r'canva', "Canva Pro", "Design & Software", "canva.com/settings/billing"),
    (r'figma', "Figma", "Design & Software", "figma.com/settings"),
    (r'notion(?:\s*labs)?', "Notion", "Productivity SaaS", "notion.so/settings"),
    (r'slack(?:\s*technologies)?', "Slack", "Productivity SaaS", "slack.com/billing"),
    (r'zoom\.us|zoom\s*video', "Zoom", "Productivity SaaS", "zoom.us/billing"),
    (r'dropbox', "Dropbox", "Cloud Storage", "dropbox.com/account/plan"),
    (r'box\.com|box\s*inc', "Box.com", "Cloud Storage", "box.com/billing"),
    (r'google\s*(?:\*|storage|workspace|gsuite|cloud|one)', "Google Workspace / One", "Cloud & Productivity", "admin.google.com"),
    (r'microsoft\s*(?:\*|365|msft|azure|office)', "Microsoft 365 / Azure", "Cloud & Productivity", "account.microsoft.com/services"),
    (r'github', "GitHub", "AI & Dev Tools", "github.com/settings/billing"),
    (r'gitlab', "GitLab", "AI & Dev Tools", "gitlab.com/-/subscriptions"),
    (r'atlassian|jira|confluence|trello', "Atlassian (Jira/Trello)", "Productivity SaaS", "atlassian.com/myaccount"),
    (r'1password|agilebits', "1Password", "Security & Utilities", "my.1password.com"),
    (r'lastpass', "LastPass", "Security & Utilities", "lastpass.com/my-account"),
    (r'bitwarden', "Bitwarden", "Security & Utilities", "vault.bitwarden.com"),
    (r'calendly', "Calendly", "Productivity SaaS", "calendly.com/billing"),
    (r'loom(?:\s*video)?', "Loom", "Productivity SaaS", "loom.com/settings"),
    (r'grammarly', "Grammarly", "Productivity SaaS", "grammarly.com/account"),
    (r'docu(?:sign)?', "DocuSign", "Productivity SaaS", "docusign.com"),
    (r'airtable', "Airtable", "Productivity SaaS", "airtable.com/account"),
    (r'miro', "Miro", "Productivity SaaS", "miro.com/app/settings"),
    (r'zapier', "Zapier", "Automation SaaS", "zapier.com/app/billing"),
    (r'make\.com|integromat', "Make.com", "Automation SaaS", "make.com/user/billing"),
    (r'hubspot', "HubSpot", "Sales & Marketing", "hubspot.com"),
    (r'mailchimp|intuit\s*mailchimp', "Mailchimp", "Sales & Marketing", "mailchimp.com/account"),

    # Infrastructure & Hosting
    (r'aws|amazon\s*web\s*services', "Amazon Web Services (AWS)", "Cloud Infrastructure", "aws.amazon.com/billing"),
    (r'digitalocean', "DigitalOcean", "Cloud Infrastructure", "cloud.digitalocean.com/billing"),
    (r'heroku', "Heroku", "Cloud Infrastructure", "dashboard.heroku.com/account/billing"),
    (r'vercel', "Vercel", "Cloud Infrastructure", "vercel.com/dashboard/billing"),
    (r'cloudflare', "Cloudflare", "Cloud Infrastructure", "dash.cloudflare.com"),
    (r'render\.com', "Render", "Cloud Infrastructure", "render.com"),
    (r'datadog', "Datadog", "Cloud Infrastructure", "datadoghq.com"),
    (r'sentry', "Sentry.io", "AI & Dev Tools", "sentry.io/settings/billing"),

    # Gyms & Fitness
    (r'planet\s*fit(?:ness)?', "Planet Fitness", "Gym & Fitness", "planetfitness.com"),
    (r'equinox', "Equinox", "Gym & Fitness", "equinox.com"),
    (r'la\s*fitness', "LA Fitness", "Gym & Fitness", "lafitness.com"),
    (r'anytime\s*fitness', "Anytime Fitness", "Gym & Fitness", "anytimefitness.com"),
    (r'peloton', "Peloton", "Gym & Fitness", "onepeloton.com"),
    (r'orange\s*theory|orangetheory', "OrangeTheory Fitness", "Gym & Fitness", "orangetheory.com"),
    (r'classpass', "ClassPass", "Gym & Fitness", "classpass.com"),
    (r'whoop', "Whoop", "Gym & Fitness", "whoop.com"),
    (r'strava', "Strava", "Gym & Fitness", "strava.com/settings/billing"),

    # News, Learning & Lifestyle
    (r'ny\s*times|nytimes|new\s*york\s*times', "The New York Times", "News & Media", "nytimes.com/subscription"),
    (r'wsj|wall\s*street\s*journal', "Wall Street Journal", "News & Media", "customercenter.wsj.com"),
    (r'bloomberg', "Bloomberg", "News & Media", "bloomberg.com/account"),
    (r'washington\s*post|washpost', "The Washington Post", "News & Media", "washingtonpost.com"),
    (r'substack', "Substack", "News & Media", "substack.com/settings"),
    (r'medium(?:\s*membership)?', "Medium", "News & Media", "medium.com/me/settings"),
    (r'duolingo', "Duolingo Plus", "Education", "duolingo.com/settings/account"),
    (r'coursera', "Coursera", "Education", "coursera.org/account-profile"),
    (r'udemy', "Udemy", "Education", "udemy.com/user/edit-account"),
    (r'chegg', "Chegg", "Education", "chegg.com/my/account"),
    (r'masterclass', "MasterClass", "Education", "masterclass.com"),

    # Telecom & Utilities
    (r'at&t|att\s*bill', "AT&T", "Telecom & Utilities", "att.com"),
    (r'verizon', "Verizon", "Telecom & Utilities", "verizon.com"),
    (r't-mobile|tmobile', "T-Mobile", "Telecom & Utilities", "t-mobile.com"),
    (r'comcast|xfinity', "Xfinity / Comcast", "Telecom & Utilities", "xfinity.com"),
]

# Compiled patterns for high-speed scanning
COMPILED_MERCHANTS = [
    (re.compile(pattern, re.IGNORECASE), name, cat, url)
    for pattern, name, cat, url in KNOWN_MERCHANTS
]

# Noise prefixes & suffixes to prune from merchant strings
NOISE_PATTERNS = [
    re.compile(r'^(?:pos debit|pos purchase|pos transaction|debit purchase|checkcard|recurring payment|recurring debit|preauthorized debit|ach debit|wire out|card purchase|withdrawal)\s*[-:]?\s*', re.IGNORECASE),
    re.compile(r'\b(?:\d{3}[-.\s]??\d{3}[-.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-.\s]??\d{4})\b'), # Phone numbers
    re.compile(r'\b(?:[A-Z]{2}\s+\d{5}(?:-\d{4})?)\b'), # State + Zip e.g. CA 94105
    re.compile(r'\b(?:US|USA|CA|NY|WA|TX|FL|IL|UK|DE)\b(?:\s*[\d-]*)$', re.IGNORECASE), # Trailing state/country codes
    re.compile(r'[*#]\s*[A-Z0-9_-]{3,}', re.IGNORECASE), # Terminal / invoice IDs like *2948 or #10493
    re.compile(r'\b(?:\.com|\.io|\.net|\.org|\.us|\.co)\b', re.IGNORECASE), # Domain extensions
    re.compile(r'\s{2,}') # Excess spaces
]


class MerchantNormalizer:
    """Normalizes raw merchant descriptors and categorizes subscription spending."""

    def __init__(self):
        self._cache: Dict[str, Tuple[str, str, bool, Optional[str]]] = {}

    def clean_raw_descriptor(self, raw_desc: str) -> str:
        """Strip transaction boilerplate, phone numbers, merchant IDs, and trailing garbage."""
        if not raw_desc or not isinstance(raw_desc, str):
            return "Unknown Merchant"

        s = raw_desc.strip()
        # Apply noise strip regexes
        for pat in NOISE_PATTERNS:
            s = pat.sub(' ', s)

        # Remove trailing punctuation and cleanup spacing
        s = re.sub(r'[\*\#\-_,/\.]+$', '', s).strip()
        s = re.sub(r'\s+', ' ', s)
        return s.title() if s else raw_desc.strip()

    def normalize(self, raw_desc: str) -> Tuple[str, str, bool, Optional[str]]:
        """
        Takes raw bank statement text and returns:
          (canonical_merchant, category, is_known_recurring_provider, cancellation_hint)
        """
        if raw_desc in self._cache:
            return self._cache[raw_desc]

        raw_clean = str(raw_desc).strip()

        # Step 1: Match against known subscription service directory
        for regex, canonical_name, category, hint in COMPILED_MERCHANTS:
            if regex.search(raw_clean):
                res = (canonical_name, category, True, hint)
                self._cache[raw_desc] = res
                return res

        # Step 2: Heuristic cleanup of unknown merchant
        cleaned = self.clean_raw_descriptor(raw_clean)
        
        # Detect common SaaS/Subscription keywords
        is_sub_hint = bool(re.search(r'sub|member|monthly|annual|license|recurring|club|gym|cloud|hosting|soft', raw_clean, re.IGNORECASE))
        category = "Subscriptions & SaaS" if is_sub_hint else "General Spend"
        
        res = (cleaned or "Unknown Merchant", category, is_sub_hint, None)
        self._cache[raw_desc] = res
        return res

    def cluster_similar_merchants(self, merchant_names: list, cutoff: float = 0.85) -> Dict[str, str]:
        """
        Fuzzy-match and cluster similar unknown merchant names across months
        (e.g., 'Acme Hosting Srv 1' vs 'Acme Hosting Srv 2' -> 'Acme Hosting Srv 1')
        """
        clusters: Dict[str, str] = {}
        unique_names = sorted(set(merchant_names))

        for i, name in enumerate(unique_names):
            if name in clusters:
                continue
            clusters[name] = name
            # Check remaining names
            for other in unique_names[i+1:]:
                if other in clusters:
                    continue
                ratio = difflib.SequenceMatcher(None, name.lower(), other.lower()).ratio()
                if ratio >= cutoff:
                    clusters[other] = name

        return clusters
