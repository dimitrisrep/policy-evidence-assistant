"""Fictional policies for reproducible tests. None represents an actual airline."""

import json
from pathlib import Path

POLICIES = {
    "refund": (
        "Refund processing",
        "For Example Air, an approved involuntary full refund is returned to the original payment method within seven business days after approval. The refund team sends a confirmation email when processing starts. A bank may require additional posting time. The passenger must not be promised an exact bank posting date.",
    ),
    "rebooking": (
        "Involuntary rebooking",
        "After an Example Air schedule disruption, an agent may request one alternative flight on the same route. Rebooking depends on seat availability and current carrier authorization. The agent must confirm the available flight before issuing a replacement ticket. Eligibility alone does not reserve a seat.",
    ),
    "cancellation": (
        "Airline cancellations",
        "When Example Air cancels a flight, support records the cancellation notice and offers a review of refund or replacement travel options. The passenger chooses which option to request. Support must check the relevant fare and disruption rules before making any change. Cancellation does not automatically issue a refund.",
    ),
    "baggage": (
        "Missing baggage",
        "A passenger whose checked suitcase does not arrive must report the missing baggage at the arrival airport baggage desk before leaving. The desk creates a property irregularity report and supplies a reference number. The passenger should retain bag tags and follow the tracing instructions supplied by the baggage team.",
    ),
    "checkin": (
        "Online check-in window",
        "Example Air online check-in opens 24 hours before the scheduled departure and closes two hours before departure. Passengers provide their booking reference and surname in the check-in portal. Airport document checks may still be required. A completed online check-in does not waive the boarding gate deadline.",
    ),
    "accessibility": (
        "Mobility assistance",
        "Wheelchair and mobility assistance requests should reach Example Air at least 48 hours before departure. Support records the assistance category and airport transfer needs. Late requests are forwarded to the accessibility team for a feasibility check. An agent must not request medical information that is unnecessary for arranging assistance.",
    ),
    "name": (
        "Passenger name corrections",
        "Minor spelling errors in an Example Air passenger name require a name-correction review. The agent compares the booking against the travel document, records the proposed correction and contacts the ticketing desk. Tickets cannot be transferred to another person through a name correction. The ticketing desk confirms any applicable charge.",
    ),
    "compensation": (
        "Compensation review",
        "A compensation request is handled separately from a ticket refund. The Example Air claims team reviews the disruption cause, journey details and applicable requirements. Agents must not infer compensation eligibility from a refund prediction. The passenger receives a claim reference after submitting the required information.",
    ),
    "payment": (
        "Duplicate payment charges",
        "For a possible duplicate card charge, support checks whether both entries are settled transactions or whether one is a temporary authorization. The payments team investigates two settled charges for the same booking. Support records transaction dates and masked card details only. Full card numbers must not be collected in chat.",
    ),
    "voucher": (
        "Travel vouchers",
        "An Example Air travel voucher is optional when an eligible passenger has another available remedy. Support explains the voucher expiry date and usage restrictions before obtaining explicit acceptance. A voucher cannot be substituted for a requested cash refund without confirmation. Unused voucher balances follow the terms shown on the voucher.",
    ),
    "connection": (
        "Missed connections",
        "For a protected Example Air connection affected by an earlier flight disruption, the agent checks the complete ticket and requests a suitable onward connection. Separate tickets require an individual review and are not automatically protected. A revised connection must respect the airport minimum connection time and seat availability.",
    ),
    "contact": (
        "Updating contact details",
        "A passenger may request an update to the email address or telephone number linked to an Example Air booking after identity verification. Support confirms the new contact details by reading them back and sends an update confirmation. A contact-detail change does not modify the passenger name or ticket ownership.",
    ),
}
QUERIES = {
    "refund": [
        "How long does an approved refund take?",
        "Where is an approved reimbursement sent?",
        "Can support promise a bank posting date?",
    ],
    "rebooking": [
        "Does rebooking guarantee a reserved seat?",
        "What must an agent verify before issuing a replacement ticket?",
        "Can I request an alternative flight on the same route?",
    ],
    "cancellation": [
        "Does a cancellation automatically refund my ticket?",
        "What information is recorded when the airline cancels a flight?",
        "Who chooses between refund and replacement travel after airline cancellation?",
    ],
    "baggage": [
        "Where do I report a missing suitcase?",
        "What is a property irregularity report?",
        "Should I keep my bag tags for tracing?",
    ],
    "checkin": [
        "When does online check-in open?",
        "What details does the check-in portal need?",
        "Does online check-in waive the boarding gate deadline?",
    ],
    "accessibility": [
        "How early should I request wheelchair assistance?",
        "Who reviews late mobility assistance requests?",
        "What assistance information should an agent record?",
    ],
    "name": [
        "Can I transfer my ticket through a name correction?",
        "Who approves a passenger spelling correction?",
        "Which document is checked for a spelling error?",
    ],
    "compensation": [
        "Can a refund prediction prove compensation eligibility?",
        "Who reviews compensation claims?",
        "Are compensation requests separate from ticket refunds?",
    ],
    "payment": [
        "How are duplicate card charges investigated?",
        "Can an authorization look like a second settled charge?",
        "May support collect full card numbers in chat?",
    ],
    "voucher": [
        "Must a passenger accept a travel voucher?",
        "Can a voucher replace a requested cash refund without confirmation?",
        "What voucher terms should be explained?",
    ],
    "connection": [
        "Are separate tickets automatically protected for missed connections?",
        "What checks apply to a revised onward connection?",
        "Does a protected connection need seat availability?",
    ],
    "contact": [
        "How can I update the email address linked to my booking?",
        "Does changing a telephone number change ticket ownership?",
        "What verification is needed for contact-detail changes?",
    ],
}


