"""Deterministic experiment simulator.

Each scenario produces the raw thing an experimentation platform would hand
you: a design (decided up front) and a series of looks (cumulative counts).
The checker never learns the true effect — only the data.
"""

import random

from .models import Design, ExperimentData, Look
from .stats import two_proportion_pvalue


def _simulate_looks(
    rng: random.Random,
    control_rate: float,
    treatment_rate: float,
    users_per_arm: int,
    n_looks: int,
    treatment_keep: float = 1.0,
) -> list[Look]:
    per_look = users_per_arm // n_looks
    looks = []
    cu = cc = tu = tc = 0
    for day in range(1, n_looks + 1):
        for _ in range(per_look):
            cu += 1
            cc += rng.random() < control_rate
        for _ in range(per_look):
            # SRM bug: some treatment users crash before assignment is logged.
            if rng.random() >= treatment_keep:
                continue
            tu += 1
            tc += rng.random() < treatment_rate
        looks.append(
            Look(
                day=day,
                control_users=cu,
                control_conversions=cc,
                treatment_users=tu,
                treatment_conversions=tc,
            )
        )
    return looks


def clean_win(seed: int = 3) -> ExperimentData:
    """A real 15% lift, one pre-registered analysis, plenty of samples."""
    design = Design(name="new_checkout_flow", baseline_rate=0.10, relative_mde=0.10)
    rng = random.Random(seed)
    looks = _simulate_looks(rng, 0.10, 0.115, users_per_arm=16000, n_looks=1)
    return ExperimentData(design=design, looks=looks)


def srm_bug(seed: int = 4) -> ExperimentData:
    """Treatment crashes for 12% of users before assignment is logged."""
    design = Design(name="onboarding_redesign", baseline_rate=0.10, relative_mde=0.10)
    rng = random.Random(seed)
    looks = _simulate_looks(rng, 0.10, 0.112, users_per_arm=16000, n_looks=1, treatment_keep=0.88)
    return ExperimentData(design=design, looks=looks)


def underpowered(seed: int = 5) -> ExperimentData:
    """A real 10% lift, but only 1,500 users per arm."""
    design = Design(name="pricing_page_copy", baseline_rate=0.10, relative_mde=0.10)
    rng = random.Random(seed)
    looks = _simulate_looks(rng, 0.10, 0.11, users_per_arm=1500, n_looks=1)
    return ExperimentData(design=design, looks=looks)


def peeking(seed: int = 0) -> ExperimentData:
    """NO true effect. The PM checks the dashboard every day and stops the
    moment p dips under 0.05 — the data ends at that look, exactly as it
    would in real life."""
    design = Design(name="cta_button_color", baseline_rate=0.10, relative_mde=0.10)
    rng = random.Random(seed)
    looks = _simulate_looks(rng, 0.10, 0.10, users_per_arm=6000, n_looks=20)
    for i, look in enumerate(looks):
        p = two_proportion_pvalue(
            look.control_conversions, look.control_users,
            look.treatment_conversions, look.treatment_users,
        )
        if p < design.alpha:
            return ExperimentData(design=design, looks=looks[: i + 1])
    return ExperimentData(design=design, looks=looks)


def find_peeking_seed(start: int = 0, limit: int = 200) -> int:
    """Find a seed where daily peeking 'finds' a significant result under a
    true null. That such seeds are easy to find IS the point of the demo."""
    for seed in range(start, start + limit):
        data = peeking(seed)
        if len(data.looks) < 20:
            return seed
    raise RuntimeError("no peeking seed found in range")


def true_null_powered(seed: int = 6) -> ExperimentData:
    """No effect, but a fully powered, single-look experiment — the case
    where 'don't ship' is a trustworthy answer."""
    design = Design(name="ai_product_descriptions", baseline_rate=0.10, relative_mde=0.10)
    rng = random.Random(seed)
    looks = _simulate_looks(rng, 0.10, 0.10, users_per_arm=16000, n_looks=1)
    return ExperimentData(design=design, looks=looks)
