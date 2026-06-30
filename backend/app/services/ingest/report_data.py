"""ReportData — unified output schema for all ingest paths (XML + PDF).

Every field the rule engine touches lives here.
Both xml_parser.py and pdf_extractor.py must return a ReportData instance.

SECURITY: Fields marked # NPI must never appear in logs or be passed to AI.
          Use pii_scrubber.py before passing any text field to Ollama.
"""
from dataclasses import dataclass, field


@dataclass
class ComparableSale:
    """One comparable sale from the sales comparison grid."""

    address: str = ""               # NPI — display only, never logged
    sale_price: float = 0.0
    sale_date: str = ""             # YYYY-MM-DD or raw UAD date string
    distance_miles: float = 0.0
    gla_sqft: float = 0.0
    lot_size: str = ""
    year_built: int = 0
    condition: str = ""             # C1-C6
    quality: str = ""               # Q1-Q6
    net_adjustment: float = 0.0
    gross_adjustment: float = 0.0
    adjusted_sale_price: float = 0.0
    is_arms_length: bool = True
    is_closed_sale: bool = True
    data_source: str = ""
    days_on_market: int | None = None

    @property
    def net_adjustment_pct(self) -> float:
        if self.sale_price == 0:
            return 0.0
        return abs(self.net_adjustment / self.sale_price) * 100

    @property
    def gross_adjustment_pct(self) -> float:
        if self.sale_price == 0:
            return 0.0
        return abs(self.gross_adjustment / self.sale_price) * 100


@dataclass
class ReportData:
    """
    Unified representation of an appraisal report after parsing.
    Fields marked # NPI must not be logged or passed to any external AI.
    """

    file_type: str = ""
    form_type: str = ""
    parse_errors: list[str] = field(default_factory=list)

    subject_address: str = ""       # NPI
    subject_city: str = ""          # NPI
    subject_state: str = ""
    subject_zip: str = ""
    subject_county: str = ""
    subject_legal_description: str = ""
    assessor_parcel_number: str = ""

    subject_gla_sqft: float = 0.0
    subject_lot_size: str = ""
    subject_year_built: int = 0
    subject_condition: str = ""     # C1-C6
    subject_quality: str = ""       # Q1-Q6
    subject_bedrooms: int = 0
    subject_bathrooms: float = 0.0
    subject_property_type: str = ""

    effective_date: str = ""
    inspection_date: str = ""
    report_date: str = ""

    appraiser_name: str = ""        # NPI
    appraiser_license: str = ""
    appraiser_license_state: str = ""
    appraiser_certification_type: str = ""
    supervisory_appraiser_name: str = ""  # NPI
    supervisory_appraiser_license: str = ""
    appraiser_signed: bool = False
    supervisory_signed: bool = False

    client_name: str = ""           # NPI
    lender_name: str = ""           # NPI
    borrower_name: str = ""         # NPI

    contract_price: float | None = None
    contract_date: str = ""
    is_purchase: bool = False
    is_refinance: bool = False

    flood_zone: str = ""
    flood_map_number: str = ""
    flood_map_date: str = ""
    in_sfha: bool = False

    approaches_used: list[str] = field(default_factory=list)
    value_by_sales_comparison: float | None = None
    value_by_cost_approach: float | None = None
    value_by_income_approach: float | None = None
    final_value_opinion: float | None = None
    value_as_improved: float | None = None

    comparables: list[ComparableSale] = field(default_factory=list)
    listing_comps: list[ComparableSale] = field(default_factory=list)

    neighborhood_description: str = ""
    market_conditions_commentary: str = ""
    reconciliation_text: str = ""
    cost_approach_commentary: str = ""
    income_approach_commentary: str = ""
    additional_comments: str = ""
    scope_of_work: str = ""
    intended_use: str = ""
    intended_users: str = ""

    has_signed_certification: bool = False
    prior_services_disclosed: bool = False
    exposure_time_stated: bool = False
    marketing_time_stated: bool = False

    raw_text: str = ""  # PDF full text — MUST be scrubbed before AI

    @property
    def closed_comps(self) -> list[ComparableSale]:
        return [c for c in self.comparables if c.is_closed_sale]

    @property
    def has_min_comps(self) -> bool:
        return len(self.closed_comps) >= 3

    @property
    def subject_full_address(self) -> str:
        parts = [self.subject_address, self.subject_city, self.subject_state, self.subject_zip]
        return ", ".join(p for p in parts if p)

    def narratives_for_ai(self) -> str:
        """Concatenate all narrative fields. MUST be PII-scrubbed before Ollama."""
        sections = [
            ("Market Conditions", self.market_conditions_commentary),
            ("Neighborhood", self.neighborhood_description),
            ("Reconciliation", self.reconciliation_text),
            ("Scope of Work", self.scope_of_work),
            ("Additional Comments", self.additional_comments),
        ]
        return "\n\n".join(f"[{label}]\n{text}" for label, text in sections if text.strip())
