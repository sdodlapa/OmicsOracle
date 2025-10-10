"""
Comprehensive 100-paper test dataset for Sci-Hub/LibGen validation.

Papers selected to cover:
- Different publishers (Nature, Science, Cell, Springer, Wiley, Elsevier, etc.)
- Different years (1990s-2024)
- Different types (paywalled, OA, hybrid, preprints)
- Papers with DOI, PMID, both, or special cases
"""

COMPREHENSIVE_100_PAPERS = [
    # ============================================================================
    # CATEGORY 1: CLASSIC OLD PAYWALLED PAPERS (1990s-2010) - Should be in Sci-Hub
    # ============================================================================
    {
        "doi": "10.1126/science.1058040",
        "pmid": "11235003",
        "year": 2001,
        "publisher": "Science",
        "type": "paywalled",
    },
    {"doi": "10.1038/35057062", "pmid": "11237011", "year": 2001, "publisher": "Nature", "type": "paywalled"},
    {
        "doi": "10.1126/science.1072994",
        "pmid": "12130773",
        "year": 2002,
        "publisher": "Science",
        "type": "paywalled",
    },
    {
        "doi": "10.1038/nature12373",
        "pmid": "23877069",
        "year": 2013,
        "publisher": "Nature",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.cell.2013.05.039",
        "pmid": "23746838",
        "year": 2013,
        "publisher": "Cell",
        "type": "paywalled",
    },
    {
        "doi": "10.1126/science.1104742",
        "pmid": "15790847",
        "year": 2005,
        "publisher": "Science",
        "type": "paywalled",
    },
    {
        "doi": "10.1038/nature07517",
        "pmid": "19052620",
        "year": 2008,
        "publisher": "Nature",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.cell.2008.10.048",
        "pmid": "19013282",
        "year": 2008,
        "publisher": "Cell",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/S0140-6736(05)17870-2",
        "pmid": "15680456",
        "year": 2005,
        "publisher": "Lancet",
        "type": "paywalled",
    },
    {
        "doi": "10.1056/NEJMoa022152",
        "pmid": "12556542",
        "year": 2003,
        "publisher": "NEJM",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 2: RECENT PAYWALLED PAPERS (2020-2023) - May be in Sci-Hub
    # ============================================================================
    {
        "doi": "10.1038/s41586-020-2008-3",
        "pmid": "32132706",
        "year": 2020,
        "publisher": "Nature",
        "type": "paywalled",
    },
    {
        "doi": "10.1126/science.abb2507",
        "pmid": "32299953",
        "year": 2020,
        "publisher": "Science",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.cell.2020.02.052",
        "pmid": "32155444",
        "year": 2020,
        "publisher": "Cell",
        "type": "paywalled",
    },
    {
        "doi": "10.1038/s41586-021-03819-2",
        "pmid": "34265844",
        "year": 2021,
        "publisher": "Nature",
        "type": "paywalled",
    },
    {
        "doi": "10.1126/science.abf4063",
        "pmid": "33542145",
        "year": 2021,
        "publisher": "Science",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.cell.2021.02.032",
        "pmid": "33735609",
        "year": 2021,
        "publisher": "Cell",
        "type": "paywalled",
    },
    {
        "doi": "10.1038/s41586-022-04426-1",
        "pmid": "35107570",
        "year": 2022,
        "publisher": "Nature",
        "type": "paywalled",
    },
    {
        "doi": "10.1126/science.abm1483",
        "pmid": "35201898",
        "year": 2022,
        "publisher": "Science",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.cell.2022.01.003",
        "pmid": "35120655",
        "year": 2022,
        "publisher": "Cell",
        "type": "paywalled",
    },
    {
        "doi": "10.1038/s41586-023-05845-0",
        "pmid": "36890231",
        "year": 2023,
        "publisher": "Nature",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 3: VERY NEW PAPERS (2024) - Likely NOT in Sci-Hub yet
    # ============================================================================
    {
        "doi": "10.1126/science.adi4415",
        "pmid": "38753779",
        "year": 2024,
        "publisher": "Science",
        "type": "paywalled",
    },
    {
        "doi": "10.1038/s41586-024-07146-0",
        "pmid": "38480891",
        "year": 2024,
        "publisher": "Nature",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.cell.2024.01.029",
        "pmid": "38387464",
        "year": 2024,
        "publisher": "Cell",
        "type": "paywalled",
    },
    {
        "doi": "10.1038/s41586-024-08288-w",
        "pmid": None,
        "year": 2024,
        "publisher": "Nature",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.molcel.2024.02.015",
        "pmid": None,
        "year": 2024,
        "publisher": "Cell",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 4: SPRINGER/NATURE GROUP - Various journals
    # ============================================================================
    {
        "doi": "10.1038/s41467-024-46789-2",
        "pmid": None,
        "year": 2024,
        "publisher": "Nat Commun",
        "type": "OA",
    },
    {
        "doi": "10.1038/s41598-023-47123-9",
        "pmid": None,
        "year": 2023,
        "publisher": "Sci Reports",
        "type": "OA",
    },
    {
        "doi": "10.1007/s00018-024-05123-4",
        "pmid": None,
        "year": 2024,
        "publisher": "Springer",
        "type": "hybrid",
    },
    {
        "doi": "10.1007/s10719-024-10198-7",
        "pmid": None,
        "year": 2024,
        "publisher": "Springer",
        "type": "paywalled",
    },
    {
        "doi": "10.1038/s41588-023-01562-2",
        "pmid": "37932434",
        "year": 2023,
        "publisher": "Nat Genetics",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 5: ELSEVIER - Various journals
    # ============================================================================
    {
        "doi": "10.1016/S0140-6736(23)02750-7",
        "pmid": "38262407",
        "year": 2024,
        "publisher": "Lancet",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.molcel.2023.11.001",
        "pmid": "38056449",
        "year": 2023,
        "publisher": "Mol Cell",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.neuron.2023.10.015",
        "pmid": "37972609",
        "year": 2023,
        "publisher": "Neuron",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.immuni.2023.10.001",
        "pmid": "37913782",
        "year": 2023,
        "publisher": "Immunity",
        "type": "paywalled",
    },
    {
        "doi": "10.1016/j.cmet.2023.09.007",
        "pmid": "37852203",
        "year": 2023,
        "publisher": "Cell Metab",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 6: WILEY - Various journals
    # ============================================================================
    {"doi": "10.1002/advs.202308024", "pmid": None, "year": 2024, "publisher": "Adv Sci", "type": "OA"},
    {"doi": "10.1111/imm.13821", "pmid": None, "year": 2024, "publisher": "Immunology", "type": "hybrid"},
    {
        "doi": "10.1002/anie.202315129",
        "pmid": "37853894",
        "year": 2023,
        "publisher": "Angew Chem",
        "type": "paywalled",
    },
    {
        "doi": "10.1111/febs.16945",
        "pmid": "37700462",
        "year": 2023,
        "publisher": "FEBS J",
        "type": "paywalled",
    },
    {
        "doi": "10.1002/jcp.31085",
        "pmid": "37455515",
        "year": 2023,
        "publisher": "J Cell Physiol",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 7: OPEN ACCESS JOURNALS - Should be findable via Unpaywall
    # ============================================================================
    {
        "doi": "10.1371/journal.pgen.1011043",
        "pmid": None,
        "year": 2024,
        "publisher": "PLOS Genetics",
        "type": "OA",
    },
    {
        "doi": "10.1371/journal.pbio.3002912",
        "pmid": None,
        "year": 2024,
        "publisher": "PLOS Biology",
        "type": "OA",
    },
    {
        "doi": "10.1371/journal.pone.0296841",
        "pmid": None,
        "year": 2024,
        "publisher": "PLOS ONE",
        "type": "OA",
    },
    {
        "doi": "10.1186/s13059-024-03154-0",
        "pmid": None,
        "year": 2024,
        "publisher": "BMC Genomics",
        "type": "OA",
    },
    {
        "doi": "10.1186/s12915-024-01821-w",
        "pmid": None,
        "year": 2024,
        "publisher": "BMC Biology",
        "type": "OA",
    },
    {"doi": "10.7554/eLife.89410", "pmid": None, "year": 2024, "publisher": "eLife", "type": "OA"},
    {"doi": "10.3389/fimmu.2024.1352169", "pmid": None, "year": 2024, "publisher": "Frontiers", "type": "OA"},
    {"doi": "10.3390/ijms25052895", "pmid": "38474133", "year": 2024, "publisher": "MDPI", "type": "OA"},
    {"doi": "10.1093/nar/gkad1082", "pmid": "37994678", "year": 2023, "publisher": "NAR", "type": "OA"},
    {
        "doi": "10.1093/bioinformatics/btad633",
        "pmid": "37871883",
        "year": 2023,
        "publisher": "Bioinformatics",
        "type": "OA",
    },
    # ============================================================================
    # CATEGORY 8: PREPRINTS - Should be on bioRxiv/arXiv
    # ============================================================================
    {
        "doi": "10.1101/2024.02.15.580567",
        "pmid": None,
        "year": 2024,
        "publisher": "bioRxiv",
        "type": "preprint",
    },
    {
        "doi": "10.1101/2024.03.20.585912",
        "pmid": None,
        "year": 2024,
        "publisher": "bioRxiv",
        "type": "preprint",
    },
    {
        "doi": "10.1101/2023.12.15.571828",
        "pmid": None,
        "year": 2023,
        "publisher": "bioRxiv",
        "type": "preprint",
    },
    {
        "doi": "10.1101/2023.11.20.567926",
        "pmid": None,
        "year": 2023,
        "publisher": "bioRxiv",
        "type": "preprint",
    },
    {
        "doi": "10.1101/2023.10.18.562958",
        "pmid": None,
        "year": 2023,
        "publisher": "bioRxiv",
        "type": "preprint",
    },
    # ============================================================================
    # CATEGORY 9: AMERICAN CHEMICAL SOCIETY (ACS)
    # ============================================================================
    {
        "doi": "10.1021/jacs.3c11375",
        "pmid": "38054869",
        "year": 2023,
        "publisher": "JACS",
        "type": "paywalled",
    },
    {
        "doi": "10.1021/acs.chemrev.3c00611",
        "pmid": "38266214",
        "year": 2024,
        "publisher": "Chem Rev",
        "type": "paywalled",
    },
    {
        "doi": "10.1021/acsnano.3c09755",
        "pmid": "38236115",
        "year": 2024,
        "publisher": "ACS Nano",
        "type": "paywalled",
    },
    {
        "doi": "10.1021/bi500809n",
        "pmid": "25229933",
        "year": 2014,
        "publisher": "Biochemistry",
        "type": "paywalled",
    },
    {"doi": "10.1021/ja00051a040", "pmid": None, "year": 1990, "publisher": "JACS", "type": "paywalled"},
    # ============================================================================
    # CATEGORY 10: ROYAL SOCIETY OF CHEMISTRY (RSC)
    # ============================================================================
    {"doi": "10.1039/D3SC05339J", "pmid": "38239694", "year": 2024, "publisher": "Chem Sci", "type": "OA"},
    {
        "doi": "10.1039/D3CS00650F",
        "pmid": "38168691",
        "year": 2024,
        "publisher": "Chem Soc Rev",
        "type": "paywalled",
    },
    {
        "doi": "10.1039/D3EE03163H",
        "pmid": None,
        "year": 2024,
        "publisher": "Energy Environ",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 11: AMERICAN PHYSICAL SOCIETY (APS) / PHYSICS
    # ============================================================================
    {
        "doi": "10.1103/PhysRevLett.131.181001",
        "pmid": None,
        "year": 2023,
        "publisher": "Phys Rev Lett",
        "type": "paywalled",
    },
    {
        "doi": "10.1103/PhysRevX.13.041027",
        "pmid": None,
        "year": 2023,
        "publisher": "Phys Rev X",
        "type": "OA",
    },
    {
        "doi": "10.1103/PhysRevD.108.084038",
        "pmid": None,
        "year": 2023,
        "publisher": "Phys Rev D",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 12: AMERICAN ASSOCIATION FOR THE ADVANCEMENT OF SCIENCE (AAAS)
    # ============================================================================
    {"doi": "10.1126/sciadv.adj4801", "pmid": "38134279", "year": 2023, "publisher": "Sci Adv", "type": "OA"},
    {
        "doi": "10.1126/sciimmunol.adj2420",
        "pmid": "38170766",
        "year": 2024,
        "publisher": "Sci Immunol",
        "type": "paywalled",
    },
    {
        "doi": "10.1126/scitranslmed.adj9832",
        "pmid": "38170759",
        "year": 2024,
        "publisher": "Sci Transl Med",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 13: ROCKEFELLER UNIVERSITY PRESS
    # ============================================================================
    {"doi": "10.1084/jem.20230929", "pmid": "38175896", "year": 2024, "publisher": "J Exp Med", "type": "OA"},
    {
        "doi": "10.1083/jcb.202309094",
        "pmid": "38175915",
        "year": 2024,
        "publisher": "J Cell Biol",
        "type": "OA",
    },
    # ============================================================================
    # CATEGORY 14: OXFORD UNIVERSITY PRESS
    # ============================================================================
    {
        "doi": "10.1093/brain/awad393",
        "pmid": "38016716",
        "year": 2023,
        "publisher": "Brain",
        "type": "paywalled",
    },
    {
        "doi": "10.1093/molbev/msad273",
        "pmid": "38100354",
        "year": 2024,
        "publisher": "Mol Biol Evol",
        "type": "OA",
    },
    {
        "doi": "10.1093/hmg/ddad196",
        "pmid": "38048324",
        "year": 2024,
        "publisher": "Hum Mol Genet",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 15: CAMBRIDGE UNIVERSITY PRESS
    # ============================================================================
    {
        "doi": "10.1017/S0022112023009527",
        "pmid": None,
        "year": 2024,
        "publisher": "J Fluid Mech",
        "type": "paywalled",
    },
    {
        "doi": "10.1017/S0305004123000488",
        "pmid": None,
        "year": 2023,
        "publisher": "Math Proc Camb",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 16: TAYLOR & FRANCIS
    # ============================================================================
    {
        "doi": "10.1080/15548627.2023.2290829",
        "pmid": "38100282",
        "year": 2024,
        "publisher": "Autophagy",
        "type": "paywalled",
    },
    {
        "doi": "10.1080/21645515.2023.2291782",
        "pmid": "38100651",
        "year": 2024,
        "publisher": "Hum Vaccin",
        "type": "OA",
    },
    # ============================================================================
    # CATEGORY 17: IOP PUBLISHING
    # ============================================================================
    {
        "doi": "10.1088/1741-2560/13/2/026017",
        "pmid": "26902372",
        "year": 2016,
        "publisher": "J Neural Eng",
        "type": "paywalled",
    },
    {
        "doi": "10.1088/2053-1591/ad1870",
        "pmid": None,
        "year": 2024,
        "publisher": "Mater Res Express",
        "type": "paywalled",
    },
    # ============================================================================
    # CATEGORY 18: PROCEEDINGS OF THE NATIONAL ACADEMY OF SCIENCES (PNAS)
    # ============================================================================
    {
        "doi": "10.1073/pnas.2315638120",
        "pmid": "38011560",
        "year": 2023,
        "publisher": "PNAS",
        "type": "hybrid",
    },
    {
        "doi": "10.1073/pnas.2314756120",
        "pmid": "38011579",
        "year": 2023,
        "publisher": "PNAS",
        "type": "hybrid",
    },
    {
        "doi": "10.1073/pnas.2313491120",
        "pmid": "38011563",
        "year": 2023,
        "publisher": "PNAS",
        "type": "hybrid",
    },
    # ============================================================================
    # CATEGORY 19: EMBO PRESS
    # ============================================================================
    {
        "doi": "10.15252/embj.2023114122",
        "pmid": "38054612",
        "year": 2024,
        "publisher": "EMBO J",
        "type": "OA",
    },
    {
        "doi": "10.15252/msb.202311560",
        "pmid": "38054614",
        "year": 2024,
        "publisher": "Mol Syst Biol",
        "type": "OA",
    },
    # ============================================================================
    # CATEGORY 20: COMPANY OF BIOLOGISTS
    # ============================================================================
    {
        "doi": "10.1242/dev.202234",
        "pmid": "38054583",
        "year": 2024,
        "publisher": "Development",
        "type": "hybrid",
    },
    {
        "doi": "10.1242/jcs.261515",
        "pmid": "38054582",
        "year": 2024,
        "publisher": "J Cell Sci",
        "type": "hybrid",
    },
    # ============================================================================
    # CATEGORY 21: SPECIAL CASES - Edge cases for testing
    # ============================================================================
    # Very old paper (pre-digital)
    {
        "doi": "10.1038/171737a0",
        "pmid": "13054692",
        "year": 1953,
        "publisher": "Nature",
        "type": "paywalled",
    },  # Watson & Crick DNA
    # Paper with special characters in DOI
    {
        "doi": "10.1002/(SICI)1097-0134(199805)31:2<119::AID-PROT1>3.0.CO;2-J",
        "pmid": "9593265",
        "year": 1998,
        "publisher": "Wiley",
        "type": "paywalled",
    },
    # Retracted paper
    {
        "doi": "10.1126/science.1260419",
        "pmid": "25954009",
        "year": 2015,
        "publisher": "Science",
        "type": "retracted",
    },
    # Book chapter
    {
        "doi": "10.1007/978-1-4939-3578-9_1",
        "pmid": None,
        "year": 2016,
        "publisher": "Springer",
        "type": "book",
    },
    # Conference proceedings
    {"doi": "10.1109/CVPR.2016.90", "pmid": None, "year": 2016, "publisher": "IEEE", "type": "conference"},
]


# Summary statistics
def get_dataset_stats():
    """Get statistics about the test dataset."""
    stats = {
        "total": len(COMPREHENSIVE_100_PAPERS),
        "by_type": {},
        "by_year": {},
        "by_publisher": {},
        "with_pmid": 0,
        "with_doi": 0,
    }

    for paper in COMPREHENSIVE_100_PAPERS:
        # By type
        ptype = paper.get("type", "unknown")
        stats["by_type"][ptype] = stats["by_type"].get(ptype, 0) + 1

        # By year
        year = paper.get("year")
        if year:
            decade = f"{(year // 10) * 10}s"
            stats["by_year"][decade] = stats["by_year"].get(decade, 0) + 1

        # By publisher
        pub = paper.get("publisher", "unknown")
        stats["by_publisher"][pub] = stats["by_publisher"].get(pub, 0) + 1

        # Identifiers
        if paper.get("pmid"):
            stats["with_pmid"] += 1
        if paper.get("doi"):
            stats["with_doi"] += 1

    return stats


if __name__ == "__main__":
    stats = get_dataset_stats()
    print(f"Total papers: {stats['total']}")
    print(f"\nBy type:")
    for k, v in sorted(stats["by_type"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {k}: {v}")
    print(f"\nBy decade:")
    for k, v in sorted(stats["by_year"].items()):
        print(f"  {k}: {v}")
    print(f"\nWith PMID: {stats['with_pmid']}")
    print(f"With DOI: {stats['with_doi']}")
