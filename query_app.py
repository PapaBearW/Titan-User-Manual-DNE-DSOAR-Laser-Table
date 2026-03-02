import streamlit as st
import pdfplumber
import re
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

# Find the D-Soar PDF by pattern (filename contains special characters)
_dsoar_matches = list(BASE_DIR.glob("*D-Soar*.pdf")) or list(BASE_DIR.glob("*(CE)*.pdf"))
_dsoar_path = _dsoar_matches[0] if _dsoar_matches else BASE_DIR / "D-Soar.pdf"

PDF_FILES = {
    "D-Soar Plus Fiber Laser Machine Manual": _dsoar_path,
    "CypCut User Manual": BASE_DIR / "CypCut-User-Manual.pdf",
}
CONTEXT_CHARS = 400   # characters of context shown around each match
MAX_RESULTS   = 30    # cap total results per search

# ── PDF loading (cached so it only runs once per session) ──────────────────────
@st.cache_resource(show_spinner="Loading manuals…")
def load_pdfs():
    """Extract text page-by-page from each PDF."""
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


def search(pages, query, case_sensitive=False):
    """Return list of {page, snippet, match_count} dicts for a query."""
    flags   = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)
    results = []
    for entry in pages:
        text = entry["text"]
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        # Build a snippet centred on the FIRST match
        m     = matches[0]
        start = max(0, m.start() - CONTEXT_CHARS // 2)
        end   = min(len(text), m.end() + CONTEXT_CHARS // 2)
        snippet = ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else "")
        results.append({
            "page":        entry["page"],
            "snippet":     snippet,
            "match_count": len(matches),
        })
    return results


def highlight(text, query, case_sensitive=False):
    """Wrap every occurrence of *query* in a yellow <mark> tag."""
    flags   = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(f"({re.escape(query)})", flags)
    return pattern.sub(r'<mark style="background:#FFD700;color:#000">\1</mark>', text)


# ── UI ─────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Titan Laser Manual Query",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Titan Laser Manual Query")
st.caption("Search the D-Soar Plus Fiber Laser Machine Manual and the CypCut User Manual")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Search Options")
    target = st.radio(
        "Search in",
        options=["Both Manuals"] + list(PDF_FILES.keys()),
        index=0,
    )
    case_sensitive = st.checkbox("Case-sensitive", value=False)
    st.markdown("---")
    st.markdown("**Manuals loaded:**")
    for name in PDF_FILES:
        st.markdown(f"- {name}")

# Main search bar
query = st.text_input(
    "Enter a keyword or phrase",
    placeholder="e.g. focus, nozzle, cutting speed, axis calibration",
)

if query.strip():
    all_data = load_pdfs()

    # Decide which manuals to include
    if target == "Both Manuals":
        search_set = all_data.items()
    else:
        search_set = [(target, all_data[target])]

    total_hits = 0
    found_any  = False

    for manual_name, pages in search_set:
        results = search(pages, query.strip(), case_sensitive)
        if not results:
            continue
        found_any = True
        total_hits += len(results)

        with st.expander(
            f"📖 **{manual_name}** — {len(results)} page(s) matched",
            expanded=True,
        ):
            shown = results[:MAX_RESULTS]
            for r in shown:
                st.markdown(
                    f"<small>Page <b>{r['page']}</b> &nbsp;·&nbsp; "
                    f"{r['match_count']} occurrence(s)</small>",
                    unsafe_allow_html=True,
                )
                highlighted = highlight(r["snippet"], query.strip(), case_sensitive)
                st.markdown(
                    f'<div style="'
                    f"font-size:0.9rem;line-height:1.6;"
                    f"background:#1e1e2e;color:#cdd6f4;"
                    f"padding:10px 14px;border-radius:6px;"
                    f'border-left:4px solid #89b4fa;margin-bottom:12px">'
                    f"{highlighted}</div>",
                    unsafe_allow_html=True,
                )
            if len(results) > MAX_RESULTS:
                st.info(
                    f"Showing first {MAX_RESULTS} of {len(results)} results. "
                    "Narrow your search for more specific results."
                )

    if not found_any:
        st.warning(f'No results found for **"{query}"**. Try a different keyword.')
    else:
        st.success(f'Found matches on **{total_hits}** page(s) total.')

elif query == "":
    st.info("Type a keyword above to start searching the manuals.")
