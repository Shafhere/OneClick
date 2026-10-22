from app.models.schemas import CompanyProfile, ClaimEvidence


def test_profile_defaults_and_claim_evidence():
    profile = CompanyProfile(
        company_name="Example",
        executive_summary="An example company.",
        claim_evidence=[ClaimEvidence(claim="Offers a service", source_url="https://example.com", quote="Our service")],
    )
    assert profile.products == []
    assert profile.claim_evidence[0].quote == "Our service"
