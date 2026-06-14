import json
import os
import streamlit as st

# Map profiles to their relative filenames
MUTATION_FILES = {
    "BRAF V600E": "braf.json",
    "EGFR Exon 19 Del": "egfr.json",
    "KRAS G12C": "kras.json",
    "EML4-ALK Fusion": "alk.json"
}

@st.cache_data
def load_profile(mutation_name):
    """Loads and returns the JSON file associated with a mutation profile."""
    if mutation_name not in MUTATION_FILES:
        raise ValueError(f"Mutation profile '{mutation_name}' not found.")
    
    file_name = MUTATION_FILES[mutation_name]
    # Path relative to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", file_name)
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def get_available_mutations():
    """Returns the list of available mutation names."""
    return list(MUTATION_FILES.keys())
