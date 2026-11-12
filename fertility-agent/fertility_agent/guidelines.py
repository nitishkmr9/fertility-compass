from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuidelineSource:
    source_id: str
    title: str
    publisher: str
    published: str
    url: str
    summary: str
    review_note: str


SOURCES = (
    GuidelineSource(
        "ASRM-RESERVE-2020", "Testing and interpreting measures of ovarian reserve", "ASRM", "2020",
        "https://www.asrm.org/practice-guidance/practice-committee-documents/testing-and-interpreting-measures-of-ovarian-reserve-a-committee-opinion-2020/",
        "ASRM describes ovarian-reserve markers as useful in some clinical settings, such as predicting response to ovarian stimulation, but poor independent predictors of reproductive potential. This source supports caution about interpreting AMH or FSH alone.",
        "Committee opinion, not a patient-specific assessment. Verify the current edition before clinical use.",
    ),
    GuidelineSource(
        "ASRM-EVALUATION-2021", "Fertility evaluation of infertile women", "ASRM", "2021",
        "https://www.asrm.org/practice-guidance/practice-committee-documents/fertility-evaluation-of-infertile-women-a-committee-opinion-2021/",
        "ASRM describes fertility evaluation as a systematic clinical evaluation using history and relevant investigations. This opinion is about clinical evaluation, not a consumer prediction from sparse tracking data.",
        "Committee opinion, not a substitute for clinical judgment. The edition may change; verify before clinical use.",
    ),
    GuidelineSource(
        "NICE-NG257-2026", "Fertility problems: assessment and treatment", "NICE", "2026",
        "https://www.nice.org.uk/guidance/ng257",
        "NICE NG257 covers assessment, treatment, support, and fertility preservation for medical indications. Recommendations should be interpreted by clinicians in light of each person's circumstances and preferences.",
        "Applies to NICE guidance contexts; check the live NICE page for recommendations and updates.",
    ),
    GuidelineSource(
        "ESHRE-FFP-2020", "Female fertility preservation guideline", "ESHRE", "2020",
        "https://www.eshre.eu/Guidelines-and-Legal/Guidelines/Female-Fertility-Preservation",
        "ESHRE's female fertility preservation guideline covers information and support, pre-preservation assessment, interventions, and after-treatment care. Preservation is a discussion with a qualified clinician, not an automated recommendation or guarantee.",
        "Guideline update is under development. Check ESHRE for the current publication.",
    ),
    GuidelineSource(
        "WHO-INFERTILITY-2025", "Guideline for the prevention, diagnosis and treatment of infertility", "WHO", "2025",
        "https://www.who.int/publications/i/item/9789240115774",
        "WHO's guideline gives evidence-based recommendations for prevention, evaluation, and treatment of infertility, with person-centred and equitable fertility care. It is not a validation of a fertility score or consumer prediction.",
        "Global guidance that countries may adapt. Check the live WHO publication for details.",
    ),
)

ALLOWED_OPTIONS = (
    "Lifestyle optimization",
    "Testing",
    "Preconception counselling",
    "Fertility-preservation discussion",
    "Specialist referral",
)

MODIFIABLE_FACTORS = {"smoking", "alcohol", "sleep", "activity", "nutrition"}
NON_MODIFIABLE_FACTORS = {"age"}


def guideline_chunks() -> list[dict[str, str]]:
    return [
        {
            "id": source.source_id,
            "text": f"{source.title} ({source.publisher}, {source.published}). {source.summary} {source.review_note}",
            "title": source.title,
            "publisher": source.publisher,
            "year": source.published,
            "url": source.url,
        }
        for source in SOURCES
    ]