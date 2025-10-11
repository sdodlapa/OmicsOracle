"""
Biomarker knowledge graph construction.

Builds a knowledge graph connecting datasets, papers, biomarkers, and diseases.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from omics_oracle_v2.lib.citations.models import UsageAnalysis
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


@dataclass
class BiomarkerNode:
    """Node representing a biomarker."""

    name: str
    biomarker_type: str = "gene"  # gene, protein, metabolite, etc.
    discovered_in_papers: List[str] = field(default_factory=list)
    validation_status: str = "unvalidated"  # unvalidated, validated, clinical
    diseases: Set[str] = field(default_factory=set)
    first_discovery_year: Optional[int] = None
    citation_count: int = 0


@dataclass
class PaperNode:
    """Node representing a research paper."""

    paper_id: str
    title: str
    year: Optional[int] = None
    dataset_used: Optional[str] = None
    biomarkers_discovered: List[str] = field(default_factory=list)
    application_domain: Optional[str] = None
    methodology: Optional[str] = None


@dataclass
class DatasetNode:
    """Node representing a dataset."""

    title: str
    year: Optional[int] = None
    citing_papers: List[str] = field(default_factory=list)
    biomarkers_discovered: List[str] = field(default_factory=list)
    research_domains: Set[str] = field(default_factory=set)


class BiomarkerKnowledgeGraph:
    """
    Knowledge graph for biomarker discoveries from dataset usage.

    Connects datasets -> papers -> biomarkers -> diseases/applications.

    Example:
        >>> graph = BiomarkerKnowledgeGraph()
        >>> graph.build_from_analyses(dataset, citation_analyses)
        >>> biomarkers = graph.get_all_biomarkers()
        >>> connections = graph.get_biomarker_connections("GENE1")
    """

    def __init__(self):
        """Initialize empty knowledge graph."""
        self.biomarkers: Dict[str, BiomarkerNode] = {}
        self.papers: Dict[str, PaperNode] = {}
        self.datasets: Dict[str, DatasetNode] = {}

        # Edges (relationships)
        self.dataset_paper_edges: Dict[str, List[str]] = defaultdict(list)
        self.paper_biomarker_edges: Dict[str, List[str]] = defaultdict(list)
        self.biomarker_disease_edges: Dict[str, List[str]] = defaultdict(list)

    def build_from_analyses(
        self,
        dataset: Publication,
        citation_analyses: List[UsageAnalysis],
        citing_papers: Optional[List[Publication]] = None,
    ):
        """
        Build knowledge graph from citation analyses.

        Args:
            dataset: Dataset publication
            citation_analyses: List of citation analyses
            citing_papers: Optional list of citing publications
        """
        logger.info(f"Building knowledge graph for: {dataset.title}")

        # Add dataset node
        dataset_id = dataset.doi or dataset.title
        self.datasets[dataset_id] = DatasetNode(
            title=dataset.title,
            year=dataset.publication_date.year if dataset.publication_date else None,
        )

        # Process each citation
        for i, analysis in enumerate(citation_analyses):
            if not analysis.dataset_reused:
                continue  # Skip papers that didn't reuse dataset

            # Get paper info
            if citing_papers and i < len(citing_papers):
                paper = citing_papers[i]
                paper_year = paper.publication_date.year if paper.publication_date else None
            else:
                paper_year = None

            # Add paper node
            paper_node = PaperNode(
                paper_id=analysis.paper_id,
                title=analysis.paper_title,
                year=paper_year,
                dataset_used=dataset_id,
                biomarkers_discovered=analysis.novel_biomarkers,
                application_domain=analysis.application_domain,
                methodology=analysis.methodology,
            )
            self.papers[analysis.paper_id] = paper_node

            # Add edge: dataset -> paper
            self.dataset_paper_edges[dataset_id].append(analysis.paper_id)
            self.datasets[dataset_id].citing_papers.append(analysis.paper_id)

            if analysis.application_domain:
                self.datasets[dataset_id].research_domains.add(analysis.application_domain)

            # Add biomarker nodes
            for biomarker_name in analysis.novel_biomarkers:
                if biomarker_name not in self.biomarkers:
                    self.biomarkers[biomarker_name] = BiomarkerNode(
                        name=biomarker_name,
                        first_discovery_year=paper_year,
                    )
                else:
                    # Update if earlier discovery
                    if paper_year and (
                        not self.biomarkers[biomarker_name].first_discovery_year
                        or paper_year < self.biomarkers[biomarker_name].first_discovery_year
                    ):
                        self.biomarkers[biomarker_name].first_discovery_year = paper_year

                # Add to biomarker's paper list
                self.biomarkers[biomarker_name].discovered_in_papers.append(analysis.paper_id)
                self.biomarkers[biomarker_name].citation_count += 1

                # Update validation status
                if analysis.validation_status == "validated":
                    self.biomarkers[biomarker_name].validation_status = "validated"

                # Add disease/domain
                if analysis.application_domain:
                    self.biomarkers[biomarker_name].diseases.add(analysis.application_domain)

                # Add edge: paper -> biomarker
                self.paper_biomarker_edges[analysis.paper_id].append(biomarker_name)

                # Add edge: biomarker -> disease
                if analysis.application_domain:
                    self.biomarker_disease_edges[biomarker_name].append(analysis.application_domain)

                # Add to dataset's biomarker list
                if biomarker_name not in self.datasets[dataset_id].biomarkers_discovered:
                    self.datasets[dataset_id].biomarkers_discovered.append(biomarker_name)

        logger.info(
            f"Graph built: {len(self.biomarkers)} biomarkers, "
            f"{len(self.papers)} papers, {len(self.datasets)} datasets"
        )

    def get_all_biomarkers(self) -> List[BiomarkerNode]:
        """Get all biomarker nodes."""
        return list(self.biomarkers.values())

    def get_biomarker(self, name: str) -> Optional[BiomarkerNode]:
        """Get specific biomarker node."""
        return self.biomarkers.get(name)

    def get_biomarker_connections(self, biomarker_name: str) -> Dict:
        """
        Get all connections for a biomarker.

        Args:
            biomarker_name: Biomarker name

        Returns:
            Dictionary with connection information
        """
        if biomarker_name not in self.biomarkers:
            return {}

        biomarker = self.biomarkers[biomarker_name]

        # Get connected papers
        papers = [
            self.papers[paper_id] for paper_id in biomarker.discovered_in_papers if paper_id in self.papers
        ]

        # Get connected datasets (through papers)
        datasets = set()
        for paper in papers:
            if paper.dataset_used:
                datasets.add(paper.dataset_used)

        return {
            "biomarker": biomarker,
            "discovered_in_papers": papers,
            "datasets_used": list(datasets),
            "diseases": list(biomarker.diseases),
            "total_citations": biomarker.citation_count,
            "validation_status": biomarker.validation_status,
        }

    def get_dataset_biomarkers(self, dataset_title: str) -> List[BiomarkerNode]:
        """
        Get all biomarkers discovered using a dataset.

        Args:
            dataset_title: Dataset title or ID

        Returns:
            List of biomarker nodes
        """
        if dataset_title in self.datasets:
            biomarker_names = self.datasets[dataset_title].biomarkers_discovered
            return [self.biomarkers[name] for name in biomarker_names if name in self.biomarkers]
        return []

    def get_biomarkers_by_disease(self, disease: str) -> List[BiomarkerNode]:
        """
        Get biomarkers associated with a disease/domain.

        Args:
            disease: Disease or application domain

        Returns:
            List of biomarker nodes
        """
        return [
            biomarker
            for biomarker in self.biomarkers.values()
            if disease.lower() in [d.lower() for d in biomarker.diseases]
        ]

    def get_validated_biomarkers(self) -> List[BiomarkerNode]:
        """Get all validated biomarkers."""
        return [
            biomarker for biomarker in self.biomarkers.values() if biomarker.validation_status == "validated"
        ]

    def get_biomarker_timeline(self) -> Dict[int, List[str]]:
        """
        Get biomarker discoveries organized by year.

        Returns:
            Dictionary mapping year -> list of biomarker names
        """
        timeline = defaultdict(list)
        for biomarker in self.biomarkers.values():
            if biomarker.first_discovery_year:
                timeline[biomarker.first_discovery_year].append(biomarker.name)
        return dict(timeline)

    def get_statistics(self) -> Dict:
        """
        Get graph statistics.

        Returns:
            Dictionary with graph metrics
        """
        return {
            "total_biomarkers": len(self.biomarkers),
            "total_papers": len(self.papers),
            "total_datasets": len(self.datasets),
            "validated_biomarkers": len(self.get_validated_biomarkers()),
            "diseases_studied": len(self._get_all_diseases()),
            "average_biomarkers_per_paper": (len(self.biomarkers) / len(self.papers) if self.papers else 0),
            "most_cited_biomarker": self._get_most_cited_biomarker(),
        }

    def _get_all_diseases(self) -> Set[str]:
        """Get all unique diseases/domains in graph."""
        diseases = set()
        for biomarker in self.biomarkers.values():
            diseases.update(biomarker.diseases)
        return diseases

    def _get_most_cited_biomarker(self) -> Optional[str]:
        """Get most frequently cited biomarker."""
        if not self.biomarkers:
            return None

        most_cited = max(self.biomarkers.values(), key=lambda b: b.citation_count)
        return most_cited.name

    def export_to_dict(self) -> Dict:
        """
        Export graph to dictionary format.

        Returns:
            Dictionary representation of graph
        """
        return {
            "biomarkers": {
                name: {
                    "name": bm.name,
                    "type": bm.biomarker_type,
                    "papers": bm.discovered_in_papers,
                    "validation": bm.validation_status,
                    "diseases": list(bm.diseases),
                    "first_discovery": bm.first_discovery_year,
                    "citations": bm.citation_count,
                }
                for name, bm in self.biomarkers.items()
            },
            "papers": {
                paper_id: {
                    "id": paper.paper_id,
                    "title": paper.title,
                    "year": paper.year,
                    "dataset": paper.dataset_used,
                    "biomarkers": paper.biomarkers_discovered,
                    "domain": paper.application_domain,
                }
                for paper_id, paper in self.papers.items()
            },
            "datasets": {
                dataset_id: {
                    "title": ds.title,
                    "year": ds.year,
                    "papers": ds.citing_papers,
                    "biomarkers": ds.biomarkers_discovered,
                    "domains": list(ds.research_domains),
                }
                for dataset_id, ds in self.datasets.items()
            },
            "edges": {
                "dataset_paper": dict(self.dataset_paper_edges),
                "paper_biomarker": dict(self.paper_biomarker_edges),
                "biomarker_disease": dict(self.biomarker_disease_edges),
            },
        }

    def generate_summary(self) -> str:
        """
        Generate human-readable summary of knowledge graph.

        Returns:
            Text summary
        """
        stats = self.get_statistics()

        lines = [
            "Biomarker Knowledge Graph Summary",
            "=" * 40,
            f"Total Biomarkers: {stats['total_biomarkers']}",
            f"Validated Biomarkers: {stats['validated_biomarkers']}",
            f"Research Papers: {stats['total_papers']}",
            f"Datasets: {stats['total_datasets']}",
            f"Diseases/Domains: {stats['diseases_studied']}",
            "",
            f"Average biomarkers per paper: {stats['average_biomarkers_per_paper']:.2f}",
        ]

        if stats["most_cited_biomarker"]:
            lines.append(f"Most cited biomarker: {stats['most_cited_biomarker']}")

        # Top validated biomarkers
        validated = self.get_validated_biomarkers()
        if validated:
            lines.append("")
            lines.append("Top Validated Biomarkers:")
            for biomarker in sorted(validated, key=lambda b: b.citation_count, reverse=True)[:5]:
                diseases = ", ".join(list(biomarker.diseases)[:2])
                lines.append(f"  - {biomarker.name} ({biomarker.citation_count} citations, {diseases})")

        return "\n".join(lines)
