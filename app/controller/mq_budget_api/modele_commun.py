from flask_restx import fields

etape_model = fields.String(
    description="Etape budgetaire",
    enum=[
        "budget primitif",
        "budget supplémentaire",
        "décision modificative",
        "compte administratif",
    ],
    required=True,
)