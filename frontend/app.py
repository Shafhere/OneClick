
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="OneClick | Company Intelligence",
    page_icon="🔎",
    layout="wide",
)

st.title("OneClick")
st.caption("Understand a company from its public website.")

with st.sidebar:
    st.header("Research a company")
    target_url = st.text_input(
        "Company website URL",
        placeholder="https://example.com",
    )
    analyze = st.button(
        "Generate intelligence report",
        type="primary",
        use_container_width=True,
    )

if analyze:
    if not target_url.strip():
        st.warning("Enter a company website URL.")
    else:
        with st.spinner(
            "Collecting pages, extracting company information, "
            "and building the research index..."
        ):
            try:
                response = requests.post(
                    f"{API_URL}/analyze",
                    json={"url": target_url.strip()},
                    timeout=300,
                )
                response.raise_for_status()

                result = response.json()
                st.session_state["intel_url"] = target_url.strip()
                st.session_state["intel_result"] = result

            except requests.RequestException as exc:
                st.error(f"Analysis failed: {exc}")

if "intel_result" in st.session_state:
    result = st.session_state["intel_result"]
    profile = result["profile"]
    url = st.session_state["intel_url"]

    st.header(profile["company_name"])
    st.write(profile["executive_summary"])

    st.caption(
        f"Pages collected: {result['pages_crawled']} | "
        "Research time: current session"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Industry", profile["industry"])
    col2.metric("Headquarters", profile["headquarters"])
    col3.metric("Business model", profile["business_model"])

    st.divider()

    st.subheader("Company overview")
    left, right = st.columns(2)

    with left:
        st.markdown("**Target audience**")
        st.write(profile["target_audience"])

        st.markdown("**Pricing model**")
        st.write(profile["pricing_model"])

        st.markdown("**Founding year**")
        st.write(profile["founding_year"] or "Not found")

    with right:
        st.markdown("**Partnerships**")
        if profile["partnerships"]:
            for item in profile["partnerships"]:
                st.write(f"- {item}")
        else:
            st.write("No information found in collected pages.")

        st.markdown("**Sustainability**")
        if profile["sustainability"]:
            for item in profile["sustainability"]:
                st.write(f"- {item}")
        else:
            st.write("No information found in collected pages.")

    st.divider()
    st.subheader("Products and services")

    if profile["products"]:
        for product in profile["products"]:
            with st.expander(product["name"]):
                st.write(product["description"])
                st.markdown("**Sources**")

                for source in product["source_urls"]:
                    st.markdown(f"- [{source}]({source})")
    else:
        st.info("No products or services were identified.")

    st.subheader("Research gaps")
    if profile["known_gaps"]:
        for gap in profile["known_gaps"]:
            st.write(f"- {gap}")
    else:
        st.write("No gaps were reported by the extraction model.")

    st.subheader("Collected source pages")
    for page in result["pages"]:
        st.markdown(f"- [{page['title'] or page['url']}]({page['url']})")

    st.divider()
    st.subheader("Ask questions about this company")

    question = st.text_input(
        "Your question",
        placeholder="How does this company make money?",
        key="company_question",
    )

    if st.button("Ask OneClick"):
        if question.strip():
            with st.spinner("Searching company evidence..."):
                try:
                    response = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "url": url,
                            "question": question.strip(),
                        },
                        timeout=120,
                    )
                    response.raise_for_status()
                    answer = response.json()

                    st.markdown("**Answer**")
                    st.write(answer["answer"])

                    st.markdown("**Retrieved source pages**")
                    for source in answer.get("sources", []):
                        st.markdown(f"- [{source}]({source})")

                except requests.RequestException as exc:
                    st.error(f"Chat failed: {exc}")
