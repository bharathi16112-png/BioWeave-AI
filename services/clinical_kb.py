"""Curated clinical knowledge base with unified mutation profile keys."""

from __future__ import annotations

# Canonical keys align with demo profiles in data_loader.MUTATION_FILES
MUTATION_PROFILES: dict[str, dict] = {
    "BRAF V600E": {
        "gene": "BRAF",
        "variant": "V600E",
        "protein_change": "V600E",
        "family": "MAPK",
        "tumor_type": "Melanoma / NSCLC",
        "pathway": "MAPK / ERK Pathway",
        "drug": "Dabrafenib + Trametinib",
        "baseline": 0.94,
        "post": 0.28,
        "rationale": (
            "The BRAF V600E mutation bypasses upstream RAS regulation, leading to continuous "
            "monomeric activation of B-Raf. Combining Dabrafenib (BRAF inhibitor) with "
            "Trametinib (MEK inhibitor) dual-blocks the cascade, significantly reducing "
            "vertical pathway escape and delaying acquired resistance channels."
        ),
        "nodes": [
            {"id": "N1", "label": "BRAF V600E", "type": "mutation", "status": "active"},
            {"id": "N2", "label": "B-Raf Kinase Monomer", "type": "protein", "status": "constitutively_active"},
            {"id": "N3", "label": "MEK 1/2 Phosphorylation", "type": "pathway_node", "status": "hyperactive"},
            {"id": "N4", "label": "ERK 1/2 Translocation", "type": "pathway_node", "status": "hyperactive"},
            {"id": "N5", "label": "Cell Proliferation", "type": "biological_outcome", "status": "abnormal"},
            {"id": "N6", "label": "Dabrafenib", "type": "therapeutic", "mechanism": "BRAF Inhibitor"},
            {"id": "N7", "label": "Trametinib", "type": "therapeutic", "mechanism": "MEK Inhibitor"},
        ],
        "edges": [
            {"source": "N1", "target": "N2", "relation": "encodes_variant", "type": "genetic"},
            {"source": "N2", "target": "N3", "relation": "activates", "type": "signaling"},
            {"source": "N3", "target": "N4", "relation": "phosphorylates", "type": "signaling"},
            {"source": "N4", "target": "N5", "relation": "drives", "type": "phenotype"},
            {"source": "N6", "target": "N2", "relation": "inhibits", "type": "intervention"},
            {"source": "N7", "target": "N3", "relation": "inhibits", "type": "intervention"},
        ],
        "exclusions": [
            {
                "drug_name": "Cetuximab / Panitumumab",
                "class": "EGFR Monoclonal Antibody",
                "status": "Contraindicated",
                "reasoning": (
                    "BRAF V600E acts downstream of EGFR. Upstream receptor blockade "
                    "provides no benefit — mutant B-Raf propagates mitotic signals "
                    "independent of receptor activation."
                ),
            },
            {
                "drug_name": "Standard Chemotherapy (FOLFOX/FOLFIRI)",
                "class": "Cytotoxic Agent",
                "status": "Deprioritised",
                "reasoning": (
                    "Patient qualifies for a highly selective targeted inhibitor regimen "
                    "with superior response rates and tolerability profile per NCCN v2.2026."
                ),
            },
        ],
        "evidence": [
            {
                "step": 1,
                "source_name": "ClinVar",
                "assertion": "Variant: Pathogenic",
                "evidence_id": "VCV000013961",
                "confidence_score": 0.99,
                "url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/VCV000013961/",
                "snippet": (
                    "BRAF p.Val600Glu (V600E) is a well-characterised oncogenic driver "
                    "altering the kinase activation segment."
                ),
            },
            {
                "step": 2,
                "source_name": "KEGG Pathway DB",
                "assertion": "MAPK Cascade Overactivation",
                "evidence_id": "hsa04010",
                "confidence_score": 0.95,
                "url": "https://www.genome.jp/dbget-bin/www_bget?pathway+hsa04010",
                "snippet": (
                    "Mutant BRAF leads to constitutive phosphorylation of MEK1/2 and ERK1/2, "
                    "overriding growth checkpoints."
                ),
            },
            {
                "step": 3,
                "source_name": "OncoKB",
                "assertion": "Approved Combination Therapy",
                "evidence_id": "OncoKB-BRAF",
                "confidence_score": 1.00,
                "url": "https://www.oncokb.org/gene/BRAF",
                "snippet": (
                    "Dabrafenib + Trametinib is FDA-approved for BRAF V600E+ "
                    "unresectable/metastatic melanoma."
                ),
            },
        ],
    },
    "EGFR Exon 19 Del": {
        "gene": "EGFR",
        "variant": "Exon 19 Deletion",
        "protein_change": "Exon 19 Del",
        "family": "Receptor Tyrosine Kinase",
        "tumor_type": "Non-Small Cell Lung Carcinoma",
        "pathway": "JAK / STAT & PI3K-AKT Pathway",
        "drug": "Osimertinib (Tagrisso)",
        "baseline": 0.88,
        "post": 0.12,
        "rationale": (
            "EGFR exon 19 deletions constitutively activate the intracellular kinase domain. "
            "Osimertinib (3rd-generation TKI) irreversibly binds the mutant EGFR ATP pocket, "
            "suppressing downstream JAK/STAT and PI3K-AKT signaling while sparing wild-type EGFR."
        ),
        "nodes": [
            {"id": "N1", "label": "EGFR Exon 19 Del", "type": "mutation", "status": "active"},
            {"id": "N2", "label": "EGFR Kinase Domain", "type": "protein", "status": "constitutively_active"},
            {"id": "N3", "label": "JAK/STAT Signaling", "type": "pathway_node", "status": "hyperactive"},
            {"id": "N4", "label": "PI3K-AKT Cascade", "type": "pathway_node", "status": "hyperactive"},
            {"id": "N5", "label": "Tumour Cell Survival", "type": "biological_outcome", "status": "abnormal"},
            {"id": "N6", "label": "Osimertinib", "type": "therapeutic", "mechanism": "3rd-Gen EGFR TKI"},
        ],
        "edges": [
            {"source": "N1", "target": "N2", "relation": "activates", "type": "genetic"},
            {"source": "N2", "target": "N3", "relation": "stimulates", "type": "signaling"},
            {"source": "N2", "target": "N4", "relation": "stimulates", "type": "signaling"},
            {"source": "N3", "target": "N5", "relation": "drives", "type": "phenotype"},
            {"source": "N4", "target": "N5", "relation": "drives", "type": "phenotype"},
            {"source": "N6", "target": "N2", "relation": "inhibits", "type": "intervention"},
        ],
        "exclusions": [
            {
                "drug_name": "Erlotinib / Gefitinib (1st-Gen)",
                "class": "1st-Gen EGFR TKI",
                "status": "Deprioritised",
                "reasoning": (
                    "Osimertinib shows superior PFS and CNS penetration vs 1st-gen TKIs "
                    "(FLAURA trial). 1st-gen agents also lack activity against T790M resistance."
                ),
            },
            {
                "drug_name": "Platinum-based Chemotherapy",
                "class": "Cytotoxic Agent",
                "status": "Deprioritised",
                "reasoning": (
                    "NCCN guidelines recommend targeted TKI therapy as first-line for EGFR-mutant NSCLC."
                ),
            },
        ],
        "evidence": [
            {
                "step": 1,
                "source_name": "ClinVar",
                "assertion": "Variant: Pathogenic",
                "evidence_id": "VCV000016256",
                "confidence_score": 0.99,
                "url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/VCV000016256/",
                "snippet": (
                    "EGFR exon 19 deletions are recurrent activating mutations in NSCLC."
                ),
            },
            {
                "step": 2,
                "source_name": "KEGG Pathway DB",
                "assertion": "PI3K-AKT Overactivation",
                "evidence_id": "hsa04151",
                "confidence_score": 0.94,
                "url": "https://www.genome.jp/dbget-bin/www_bget?pathway+hsa04151",
                "snippet": (
                    "Activated EGFR recruits PI3K, triggering AKT-mTOR axis and promoting cell survival."
                ),
            },
            {
                "step": 3,
                "source_name": "OncoKB",
                "assertion": "First-Line Approval",
                "evidence_id": "OncoKB-EGFR",
                "confidence_score": 1.00,
                "url": "https://www.oncokb.org/gene/EGFR",
                "snippet": (
                    "Osimertinib is FDA-approved as first-line therapy for EGFR exon 19 del "
                    "/ L858R metastatic NSCLC."
                ),
            },
        ],
    },
    "KRAS G12C": {
        "gene": "KRAS",
        "variant": "G12C",
        "protein_change": "G12C",
        "family": "RAS GTPase",
        "tumor_type": "NSCLC / Colorectal Carcinoma",
        "pathway": "RAS / MAPK Signaling",
        "drug": "Sotorasib (Lumakras)",
        "baseline": 0.95,
        "post": 0.22,
        "rationale": (
            "KRAS G12C traps the protein in a GTP-bound active state. Sotorasib irreversibly "
            "covalently binds the cysteine-12 residue in the GDP-bound (inactive) state, "
            "locking KRAS off and blocking downstream RAS-MAPK and PI3K cascades."
        ),
        "nodes": [
            {"id": "N1", "label": "KRAS G12C", "type": "mutation", "status": "active"},
            {"id": "N2", "label": "KRAS GTPase", "type": "protein", "status": "constitutively_active"},
            {"id": "N3", "label": "RAF Kinase Activation", "type": "pathway_node", "status": "hyperactive"},
            {"id": "N4", "label": "MEK / ERK Cascade", "type": "pathway_node", "status": "hyperactive"},
            {"id": "N5", "label": "Tumour Proliferation", "type": "biological_outcome", "status": "abnormal"},
            {"id": "N6", "label": "Sotorasib", "type": "therapeutic", "mechanism": "KRAS G12C Covalent Inhibitor"},
        ],
        "edges": [
            {"source": "N1", "target": "N2", "relation": "locks_active", "type": "genetic"},
            {"source": "N2", "target": "N3", "relation": "activates", "type": "signaling"},
            {"source": "N3", "target": "N4", "relation": "phosphorylates", "type": "signaling"},
            {"source": "N4", "target": "N5", "relation": "drives", "type": "phenotype"},
            {"source": "N6", "target": "N2", "relation": "covalent_lock", "type": "intervention"},
        ],
        "exclusions": [
            {
                "drug_name": "EGFR-targeted Monoclonal Antibodies",
                "class": "Anti-EGFR mAb",
                "status": "Contraindicated",
                "reasoning": (
                    "RAS mutations confer primary resistance to EGFR antibodies (e.g. Cetuximab). "
                    "Downstream KRAS activation bypasses receptor blockade entirely."
                ),
            },
        ],
        "evidence": [
            {
                "step": 1,
                "source_name": "ClinVar",
                "assertion": "Variant: Pathogenic",
                "evidence_id": "VCV000012375",
                "confidence_score": 0.99,
                "url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/12375/",
                "snippet": (
                    "KRAS p.Gly12Cys introduces a cysteine enabling covalent targeting; "
                    "constitutively activates RAS."
                ),
            },
            {
                "step": 2,
                "source_name": "KEGG Pathway DB",
                "assertion": "RAS Signaling Cascade",
                "evidence_id": "hsa04014",
                "confidence_score": 0.96,
                "url": "https://www.genome.jp/dbget-bin/www_bget?pathway+hsa04014",
                "snippet": (
                    "Constitutively active KRAS drives persistent RAF-MEK-ERK signaling, "
                    "promoting uncontrolled proliferation."
                ),
            },
            {
                "step": 3,
                "source_name": "OncoKB",
                "assertion": "First KRAS Inhibitor Approval",
                "evidence_id": "OncoKB-KRAS",
                "confidence_score": 1.00,
                "url": "https://www.oncokb.org/gene/KRAS",
                "snippet": (
                    "Sotorasib received FDA accelerated approval for KRAS G12C+ metastatic NSCLC "
                    "(CodeBreaK 100 trial)."
                ),
            },
        ],
    },
    "EML4-ALK Fusion": {
        "gene": "ALK",
        "variant": "EML4-ALK Fusion",
        "protein_change": "Fusion",
        "family": "Receptor Tyrosine Kinase",
        "tumor_type": "Non-Small Cell Lung Carcinoma",
        "pathway": "ALK / STAT3 & PI3K Cascade",
        "drug": "Alectinib (Alecensa)",
        "baseline": 0.90,
        "post": 0.15,
        "rationale": (
            "EML4-ALK fusion creates a constitutively active chimeric kinase. Alectinib "
            "selectively inhibits ALK (and RET), achieving superior CNS penetration vs "
            "crizotinib — critical for preventing brain metastases in ALK+ NSCLC."
        ),
        "nodes": [
            {"id": "N1", "label": "EML4-ALK Fusion", "type": "mutation", "status": "active"},
            {"id": "N2", "label": "ALK Kinase Domain", "type": "protein", "status": "constitutively_active"},
            {"id": "N3", "label": "STAT3 Activation", "type": "pathway_node", "status": "hyperactive"},
            {"id": "N4", "label": "PI3K / AKT Signaling", "type": "pathway_node", "status": "hyperactive"},
            {"id": "N5", "label": "Anti-Apoptosis", "type": "biological_outcome", "status": "abnormal"},
            {"id": "N6", "label": "Alectinib", "type": "therapeutic", "mechanism": "2nd-Gen ALK Inhibitor"},
        ],
        "edges": [
            {"source": "N1", "target": "N2", "relation": "fuses_activates", "type": "genetic"},
            {"source": "N2", "target": "N3", "relation": "phosphorylates", "type": "signaling"},
            {"source": "N2", "target": "N4", "relation": "activates", "type": "signaling"},
            {"source": "N3", "target": "N5", "relation": "drives", "type": "phenotype"},
            {"source": "N4", "target": "N5", "relation": "drives", "type": "phenotype"},
            {"source": "N6", "target": "N2", "relation": "inhibits", "type": "intervention"},
        ],
        "exclusions": [
            {
                "drug_name": "Crizotinib (1st-Gen ALK)",
                "class": "1st-Gen ALK Inhibitor",
                "status": "Deprioritised",
                "reasoning": (
                    "Alectinib demonstrated superior PFS and CNS activity over crizotinib "
                    "in the ALEX trial. Crizotinib has limited blood-brain barrier penetration."
                ),
            },
        ],
        "evidence": [
            {
                "step": 1,
                "source_name": "ClinVar",
                "assertion": "Rearrangement: Pathogenic",
                "evidence_id": "VCV000030458",
                "confidence_score": 0.98,
                "url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/30458/",
                "snippet": (
                    "EML4-ALK inversion on chromosome 2p creates a constitutively active fusion oncogene."
                ),
            },
            {
                "step": 2,
                "source_name": "KEGG Pathway DB",
                "assertion": "ALK Signaling Overactivation",
                "evidence_id": "hsa05223",
                "confidence_score": 0.93,
                "url": "https://www.genome.jp/dbget-bin/www_bget?pathway+hsa05223",
                "snippet": (
                    "ALK fusion activates STAT3, PI3K/AKT, and MAPK pathways, "
                    "promoting survival and proliferation."
                ),
            },
            {
                "step": 3,
                "source_name": "OncoKB",
                "assertion": "First-Line Approval (ALEX)",
                "evidence_id": "OncoKB-ALK",
                "confidence_score": 1.00,
                "url": "https://www.oncokb.org/gene/ALK",
                "snippet": (
                    "Alectinib is FDA-approved as first-line therapy for ALK-positive metastatic NSCLC."
                ),
            },
        ],
    },
}

# Backward-compatible aliases from older live pipeline keys
MUTATION_ALIASES = {
    "EGFR L858R": "EGFR Exon 19 Del",
    "ALK Fusion": "EML4-ALK Fusion",
}


def resolve_profile_key(mutation_key: str) -> str:
    """Map legacy or alias mutation labels to canonical profile keys."""
    if mutation_key in MUTATION_PROFILES:
        return mutation_key
    return MUTATION_ALIASES.get(mutation_key, mutation_key)


def get_profile(mutation_key: str) -> dict:
    """Return the clinical profile for a canonical mutation key."""
    key = resolve_profile_key(mutation_key)
    if key not in MUTATION_PROFILES:
        raise KeyError(f"No clinical profile for mutation '{mutation_key}'")
    return MUTATION_PROFILES[key]
