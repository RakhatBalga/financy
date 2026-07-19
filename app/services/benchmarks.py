"""Reference spending structure for Kazakhstan (shares of expenses, %).

Approximate shares of household consumption expenditure by broad bucket, based
on the Bureau of National Statistics household budget survey (stat.gov.kz).
We compare *shares of total spending*, not absolute amounts — shares are fair
across income levels, unlike tenge figures.

The bot's categories are granular, so each is mapped to a broad bucket and the
user's shares are aggregated before comparing. Both the current Kazakh category
names and the legacy Russian ones are mapped, so pre-migration data still works.

Numbers are rounded, illustrative reference points — not exact official figures.
Update roughly once a year from the latest published survey.
"""

from __future__ import annotations

# Broad bucket (Kazakh, user-facing) -> approximate share of household spending (%)
KZ_BUCKET_SHARES: dict[str, float] = {
    "Тамақтану": 48.0,
    "Тұрғын үй және ЖКХ": 15.0,
    "Көлік": 12.0,
    "Байланыс": 4.0,
    "Денсаулық": 7.0,
    "Киім": 6.0,
    "Ойын-сауық": 5.0,
    "Басқа": 3.0,
}

_FALLBACK_BUCKET = "Басқа"

# Granular category (lowercase) -> broad bucket. Kazakh canonical + Russian legacy.
_CATEGORY_TO_BUCKET: dict[str, str] = {
    # Kazakh
    "азық-түлік": "Тамақтану",
    "сырттағы тамақ": "Тамақтану",
    "тұрғын үй": "Тұрғын үй және ЖКХ",
    "коммуналдық": "Тұрғын үй және ЖКХ",
    "көлік": "Көлік",
    "такси": "Көлік",
    "саяхат": "Көлік",
    "байланыс пен интернет": "Байланыс",
    "денсаулық": "Денсаулық",
    "киім": "Киім",
    "ойын-сауық": "Ойын-сауық",
    "жазылымдар": "Ойын-сауық",
    "білім": "Басқа",
    "балаларға": "Басқа",
    "сыйлықтар": "Басқа",
    "несие мен бөліп төлеу": "Басқа",
    "отбасыға көмек": "Басқа",
    "аударымдар": "Басқа",
    "басқа": "Басқа",
    # Legacy Russian
    "продукты": "Тамақтану",
    "еда вне дома": "Тамақтану",
    "жильё": "Тұрғын үй және ЖКХ",
    "коммуналка": "Тұрғын үй және ЖКХ",
    "транспорт": "Көлік",
    "путешествия": "Көлік",
    "связь и интернет": "Байланыс",
    "здоровье": "Денсаулық",
    "одежда": "Киім",
    "развлечения": "Ойын-сауық",
    "подписки": "Ойын-сауық",
    "образование": "Басқа",
    "детям": "Басқа",
    "подарки": "Басқа",
    "кредиты и рассрочка": "Басқа",
    "помощь семье": "Басқа",
    "переводы": "Басқа",
    "прочее": "Басқа",
}


def compare_shares(
    user_shares: dict[str, float],
) -> list[tuple[str, float, float]]:
    """Compare a user's category shares against the KZ reference buckets.

    ``user_shares`` maps category name -> percent of the user's spending.
    Categories are aggregated into broad buckets. Returns
    ``[(bucket, user_pct, kz_pct), ...]`` ordered by the size of the gap
    (user − kz) so the biggest deviations come first.
    """
    bucket_pct: dict[str, float] = {b: 0.0 for b in KZ_BUCKET_SHARES}
    for name, pct in user_shares.items():
        bucket = _CATEGORY_TO_BUCKET.get(name.strip().casefold(), _FALLBACK_BUCKET)
        bucket_pct[bucket] = bucket_pct.get(bucket, 0.0) + pct

    rows = [
        (bucket, bucket_pct.get(bucket, 0.0), kz_pct)
        for bucket, kz_pct in KZ_BUCKET_SHARES.items()
    ]
    rows.sort(key=lambda r: abs(r[1] - r[2]), reverse=True)
    return rows
