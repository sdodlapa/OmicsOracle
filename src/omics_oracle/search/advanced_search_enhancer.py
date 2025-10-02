#!/usr/bin/env python3
"""
OmicsOracle Advanced Search Feature Enhancer

This script implements advanced search features for OmicsOracle,
including semantic ranking, context-aware filtering, and result clustering.
"""

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path


class AdvancedSearchEnhancer:
    """
    Implements advanced search features for OmicsOracle.

    Features include:
    - Semantic result ranking using biomedical context
    - Advanced filtering with context-aware filters
    - Result clustering and categorization
    - Personalized search result ranking
    - Query reformulation suggestions
    """

    def __init__(self):
        """Initialize the advanced search enhancer."""
        # Configurations
        self.config = {
            "enable_semantic_ranking": True,
            "enable_result_clustering": True,
            "enable_query_reformulation": True,
            "enable_personalized_ranking": False,  # Requires user profiles
            "min_similarity_threshold": 0.65,
            "max_clusters": 5,
            "max_reformulations": 3,
        }

    def add_semantic_ranking(self, search_results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Enhance search results with semantic ranking based on biomedical context.

        Args:
            search_results: Original search results
            query: The user's search query

        Returns:
            Enhanced search results with semantic ranking scores
        """
        logger.info(f"Adding semantic ranking for query: {query}")

        # Analyze query for key biomedical concepts
        query_concepts = self._extract_biomedical_concepts(query)

        # Calculate semantic relevance for each result
        for result in search_results:
            # Extract text for semantic matching
            result_text = self._get_result_text(result)

            # Calculate semantic similarity
            similarity_score = self._calculate_semantic_similarity(query_concepts, result_text)

            # Add semantic score to the result
            result["semantic_score"] = similarity_score

        # Re-rank results based on semantic score
        if search_results:
            search_results.sort(key=lambda x: x.get("semantic_score", 0), reverse=True)

        return search_results

    def _extract_biomedical_concepts(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract biomedical concepts from text.

        Args:
            text: The text to analyze

        Returns:
            List of extracted biomedical concepts with metadata
        """
        # This is a placeholder implementation
        # In a real implementation, this would use a biomedical NLP library
        # or service to extract entities and concepts

        concepts = []

        # Simple concept extraction based on keyword matching
        biomedical_keywords = {
            "cancer": {"type": "disease", "importance": 1.0},
            "tumor": {"type": "disease", "importance": 0.9},
            "gene expression": {"type": "data_type", "importance": 0.8},
            "RNA-seq": {"type": "data_type", "importance": 0.9},
            "liver": {"type": "tissue", "importance": 0.7},
            "brain": {"type": "tissue", "importance": 0.7},
            "heart": {"type": "tissue", "importance": 0.7},
            "human": {"type": "organism", "importance": 0.6},
            "mouse": {"type": "organism", "importance": 0.6},
            "pathway": {"type": "analysis", "importance": 0.8},
            "methylation": {"type": "data_type", "importance": 0.9},
            "proteomics": {"type": "data_type", "importance": 0.9},
            "single cell": {"type": "data_type", "importance": 1.0},
        }

        # Find keywords in the text
        text_lower = text.lower()
        for keyword, metadata in biomedical_keywords.items():
            if keyword.lower() in text_lower:
                concepts.append(
                    {
                        "text": keyword,
                        "type": metadata["type"],
                        "importance": metadata["importance"],
                    }
                )

        return concepts

    def _get_result_text(self, result: Dict[str, Any]) -> str:
        """
        Extract text from a search result for semantic analysis.

        Args:
            result: A search result item

        Returns:
            Extracted text for semantic analysis
        """
        text_parts = []

        # Extract various text fields from the result
        # Adjust based on your actual result structure
        if "title" in result:
            text_parts.append(result["title"])

        if "summary" in result:
            text_parts.append(result["summary"])

        if "description" in result:
            text_parts.append(result["description"])

        if "metadata" in result and isinstance(result["metadata"], dict):
            # Extract relevant metadata fields
            metadata = result["metadata"]
            relevant_fields = [
                "organism",
                "tissue",
                "disease",
                "study_type",
                "data_type",
            ]

            for field in relevant_fields:
                if field in metadata and metadata[field]:
                    text_parts.append(str(metadata[field]))

        # Combine all text parts
        return " ".join(text_parts)

    def _calculate_semantic_similarity(self, query_concepts: List[Dict[str, Any]], result_text: str) -> float:
        """
        Calculate semantic similarity between query concepts and result text.

        Args:
            query_concepts: Extracted biomedical concepts from the query
            result_text: Text extracted from the search result

        Returns:
            Semantic similarity score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        # In a real implementation, this would use more sophisticated
        # semantic similarity algorithms, possibly using word embeddings

        if not query_concepts or not result_text:
            return 0.0

        result_text_lower = result_text.lower()

        # Calculate weighted concept matches
        total_importance = sum(concept["importance"] for concept in query_concepts)
        if total_importance == 0:
            return 0.0

        weighted_matches = 0
        for concept in query_concepts:
            if concept["text"].lower() in result_text_lower:
                weighted_matches += concept["importance"]

        # Normalize to 0.0-1.0 range
        similarity = weighted_matches / total_importance

        return similarity

    def cluster_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cluster search results into meaningful categories.

        Args:
            search_results: List of search results

        Returns:
            Dictionary with clustered results
        """
        logger.info(f"Clustering {len(search_results)} search results")

        if not search_results:
            return {"clusters": [], "results": search_results}

        # Extract features for clustering
        result_features = self._extract_clustering_features(search_results)

        # Determine cluster categories
        clusters = self._identify_clusters(result_features)

        # Assign results to clusters
        clustered_results = self._assign_results_to_clusters(search_results, result_features, clusters)

        return clustered_results

    def _extract_clustering_features(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract features for clustering from search results.

        Args:
            results: Search results

        Returns:
            List of feature dictionaries for clustering
        """
        features = []

        for result in results:
            result_features = {}

            # Extract organism, tissue, disease, and data type
            if "metadata" in result and isinstance(result["metadata"], dict):
                metadata = result["metadata"]

                # Extract and normalize key features
                for key in [
                    "organism",
                    "tissue",
                    "disease",
                    "data_type",
                    "study_type",
                ]:
                    if key in metadata and metadata[key]:
                        result_features[key] = str(metadata[key]).lower()

            # Add publication year as a feature if available
            if "year" in result:
                result_features["year"] = result["year"]

            features.append(result_features)

        return features

    def _identify_clusters(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify meaningful clusters from result features.

        Args:
            features: Extracted features for clustering

        Returns:
            List of cluster definitions
        """
        # This is a simplified clustering approach
        # In a real implementation, more sophisticated clustering algorithms would be used

        # Count feature occurrences
        feature_counts = {}

        for feature_dict in features:
            for key, value in feature_dict.items():
                if key not in feature_counts:
                    feature_counts[key] = {}

                if value not in feature_counts[key]:
                    feature_counts[key][value] = 0

                feature_counts[key][value] += 1

        # Identify potential clusters based on frequent feature values
        potential_clusters = []

        for feature_key, value_counts in feature_counts.items():
            # Sort values by frequency
            sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)

            # Consider only frequent values (occurring in at least 10% of results)
            min_count = max(2, len(features) * 0.1)

            for value, count in sorted_values:
                if count >= min_count:
                    potential_clusters.append(
                        {
                            "feature": feature_key,
                            "value": value,
                            "count": count,
                            "label": f"{value.title()} {feature_key.title().replace('_', ' ')}",
                        }
                    )

        # Sort clusters by count and limit to max_clusters
        potential_clusters.sort(key=lambda x: x["count"], reverse=True)
        return potential_clusters[: self.config["max_clusters"]]

    def _assign_results_to_clusters(
        self,
        results: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Assign search results to identified clusters.

        Args:
            results: Original search results
            features: Extracted features for each result
            clusters: Identified clusters

        Returns:
            Dictionary with clustered results
        """
        # Create the clustering result structure
        clustered_results = {
            "clusters": [],
            "results": results,  # Keep original results for backward compatibility
        }

        # Initialize clusters with metadata
        for cluster in clusters:
            clustered_results["clusters"].append(
                {
                    "id": f"{cluster['feature']}_{cluster['value']}",
                    "label": cluster["label"],
                    "feature": cluster["feature"],
                    "value": cluster["value"],
                    "count": 0,
                    "results": [],
                }
            )

        # Assign results to clusters
        for i, (result, feature_dict) in enumerate(zip(results, features)):
            result_assigned = False

            for cluster_idx, cluster in enumerate(clusters):
                feature = cluster["feature"]
                value = cluster["value"]

                if feature in feature_dict and feature_dict[feature] == value:
                    # Add result index to this cluster
                    clustered_results["clusters"][cluster_idx]["results"].append(i)
                    clustered_results["clusters"][cluster_idx]["count"] += 1
                    result_assigned = True

            # Results can belong to multiple clusters

        return clustered_results

    def generate_query_reformulations(self, original_query: str) -> List[Dict[str, Any]]:
        """
        Generate alternative query formulations to suggest to the user.

        Args:
            original_query: The user's original search query

        Returns:
            List of query reformulation suggestions
        """
        logger.info(f"Generating reformulations for query: {original_query}")

        reformulations = []

        # Extract biomedical concepts from the query
        query_concepts = self._extract_biomedical_concepts(original_query)

        # Simple reformulation strategies:

        # 1. Add data type if missing
        if not any(c["type"] == "data_type" for c in query_concepts):
            data_types = [
                "RNA-seq",
                "gene expression",
                "methylation",
                "proteomics",
                "single cell",
            ]
            for data_type in data_types[:2]:  # Limit to avoid too many suggestions
                new_query = f"{original_query} {data_type}"
                reformulations.append(
                    {
                        "query": new_query,
                        "explanation": f"Added data type: {data_type}",
                        "confidence": 0.7,
                    }
                )

        # 2. Add organism if missing
        if not any(c["type"] == "organism" for c in query_concepts):
            new_query = f"human {original_query}"
            reformulations.append(
                {
                    "query": new_query,
                    "explanation": "Specified human organism",
                    "confidence": 0.8,
                }
            )

        # 3. Suggest more specific tissue or disease if general terms are used
        disease_specializations = {
            "cancer": ["breast cancer", "lung cancer", "liver cancer"],
            "tumor": ["brain tumor", "liver tumor", "metastatic tumor"],
        }

        tissue_specializations = {
            "brain": ["hippocampus", "cortex", "cerebellum"],
            "blood": ["PBMC", "T cells", "B cells"],
        }

        for concept in query_concepts:
            if concept["type"] == "disease" and concept["text"] in disease_specializations:
                specializations = disease_specializations[concept["text"]]
                for spec in specializations[:1]:  # Limit to avoid too many suggestions
                    new_query = original_query.replace(concept["text"], spec)
                    reformulations.append(
                        {
                            "query": new_query,
                            "explanation": f"Specified {spec} instead of general {concept['text']}",
                            "confidence": 0.75,
                        }
                    )

            elif concept["type"] == "tissue" and concept["text"] in tissue_specializations:
                specializations = tissue_specializations[concept["text"]]
                for spec in specializations[:1]:  # Limit to avoid too many suggestions
                    new_query = original_query.replace(concept["text"], spec)
                    reformulations.append(
                        {
                            "query": new_query,
                            "explanation": f"Specified {spec} instead of general {concept['text']}",
                            "confidence": 0.7,
                        }
                    )

        # Limit the number of suggestions
        reformulations.sort(key=lambda x: x["confidence"], reverse=True)
        return reformulations[: self.config["max_reformulations"]]

    def enhance_search_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        apply_semantic_ranking: bool = True,
        apply_clustering: bool = True,
        generate_reformulations: bool = True,
    ) -> Dict[str, Any]:
        """
        Apply all advanced search enhancements to results.

        Args:
            results: Original search results
            query: The user's search query
            apply_semantic_ranking: Whether to apply semantic ranking
            apply_clustering: Whether to apply result clustering
            generate_reformulations: Whether to generate query reformulations

        Returns:
            Enhanced search results with all applied features
        """
        enhanced_results = {
            "query": query,
            "results": results,
            "enhancements": [],
        }

        # Apply semantic ranking if enabled
        if apply_semantic_ranking and self.config["enable_semantic_ranking"]:
            enhanced_results["results"] = self.add_semantic_ranking(results, query)
            enhanced_results["enhancements"].append("semantic_ranking")

        # Apply clustering if enabled
        if apply_clustering and self.config["enable_result_clustering"] and len(results) >= 3:
            clustering = self.cluster_results(enhanced_results["results"])
            enhanced_results["clusters"] = clustering["clusters"]
            enhanced_results["enhancements"].append("clustering")

        # Generate query reformulations if enabled
        if generate_reformulations and self.config["enable_query_reformulation"]:
            reformulations = self.generate_query_reformulations(query)
            if reformulations:
                enhanced_results["query_reformulations"] = reformulations
                enhanced_results["enhancements"].append("query_reformulations")

        return enhanced_results

    def validate_feature_integration(self) -> Dict[str, bool]:
        """
        Validate that the advanced search features are correctly integrated.

        Returns:
            Dictionary of validation results for each feature
        """
        logger.info("Validating advanced search feature integration")

        validation_results = {
            "semantic_ranking": False,
            "result_clustering": False,
            "query_reformulation": False,
        }

        # Test data
        test_query = "human liver cancer RNA-seq"
        test_results = [
            {
                "id": "GEO123",
                "title": "RNA-seq of liver cancer in human patients",
                "metadata": {
                    "organism": "human",
                    "tissue": "liver",
                    "disease": "cancer",
                    "data_type": "RNA-seq",
                },
            },
            {
                "id": "GEO456",
                "title": "Expression profiling of hepatocellular carcinoma",
                "metadata": {
                    "organism": "human",
                    "tissue": "liver",
                    "disease": "hepatocellular carcinoma",
                    "data_type": "microarray",
                },
            },
        ]

        # Validate semantic ranking
        try:
            ranked_results = self.add_semantic_ranking(test_results.copy(), test_query)
            if len(ranked_results) == len(test_results) and "semantic_score" in ranked_results[0]:
                validation_results["semantic_ranking"] = True
        except Exception as e:
            logger.error(f"Semantic ranking validation failed: {str(e)}")

        # Validate clustering
        try:
            clustered_results = self.cluster_results(test_results.copy())
            if "clusters" in clustered_results:
                validation_results["result_clustering"] = True
        except Exception as e:
            logger.error(f"Result clustering validation failed: {str(e)}")

        # Validate query reformulation
        try:
            reformulations = self.generate_query_reformulations(test_query)
            if isinstance(reformulations, list) and len(reformulations) > 0:
                validation_results["query_reformulation"] = True
        except Exception as e:
            logger.error(f"Query reformulation validation failed: {str(e)}")

        # Log validation results
        for feature, result in validation_results.items():
            status = "✅ Passed" if result else "❌ Failed"
            logger.info(f"Validation of {feature}: {status}")

        return validation_results


def save_integration_example(enhancer: AdvancedSearchEnhancer) -> None:
    """
    Save an example of how to integrate the advanced search features.

    Args:
        enhancer: The AdvancedSearchEnhancer instance
    """
    example_code = """
# Example integration with OmicsOracle search API

from src.omics_oracle.search.advanced_search_enhancer import AdvancedSearchEnhancer

class EnhancedSearchService:
    def __init__(self):
        self.search_enhancer = AdvancedSearchEnhancer()

    async def search(self, query, options=None):
        # Call the base search implementation to get initial results
        base_results = await self._base_search(query, options)

        # Apply advanced search enhancements
        enhanced_results = self.search_enhancer.enhance_search_results(
            results=base_results["results"],
            query=query,
            apply_semantic_ranking=options.get("semantic_ranking", True),
            apply_clustering=options.get("clustering", True),
            generate_reformulations=options.get("suggest_queries", True)
        )

        return enhanced_results

    async def _base_search(self, query, options):
        # Implement your base search functionality here
        # This is a placeholder implementation
        pass

# API endpoint integration example
@app.route("/api/v1/enhanced-search")
async def enhanced_search(request):
    query = request.args.get("q")
    options = {
        "semantic_ranking": request.args.get("semantic_ranking", "true").lower() == "true",
        "clustering": request.args.get("clustering", "true").lower() == "true",
        "suggest_queries": request.args.get("suggest_queries", "true").lower() == "true"
    }

    search_service = EnhancedSearchService()
    results = await search_service.search(query, options)

    return jsonify(results)
"""

    # Save the example code
    example_path = Path("search_enhancer_integration_example.py")
    with open(example_path, "w") as f:
        f.write(example_code.strip())

    logger.info(f"Saved integration example to {example_path}")


def main():
    """Main function to validate and demonstrate the search enhancer."""
    parser = argparse.ArgumentParser(description="OmicsOracle Advanced Search Feature Enhancer")
    parser.add_argument("--validate", action="store_true", help="Validate feature integration")
    parser.add_argument(
        "--save-example",
        action="store_true",
        help="Save integration example code",
    )

    args = parser.parse_args()

    enhancer = AdvancedSearchEnhancer()

    if args.validate:
        enhancer.validate_feature_integration()

    if args.save_example:
        save_integration_example(enhancer)

    # If no specific action is requested, do validation by default
    if not (args.validate or args.save_example):
        enhancer.validate_feature_integration()
        save_integration_example(enhancer)

    print("\n✅ Advanced Search Enhancer Operations Complete")


if __name__ == "__main__":
    main()
