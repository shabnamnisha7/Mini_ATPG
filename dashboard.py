from pathlib import Path
import json
import pandas as pd
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
st.set_page_config(page_title="Mini-ATPG Dashboard", page_icon="⚙", layout="wide")

st.markdown("""
<style>
.stApp{background:#0b1020;color:#e7ecf5}
[data-testid="stSidebar"]{background:#111a2e}
[data-testid="stMetric"]{background:#131e33;border:1px solid #263650;padding:16px;border-radius:12px}
.hero{padding:24px;border-radius:15px;background:linear-gradient(120deg,#14243d,#182d49);border:1px solid #2c496d}
.hero h1{color:#f4f7ff;margin:6px 0}.hero p{color:#bdcbe0;margin:0}
</style>
<div class="hero"><small>DESIGN FOR TESTABILITY · DIGITAL CIRCUITS</small>
<h1>Mini-ATPG Results Dashboard</h1>
<p>Automated Test Pattern Generation and Fault Coverage Analysis</p></div>
""", unsafe_allow_html=True)

def load_csv(names):
    for name in names:
        p = RESULTS / name
        if p.exists():
            try:
                return pd.read_csv(p), name
            except Exception:
                pass
    return None, None

compact, compact_name = load_csv(["compact_test_set.csv", "configurable_compact_test_set.csv"])
faults, fault_name = load_csv(["sample_fault_report.csv", "configurable_fault_report.csv"])

with st.sidebar:
    st.title("Mini-ATPG")
    page = st.radio("Sections", ["Overview", "Test Patterns", "Fault Analysis", "Input Solver", "Scope"])
    st.caption("Educational software prototype")

if page == "Overview":
    st.subheader("Example circuit")
    st.markdown("**Y = (A AND B) OR C**")
    a,b,c,d = st.columns(4)
    a.metric("Input combinations", "8", "2³ combinations")
    b.metric("Modeled faults", "10", "5 signals × SA0/SA1")
    c.metric("Compact test set", "4 vectors")
    d.metric("Modeled fault coverage", "100%", "Within this example model")
    left,right = st.columns(2)
    with left:
        st.markdown("#### Circuit logic")
        st.code("n1 = A AND B\nY  = n1 OR C\n\nInputs: A, B, C\nSignals: A, B, C, n1, Y", language="text")
        p = ROOT / "circuits" / "example_circuit.json"
        if p.exists():
            with st.expander("Circuit JSON"):
                try: st.json(json.loads(p.read_text(encoding="utf-8")))
                except Exception: st.write("Could not parse circuit JSON.")
    with right:
        st.markdown("#### Input space")
        chart = pd.DataFrame({"Set":["Compact test set","Other input combinations"],"Vectors":[4,4]})
        fig = px.pie(chart, names="Set", values="Vectors", hole=.58,
                     color_discrete_sequence=["#38d9c5","#30435f"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e7ecf5",
                          legend_title_text="", margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Available result files")
    csvs = sorted(p.name for p in RESULTS.glob("*.csv")) if RESULTS.exists() else []
    st.write(", ".join(csvs) if csvs else "No CSV files found in results/.")

elif page == "Test Patterns":
    st.subheader("Generated test patterns")
    if compact is not None:
        st.caption(f"Loaded from results/{compact_name}")
        st.dataframe(compact, use_container_width=True, hide_index=True)
        st.download_button("Download test set CSV", compact.to_csv(index=False).encode(),
                           "mini_atpg_compact_test_set.csv", "text/csv")
        vector_col = next((x for x in compact.columns if any(k in x.lower() for k in ["vector","pattern","input"])), None)
        if vector_col:
            counts = compact[vector_col].astype(str).value_counts().rename_axis("Vector").reset_index(name="Rows")
            fig = px.bar(counts, x="Vector", y="Rows", text="Rows")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e7ecf5")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Compact test CSV not found. Generate the project result files first.")

elif page == "Fault Analysis":
    st.subheader("Single stuck-at fault analysis")
    x,y,z = st.columns(3)
    x.metric("Fault types", "SA0 / SA1")
    y.metric("Modeled signal sites", "5")
    z.metric("Total modeled faults", "10")
    if faults is not None:
        st.caption(f"Loaded from results/{fault_name}")
        st.dataframe(faults, use_container_width=True, hide_index=True)
        st.download_button("Download fault report CSV", faults.to_csv(index=False).encode(),
                           "mini_atpg_fault_report.csv", "text/csv")
    else:
        st.info("Fault-report CSV not found in results/.")
    st.warning("100% coverage refers only to the small modeled fault set, not a physical chip or industrial circuit.")

elif page == "Input Solver":
    st.subheader("Interactive input solver")
    st.write("For **Y = (A AND B) OR C**, select a desired output.")
    desired = st.selectbox("Desired Y", [0, 1])
    rows = []
    for A in (0,1):
        for B in (0,1):
            for C in (0,1):
                Y = int((A and B) or C)
                if Y == desired:
                    rows.append({"A":A,"B":B,"C":C,"Expected Y":Y})
    st.metric("Matching input combinations", len(rows))
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.divider()
    st.subheader("Diagnostic test example")
    st.write("Candidate faults: C SA0 and Y SA0.")
    diagnostic = pd.DataFrame([
        {"A":1,"B":1,"C":0,"Healthy Y":1,"C SA0 predicted Y":1,"Y SA0 predicted Y":0},
        {"A":1,"B":1,"C":1,"Healthy Y":1,"C SA0 predicted Y":1,"Y SA0 predicted Y":0},
    ])
    st.dataframe(diagnostic, use_container_width=True, hide_index=True)
    st.caption("Illustrative predictions for the example circuit. Use the recommender script for generated recommendations.")

else:
    st.subheader("Implementation and limitations")
    st.markdown("""
**Implemented**
- Combinational circuit modeling and single stuck-at fault simulation
- Test-vector generation, fault coverage calculation, and greedy compaction
- Configurable JSON circuits, input solving, fault diagnosis, and diagnostic test recommendations
- CSV reports and automated unit tests

**Current limitations**
- Educational prototype, not an industrial ATPG engine
- Exhaustive enumeration does not scale efficiently to large circuits
- Software fault model only; no physical chip is tested

**Future development**
- Import synthesized gate-level netlists
- Add PODEM or SAT-based ATPG
- Evaluate benchmark circuits and compare runtime and coverage
""")
    st.info("Present the results as modeled fault coverage, and state the limitations clearly.")

st.divider()
st.caption("Mini-ATPG · Python prototype · Results shown are model-based")
