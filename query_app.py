import streamlit as st
import pdfplumber
import re
from pathlib import Path
from openai import OpenAI

#  Configuration 
BASE_DIR        = Path(__file__).parent
VECTOR_STORE_ID = "vs_69a4f1cf8ddc8191a050ad0d4218e580"

PDF_FILES = {
    "D-Soar Plus Fiber Laser Machine Manual": BASE_DIR / "DSoar-Manual-searchable.pdf",
    "CypCut User Manual":                     BASE_DIR / "CypCut-User-Manual.pdf",
}
CONTEXT_CHARS = 400
MAX_RESULTS   = 30

SYSTEM_PROMPT = """You are a technical documentation assistant designed to help users find
information inside the DNE D-SOAR PLUS G laser cutting system manuals and documentation.
Your primary task is to search the uploaded manuals and return accurate instructions,
procedures, and specifications from the documentation.

Follow these rules when responding:
1. Use the Manual as the Source of Truth - always prioritize information from the uploaded
   manuals. Do not invent procedures or machine settings. If the manual does not contain
   the answer, say: "Information not found in the available documentation."
2. Return Clear Technical Answers in this exact order:
   - What the manual says (summary)
   - Steps (if applicable)
   - Warnings / safety notes
   - Reference (page/section/table)
3. Safety Comes First - always include warnings or safety notes for questions about
   maintenance, electrical systems, laser components, gas systems, or mechanical adjustments.
4. No-Guessing Rule - if the manuals do not explicitly state the answer, do NOT infer or
   estimate. Say: "Information not found in the available documentation."
5. Cite Where It Came From - include page/section numbers or headings whenever available.
6. Keep responses concise, clear, and step-by-step when possible. Users are operators or
   technicians, not engineers."""


#  PDF loading 
@st.cache_resource(show_spinner="Loading manuals...")
def load_pdfs():
    data = {}
    for label, path in PDF_FILES.items():
        pages = []
        try:
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    pages.append({"page": i, "text": text})
        except Exception as e:
            st.error(f"Could not open {label}: {e}")
        data[label] = pages
    return data


#  Keyword search helpers 
def search(pages, query, case_sensitive=False):
    flags   = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)
    results = []
    for entry in pages:
        text    = entry["text"]
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        m       = matches[0]
        start   = max(0, m.start() - CONTEXT_CHARS // 2)
        end     = min(len(text), m.end() + CONTEXT_CHARS // 2)
        snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
        results.append({"page": entry["page"], "snippet": snippet, "match_count": len(matches)})
    return results


def highlight(text, query, case_sensitive=False):
    flags   = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(f"({re.escape(query)})", flags)
    return pattern.sub(r'<mark style="background:#FFD700;color:#000">\1</mark>', text)


#  OpenAI AI answer 
def ask_titan(question: str, api_key: str) -> str:
    client   = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=SYSTEM_PROMPT,
        input=question,
        tools=[{
            "type":             "file_search",
            "vector_store_ids": [VECTOR_STORE_ID],
            "max_num_results":  20,
        }],
    )
    for block in response.output:
        if hasattr(block, "content"):
            for part in block.content:
                if hasattr(part, "text"):
                    return part.text
    return "No answer returned."


#  Page setup 
st.set_page_config(
    page_title="Titan Laser Manual Query",
    page_icon="",
    layout="wide",
)

st.title(" Titan Laser Manual Assistant")
st.caption("Search the D-Soar Plus Fiber Laser Machine Manual and the CypCut User Manual")

#  Sidebar 
with st.sidebar:
    st.header("Options")
    target = st.radio(
        "Keyword search in",
        options=["Both Manuals"] + list(PDF_FILES.keys()),
        index=0,
    )
    case_sensitive = st.checkbox("Case-sensitive", value=False)
    st.markdown("---")
    st.markdown("**Manuals loaded:**")
    for name in PDF_FILES:
        st.markdown(f"- {name}")
    st.markdown("---")

# Read API key from secrets (set in .streamlit/secrets.toml or Streamlit Cloud secrets)
api_key = st.secrets.get("OPENAI_API_KEY", "")

#  Tabs 
tab_ai, tab_search = st.tabs([" Ask Titan (AI)", " Keyword Search"])

#  Tab 1: Keyword Search 
with tab_search:
    query = st.text_input(
        "Enter a keyword or phrase",
        placeholder="e.g. focus, nozzle, cutting speed, axis calibration",
    )

    if query.strip():
        all_data   = load_pdfs()
        search_set = all_data.items() if target == "Both Manuals" else [(target, all_data[target])]
        total_hits = 0
        found_any  = False

        for manual_name, pages in search_set:
            results = search(pages, query.strip(), case_sensitive)
            if not results:
                continue
            found_any   = True
            total_hits += len(results)

            with st.expander(f" **{manual_name}**  {len(results)} page(s) matched", expanded=True):
                for r in results[:MAX_RESULTS]:
                    st.markdown(
                        f"<small>Page <b>{r['page']}</b> &nbsp;&nbsp; {r['match_count']} occurrence(s)</small>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div style="font-size:0.9rem;line-height:1.6;background:#1e1e2e;'
                        f'color:#cdd6f4;padding:10px 14px;border-radius:6px;'
                        f'border-left:4px solid #89b4fa;margin-bottom:12px">'
                        f'{highlight(r["snippet"], query.strip(), case_sensitive)}</div>',
                        unsafe_allow_html=True,
                    )
                if len(results) > MAX_RESULTS:
                    st.info(f"Showing first {MAX_RESULTS} of {len(results)} results.")

        if not found_any:
            st.warning(f'No results found for **"{query}"**. Try a different keyword.')
        else:
            st.success(f'Found matches on **{total_hits}** page(s) total.')
    elif query == "":
        st.info("Type a keyword above to start searching the manuals.")


#  Tab 2: Ask Titan 
with tab_ai:
    st.markdown("Ask a natural language question and Titan will search the manuals and answer.")

    if not api_key:
        st.warning("Enter your OpenAI API key in the sidebar to use this feature.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask Titan a question about the laser machine..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Titan is searching the manuals..."):
                    try:
                        answer = ask_titan(prompt, api_key)
                    except Exception as e:
                        answer = f"Error: {e}"
                st.markdown(answer)

            st.session_state.messages.append({"role": "assistant", "content": answer})

        if st.session_state.get("messages"):
            if st.button("Clear chat"):
                st.session_state.messages = []
                st.rerun()
