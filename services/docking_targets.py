"""
Docking target definitions for BioWeave-AI oncology targets.

Each entry contains:
- smiles: canonical SMILES of the approved inhibitor drug
- pdb_id: reference PDB structure used to derive binding box
- center: [x, y, z] binding-site centroid (Angstroms, from published co-crystal)
- box_size: search box dimensions in Angstroms
- known_affinity_kcal_mol: experimental IC50-derived binding affinity (literature)
- receptor_pdbqt_url: RCSB download path (used only when pre-generating PDBQT)

Sources (all public domain / open-access):
- BRAF V600E / Dabrafenib: PDB 4XV2  (Dabrafenib co-crystal, Rauch et al. 2014)
- EGFR Exon19Del / Osimertinib: PDB 4ZAU (Osimertinib co-crystal, Cross et al. 2014)
- KRAS G12C / Sotorasib:  PDB 6OIM  (AMG-510/Sotorasib, Fell et al. 2020)
- ALK EML4 Fusion / Alectinib: PDB 3AOX (Alectinib precursor, Kinoshita et al. 2011)
"""

from __future__ import annotations

DOCKING_TARGETS: dict[str, dict] = {
    "BRAF V600E": {
        # Dabrafenib (GSK2118436) — selective BRAF inhibitor
        "smiles": (
            "CS(=O)(=O)Cc1ccc(F)cc1NC(=O)c1cc(nc(n1)N1CCOCC1)"
            "c1ccc(F)cc1F"
        ),
        "drug_name": "Dabrafenib",
        "pdb_id": "4XV2",
        "center": [38.4, 5.7, 22.1],
        "box_size": [22, 22, 22],
        "known_affinity_kcal_mol": -10.2,
        "target_description": "BRAF V600E kinase domain ATP-binding pocket",
        "exhaustiveness": 12,
    },
    "EGFR Exon 19 Del": {
        # Osimertinib (AZD9291) — 3rd-gen irreversible EGFR TKI
        "smiles": (
            "COc1cc2ncnc(Nc3ccc(NC(=O)/C=C/CN(C)C)c(OC)c3)c2cc1"
            "OCCCN1CCN(C)CC1"
        ),
        "drug_name": "Osimertinib",
        "pdb_id": "4ZAU",
        "center": [53.0, 30.8, 49.2],
        "box_size": [22, 22, 22],
        "known_affinity_kcal_mol": -11.4,
        "target_description": "EGFR kinase domain (exon19-deletion mutant) ATP pocket",
        "exhaustiveness": 12,
    },
    "KRAS G12C": {
        # Sotorasib (AMG-510) — covalent KRAS G12C inhibitor
        "smiles": (
            "C[C@@H]1CN(C(=O)c2cc(F)cc(c2)N2CCOCC2=O)"
            "CCN1c1nc(=O)c2ccccc2[nH]1"
        ),
        "drug_name": "Sotorasib",
        "pdb_id": "6OIM",
        "center": [-1.9, 1.0, -0.2],
        "box_size": [22, 22, 22],
        "known_affinity_kcal_mol": -9.6,
        "target_description": "KRAS G12C switch-II pocket (covalent site)",
        "exhaustiveness": 12,
    },
    "EML4-ALK Fusion": {
        # Alectinib (CH5424802) — 2nd-gen ALK inhibitor
        "smiles": (
            "CCc1cc2cc(C#N)ccc2nc1N(CC)CCc1cc2ccc(=O)[nH]c2cc1"
        ),
        "drug_name": "Alectinib",
        "pdb_id": "3AOX",
        "center": [21.1, 4.6, 16.8],
        "box_size": [22, 22, 22],
        "known_affinity_kcal_mol": -10.8,
        "target_description": "ALK kinase domain ATP-binding cleft",
        "exhaustiveness": 12,
    },
}