def main():
    destination = Path("data")
    destination.mkdir(exist_ok=True)
    documents = [
        {
            "id": identity,
            "title": title,
            "airline": "EXAMPLE",
            "valid_from": "2026-01-01",
            "valid_to": "2027-12-31",
            "source": f"demo://example-air/{identity}",
            "text": text,
        }
        for identity, (title, text) in POLICIES.items()
    ]
    documents += [
        {
            "id": "expired-refund",
            "title": "Expired refund processing",
            "airline": "EXAMPLE",
            "valid_from": "2024-01-01",
            "valid_to": "2024-12-31",
            "source": "demo://example-air/expired-refund",
            "text": "The old refund processing target was ninety business days. This expired fictional document is a metadata-filtering test.",
        },
        {
            "id": "different-carrier",
            "title": "Different carrier refund processing",
            "airline": "ALTERNATE",
            "valid_from": "2026-01-01",
            "valid_to": "2027-12-31",
            "source": "demo://alternate-air/refund",
            "text": "Alternate Air refunds are reviewed by a different refund team. This fictional carrier has its own processing policy.",
        },
    ]
    queries = [
        {
            "id": f"{identity}-{i}",
            "query": text,
            "relevant_document_ids": [identity],
            "airline": "EXAMPLE",
            "as_of": "2026-10-27",
        }
        for identity, questions in QUERIES.items()
        for i, text in enumerate(questions)
    ]
    for i, text in enumerate(
        [
            "What is the quantum entanglement theorem?",
            "Recommend a vegetarian lasagna recipe",
            "Explain volcanic basalt chemistry",
            "How do I configure Kubernetes ingress?",
            "What are the cinema opening hours?",
        ]
    ):
        queries.append(
            {
                "id": f"unknown-{i}",
                "query": text,
                "relevant_document_ids": [],
                "airline": "EXAMPLE",
                "as_of": "2026-10-27",
            }
        )
    queries.append(
        {
            "id": "unknown-carrier",
            "query": "When does the refund arrive?",
            "relevant_document_ids": [],
            "airline": "NOT_IN_CORPUS",
            "as_of": "2026-10-27",
        }
    )
    for name, rows in [("policies", documents), ("queries", queries)]:
        (destination / f"{name}.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
