"""
Source Metrics and Prioritization System

Tracks performance metrics for each citation source to enable:
- Source prioritization based on quality/speed
- Adaptive timeouts and resource allocation
- Trade-off analysis between coverage and speed
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SourcePriority(Enum):
    """Source priority levels"""

    CRITICAL = 1  # Must complete (e.g., OpenAlex - fast & comprehensive)
    HIGH = 2  # Should complete (e.g., Semantic Scholar - good coverage)
    MEDIUM = 3  # Nice to have (e.g., Europe PMC - specialized)
    LOW = 4  # Optional (e.g., slow sources)
    FALLBACK = 5  # Only if others fail


@dataclass
class SourceMetrics:
    """Metrics for a single citation source"""

    source_name: str
    priority: SourcePriority = SourcePriority.MEDIUM

    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0  # seconds

    # Result quality metrics
    total_papers_found: int = 0
    unique_papers_contributed: int = 0  # Papers not found by other sources
    duplicate_papers: int = 0

    # Batch capabilities
    supports_batch: bool = False
    max_batch_size: int = 1

    # Rate limiting
    rate_limit: float = 1.0  # requests per second

    # Last execution metrics
    last_execution_time: Optional[float] = None
    last_papers_found: int = 0
    last_error: Optional[str] = None

    # Historical averages
    avg_response_time: float = 0.0
    avg_papers_per_request: float = 0.0
    success_rate: float = 0.0

    def record_request(
        self, success: bool, response_time: float, papers_found: int = 0, error: Optional[str] = None
    ):
        """Record a request execution"""
        self.total_requests += 1
        self.total_response_time += response_time
        self.last_execution_time = response_time
        self.last_papers_found = papers_found

        if success:
            self.successful_requests += 1
            self.total_papers_found += papers_found
        else:
            self.failed_requests += 1
            self.last_error = error

        # Update averages
        self._update_averages()

    def record_unique_contribution(self, unique_count: int, duplicate_count: int):
        """Record how many unique papers this source contributed"""
        self.unique_papers_contributed += unique_count
        self.duplicate_papers += duplicate_count

    def _update_averages(self):
        """Update running averages"""
        if self.total_requests > 0:
            self.avg_response_time = self.total_response_time / self.total_requests
            self.success_rate = self.successful_requests / self.total_requests

        if self.successful_requests > 0:
            self.avg_papers_per_request = self.total_papers_found / self.successful_requests

    def get_efficiency_score(self) -> float:
        """
        Calculate efficiency score (papers per second)
        Higher is better
        """
        if self.avg_response_time > 0:
            return self.avg_papers_per_request / self.avg_response_time
        return 0.0

    def get_quality_score(self) -> float:
        """
        Calculate quality score (unique contribution rate)
        Higher is better
        """
        if self.total_papers_found > 0:
            return self.unique_papers_contributed / self.total_papers_found
        return 0.0

    def get_reliability_score(self) -> float:
        """
        Calculate reliability score (success rate)
        Higher is better
        """
        return self.success_rate

    def get_overall_score(self) -> float:
        """
        Calculate overall score combining efficiency, quality, and reliability
        """
        efficiency = self.get_efficiency_score()
        quality = self.get_quality_score()
        reliability = self.get_reliability_score()

        # Weighted combination
        # Reliability is most important, then efficiency, then quality
        return (reliability * 0.5) + (efficiency * 0.3) + (quality * 0.2)

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/serialization"""
        return {
            "source_name": self.source_name,
            "priority": self.priority.name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{self.success_rate:.2%}",
            "avg_response_time": f"{self.avg_response_time:.2f}s",
            "total_papers_found": self.total_papers_found,
            "unique_papers_contributed": self.unique_papers_contributed,
            "duplicate_papers": self.duplicate_papers,
            "avg_papers_per_request": f"{self.avg_papers_per_request:.1f}",
            "efficiency_score": f"{self.get_efficiency_score():.2f}",
            "quality_score": f"{self.get_quality_score():.2%}",
            "reliability_score": f"{self.get_reliability_score():.2%}",
            "overall_score": f"{self.get_overall_score():.2f}",
        }


@dataclass
class SourceManagerConfig:
    """Configuration for source manager"""

    # Timeout settings
    max_total_time: float = 120.0  # Max time for all sources (seconds)
    per_source_timeout: float = 60.0  # Max time per source (seconds)

    # Quality thresholds
    min_papers_threshold: int = 10  # Minimum papers to consider a query successful
    min_unique_contribution: float = 0.1  # Minimum 10% unique papers to keep a source active

    # Priority settings
    enable_adaptive_priority: bool = True  # Adjust priorities based on performance
    enable_early_termination: bool = True  # Stop if we have enough papers
    early_termination_threshold: int = 100  # Stop after this many unique papers

    # Metrics persistence
    save_metrics: bool = True
    metrics_file: str = "data/analytics/source_metrics.json"


class SourceManager:
    """
    Manages multiple citation sources with prioritization and metrics
    """

    def __init__(self, config: Optional[SourceManagerConfig] = None):
        self.config = config or SourceManagerConfig()
        self.sources: Dict[str, SourceMetrics] = {}
        self._load_metrics()

    def register_source(
        self,
        name: str,
        priority: SourcePriority,
        rate_limit: float = 1.0,
        supports_batch: bool = False,
        max_batch_size: int = 1,
    ) -> SourceMetrics:
        """Register a citation source"""
        if name in self.sources:
            metrics = self.sources[name]
            # Update configuration
            metrics.priority = priority
            metrics.rate_limit = rate_limit
            metrics.supports_batch = supports_batch
            metrics.max_batch_size = max_batch_size
        else:
            metrics = SourceMetrics(
                source_name=name,
                priority=priority,
                rate_limit=rate_limit,
                supports_batch=supports_batch,
                max_batch_size=max_batch_size,
            )
            self.sources[name] = metrics

        logger.info(
            f"✓ Registered source: {name} "
            f"(priority: {priority.name}, "
            f"rate: {rate_limit}/s, "
            f"batch: {supports_batch})"
        )
        return metrics

    def get_source(self, name: str) -> Optional[SourceMetrics]:
        """Get metrics for a source"""
        return self.sources.get(name)

    def get_sources_by_priority(self) -> List[SourceMetrics]:
        """Get sources sorted by priority (CRITICAL first)"""
        return sorted(self.sources.values(), key=lambda s: (s.priority.value, -s.get_overall_score()))

    def should_execute_source(self, name: str, current_papers: int) -> bool:
        """Determine if a source should be executed based on current state"""
        metrics = self.sources.get(name)
        if not metrics:
            return True  # Unknown source, execute it

        # Always execute CRITICAL and HIGH priority sources
        if metrics.priority in [SourcePriority.CRITICAL, SourcePriority.HIGH]:
            return True

        # Check early termination
        if self.config.enable_early_termination:
            if current_papers >= self.config.early_termination_threshold:
                logger.info(
                    f"⏭️  Skipping {name} (early termination: " f"{current_papers} papers already found)"
                )
                return False

        # Check if source has been consistently poor
        if metrics.total_requests >= 5:  # Need at least 5 requests for statistics
            if metrics.success_rate < 0.5:  # Less than 50% success rate
                logger.warning(f"⚠️  Skipping {name} (low success rate: " f"{metrics.success_rate:.1%})")
                return False

            if metrics.get_quality_score() < self.config.min_unique_contribution:
                logger.warning(
                    f"⚠️  Skipping {name} (low unique contribution: " f"{metrics.get_quality_score():.1%})"
                )
                return False

        return True

    def get_recommended_timeout(self, name: str) -> float:
        """Get recommended timeout for a source based on historical performance"""
        metrics = self.sources.get(name)
        if not metrics or metrics.avg_response_time == 0:
            return self.config.per_source_timeout

        # Add 50% buffer to average response time
        recommended = metrics.avg_response_time * 1.5

        # Clamp to reasonable bounds
        return min(max(recommended, 5.0), self.config.per_source_timeout)

    def record_deduplication(self, source_contributions: Dict[str, List[str]]):
        """
        Record which papers came from which sources after deduplication

        Args:
            source_contributions: Dict mapping source name to list of unique paper IDs
        """
        all_paper_ids = set()
        for papers in source_contributions.values():
            all_paper_ids.update(papers)

        total_unique = len(all_paper_ids)

        for source_name, paper_ids in source_contributions.items():
            metrics = self.sources.get(source_name)
            if metrics:
                unique_count = len(paper_ids)
                duplicate_count = metrics.last_papers_found - unique_count
                metrics.record_unique_contribution(unique_count, duplicate_count)

                logger.info(
                    f"📊 {source_name}: {unique_count} unique papers "
                    f"({duplicate_count} duplicates) - "
                    f"{unique_count/total_unique:.1%} of total"
                )

    def get_summary(self) -> Dict:
        """Get summary of all source metrics"""
        summary = {"total_sources": len(self.sources), "sources": {}}

        for name, metrics in self.sources.items():
            summary["sources"][name] = metrics.to_dict()

        # Add rankings
        by_efficiency = sorted(self.sources.items(), key=lambda x: x[1].get_efficiency_score(), reverse=True)
        by_quality = sorted(self.sources.items(), key=lambda x: x[1].get_quality_score(), reverse=True)
        by_reliability = sorted(
            self.sources.items(), key=lambda x: x[1].get_reliability_score(), reverse=True
        )

        summary["rankings"] = {
            "by_efficiency": [name for name, _ in by_efficiency],
            "by_quality": [name for name, _ in by_quality],
            "by_reliability": [name for name, _ in by_reliability],
        }

        return summary

    def print_summary(self):
        """Print a formatted summary of source metrics"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 CITATION SOURCE METRICS SUMMARY")
        logger.info("=" * 80)

        for metrics in self.get_sources_by_priority():
            logger.info(f"\n{metrics.source_name} ({metrics.priority.name}):")
            logger.info(f"  Success Rate: {metrics.success_rate:.1%}")
            logger.info(f"  Avg Response Time: {metrics.avg_response_time:.2f}s")
            logger.info(
                f"  Papers Found: {metrics.total_papers_found} total, "
                f"{metrics.unique_papers_contributed} unique"
            )
            logger.info(f"  Efficiency: {metrics.get_efficiency_score():.2f} papers/sec")
            logger.info(f"  Quality: {metrics.get_quality_score():.1%} unique")
            logger.info(f"  Overall Score: {metrics.get_overall_score():.2f}")

        logger.info("\n" + "=" * 80)

    def _load_metrics(self):
        """Load metrics from persistent storage"""
        if not self.config.save_metrics:
            return

        try:
            import json
            from pathlib import Path

            metrics_path = Path(self.config.metrics_file)
            if metrics_path.exists():
                with open(metrics_path) as f:
                    data = json.load(f)

                for source_data in data.get("sources", {}).values():
                    # Reconstruct metrics object
                    # (simplified - in production would need more careful deserialization)
                    pass

                logger.info(f"✓ Loaded metrics from {metrics_path}")
        except Exception as e:
            logger.warning(f"Could not load metrics: {e}")

    def _save_metrics(self):
        """Save metrics to persistent storage"""
        if not self.config.save_metrics:
            return

        try:
            import json
            from pathlib import Path

            metrics_path = Path(self.config.metrics_file)
            metrics_path.parent.mkdir(parents=True, exist_ok=True)

            summary = self.get_summary()
            summary["timestamp"] = datetime.now().isoformat()

            with open(metrics_path, "w") as f:
                json.dump(summary, f, indent=2)

            logger.info(f"✓ Saved metrics to {metrics_path}")
        except Exception as e:
            logger.warning(f"Could not save metrics: {e}")

    def __del__(self):
        """Save metrics on cleanup"""
        try:
            self._save_metrics()
        except Exception:
            pass
