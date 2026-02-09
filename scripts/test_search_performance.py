#!/usr/bin/env python3
"""
PharmaKG Search Performance Testing Script
测试和优化搜索功能的性能

This script tests:
1. Full-text search performance
2. Fuzzy search with typos
3. Search suggestions
4. Aggregation search
5. Concurrent request handling
6. Large result set performance
"""

import asyncio
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import requests
    from api.services.search_service import SearchService
    from api.database import get_db
    from api.config import settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root with the conda environment activated")
    sys.exit(1)


@dataclass
class TestResult:
    """存储单个测试结果"""
    test_name: str
    duration_ms: float
    success: bool
    result_count: int = 0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """性能指标汇总"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    avg_result_count: float
    details: List[TestResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "min_response_time_ms": round(self.min_response_time_ms, 2),
            "max_response_time_ms": round(self.max_response_time_ms, 2),
            "p50_response_time_ms": round(self.p50_response_time_ms, 2),
            "p95_response_time_ms": round(self.p95_response_time_ms, 2),
            "p99_response_time_ms": round(self.p99_response_time_ms, 2),
            "requests_per_second": round(self.requests_per_second, 2),
            "avg_result_count": round(self.avg_result_count, 2),
        }


class SearchPerformanceTester:
    """搜索性能测试器"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.service: Optional[SearchService] = None
        self.results: List[PerformanceMetrics] = []
        self.start_time: Optional[datetime] = None

    def setup(self):
        """初始化测试环境"""
        print("Setting up test environment...")
        try:
            self.service = SearchService()
            db = get_db()

            # 检查全文索引
            indexes = self.service.list_fulltext_indexes()
            print(f"Found {len(indexes)} full-text indexes")
            for idx in indexes:
                print(f"  - {idx.get('name')}: {idx.get('labelsOrTypes')}")

            # 检查API连接
            try:
                response = requests.get(f"{self.api_base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("API connection successful")
                else:
                    print(f"API health check returned status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not connect to API at {self.api_base_url}: {e}")
                print("Will continue with direct service testing")

            self.start_time = datetime.now()
            print("Setup complete\n")

        except Exception as e:
            print(f"Setup failed: {e}")
            raise

    def test_fulltext_search(self) -> PerformanceMetrics:
        """测试全文搜索性能"""
        print("\n" + "=" * 60)
        print("Testing Full-Text Search Performance")
        print("=" * 60)

        test_queries = [
            "aspirin",
            "cancer",
            "diabetes",
            "protein kinase",
            "clinical trial",
            "COVID-19",
            "manufacturer",
            "pathway",
            "adverse event",
            "regulatory submission",
        ]

        results = []

        for query in test_queries:
            start = time.time()
            try:
                result = self.service.fulltext_search(query_text=query, limit=20)
                duration = (time.time() - start) * 1000

                results.append(TestResult(
                    test_name=f"fulltext_search_{query}",
                    duration_ms=duration,
                    success=True,
                    result_count=len(result.get("results", [])),
                    metadata={"query": query}
                ))

                print(f"✓ '{query}': {duration:.2f}ms ({len(result.get('results', []))} results)")

            except Exception as e:
                duration = (time.time() - start) * 1000
                results.append(TestResult(
                    test_name=f"fulltext_search_{query}",
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                ))
                print(f"✗ '{query}': FAILED - {e}")

        return self._calculate_metrics("Full-Text Search", results)

    def test_fuzzy_search(self) -> PerformanceMetrics:
        """测试模糊搜索性能"""
        print("\n" + "=" * 60)
        print("Testing Fuzzy Search Performance (with typos)")
        print("=" * 60)

        test_cases = [
            ("asprin", "Compound", "name"),  # aspirin typo
            ("diabete", "Compound", "name"),  # diabetes typo
            ("protien", "Target", "name"),   # protein typo
            ("kinase", "Target", "name"),    # partial match
            ("clincal", "ClinicalTrial", "title"),  # clinical typo
        ]

        results = []

        for query, entity_type, field in test_cases:
            start = time.time()
            try:
                result = self.service.fuzzy_search(
                    query_text=query,
                    entity_type=entity_type,
                    search_field=field,
                    max_distance=2,
                    limit=10
                )
                duration = (time.time() - start) * 1000

                results.append(TestResult(
                    test_name=f"fuzzy_search_{query}",
                    duration_ms=duration,
                    success=True,
                    result_count=len(result.get("results", [])),
                    metadata={"query": query, "entity_type": entity_type}
                ))

                method = result.get("method", "UNKNOWN")
                print(f"✓ '{query}' ({entity_type}): {duration:.2f}ms ({len(result.get('results', []))} results, {method})")

            except Exception as e:
                duration = (time.time() - start) * 1000
                results.append(TestResult(
                    test_name=f"fuzzy_search_{query}",
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                ))
                print(f"✗ '{query}': FAILED - {e}")

        return self._calculate_metrics("Fuzzy Search", results)

    def test_suggestions(self) -> PerformanceMetrics:
        """测试搜索建议性能"""
        print("\n" + "=" * 60)
        print("Testing Search Suggestions Performance")
        print("=" * 60)

        test_cases = [
            ("a", "Compound"),
            ("as", "Compound"),
            ("asp", "Compound"),
            ("c", "ClinicalTrial"),
            ("p", "Pathway"),
            ("t", "Target"),
        ]

        results = []

        for prefix, entity_type in test_cases:
            start = time.time()
            try:
                result = self.service.get_suggestions(
                    prefix=prefix,
                    entity_type=entity_type,
                    limit=10
                )
                duration = (time.time() - start) * 1000

                results.append(TestResult(
                    test_name=f"suggestions_{prefix}_{entity_type}",
                    duration_ms=duration,
                    success=True,
                    result_count=len(result.get("suggestions", [])),
                    metadata={"prefix": prefix, "entity_type": entity_type}
                ))

                print(f"✓ '{prefix}' ({entity_type}): {duration:.2f}ms ({len(result.get('suggestions', []))} suggestions)")

            except Exception as e:
                duration = (time.time() - start) * 1000
                results.append(TestResult(
                    test_name=f"suggestions_{prefix}_{entity_type}",
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                ))
                print(f"✗ '{prefix}': FAILED - {e}")

        return self._calculate_metrics("Search Suggestions", results)

    def test_aggregation_search(self) -> PerformanceMetrics:
        """测试聚合搜索性能"""
        print("\n" + "=" * 60)
        print("Testing Aggregation Search Performance")
        print("=" * 60)

        test_queries = ["cancer", "drug", "protein", "trial"]

        results = []

        for query in test_queries:
            # Test by entity type
            start = time.time()
            try:
                result = self.service.aggregate_search(
                    query_text=query,
                    group_by="entity_type",
                    limit=50
                )
                duration = (time.time() - start) * 1000

                group_count = len(result.get("groups", []))
                results.append(TestResult(
                    test_name=f"aggregate_by_entity_{query}",
                    duration_ms=duration,
                    success=True,
                    result_count=group_count,
                    metadata={"query": query, "group_by": "entity_type"}
                ))

                print(f"✓ '{query}' (by entity_type): {duration:.2f}ms ({group_count} groups)")

            except Exception as e:
                duration = (time.time() - start) * 1000
                results.append(TestResult(
                    test_name=f"aggregate_by_entity_{query}",
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                ))
                print(f"✗ '{query}' (by entity_type): FAILED - {e}")

            # Test by domain
            start = time.time()
            try:
                result = self.service.aggregate_search(
                    query_text=query,
                    group_by="domain",
                    limit=50
                )
                duration = (time.time() - start) * 1000

                group_count = len(result.get("groups", []))
                results.append(TestResult(
                    test_name=f"aggregate_by_domain_{query}",
                    duration_ms=duration,
                    success=True,
                    result_count=group_count,
                    metadata={"query": query, "group_by": "domain"}
                ))

                print(f"✓ '{query}' (by domain): {duration:.2f}ms ({group_count} groups)")

            except Exception as e:
                duration = (time.time() - start) * 1000
                results.append(TestResult(
                    test_name=f"aggregate_by_domain_{query}",
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                ))
                print(f"✗ '{query}' (by domain): FAILED - {e}")

        return self._calculate_metrics("Aggregation Search", results)

    def test_concurrent_requests(self, num_concurrent: int = 10) -> PerformanceMetrics:
        """测试并发请求性能"""
        print("\n" + "=" * 60)
        print(f"Testing Concurrent Requests ({num_concurrent} simultaneous)")
        print("=" * 60)

        query = "cancer"
        results = []

        def make_request(request_id: int) -> TestResult:
            start = time.time()
            try:
                result = self.service.fulltext_search(query_text=query, limit=20)
                duration = (time.time() - start) * 1000

                return TestResult(
                    test_name=f"concurrent_request_{request_id}",
                    duration_ms=duration,
                    success=True,
                    result_count=len(result.get("results", [])),
                    metadata={"request_id": request_id}
                )

            except Exception as e:
                duration = (time.time() - start) * 1000
                return TestResult(
                    test_name=f"concurrent_request_{request_id}",
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                )

        start_total = time.time()

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = {executor.submit(make_request, i): i for i in range(num_concurrent)}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                status = "✓" if result.success else "✗"
                print(f"{status} Request {result.metadata['request_id']}: {result.duration_ms:.2f}ms")

        total_duration = time.time() - start_total

        metrics = self._calculate_metrics(f"Concurrent Requests ({num_concurrent})", results)
        metrics.requests_per_second = num_concurrent / total_duration

        print(f"\nTotal time: {total_duration:.2f}s")
        print(f"Throughput: {metrics.requests_per_second:.2f} requests/second")

        return metrics

    def test_large_result_sets(self) -> PerformanceMetrics:
        """测试大数据集性能"""
        print("\n" + "=" * 60)
        print("Testing Large Result Sets")
        print("=" * 60)

        limits = [50, 100, 200, 500]
        query = "protein"  # 常见词应该返回较多结果

        results = []

        for limit in limits:
            start = time.time()
            try:
                result = self.service.fulltext_search(query_text=query, limit=limit)
                duration = (time.time() - start) * 1000

                result_count = len(result.get("results", []))
                results.append(TestResult(
                    test_name=f"large_results_{limit}",
                    duration_ms=duration,
                    success=True,
                    result_count=result_count,
                    metadata={"limit": limit, "actual_count": result_count}
                ))

                print(f"✓ Limit={limit}: {duration:.2f}ms ({result_count} results)")

            except Exception as e:
                duration = (time.time() - start) * 1000
                results.append(TestResult(
                    test_name=f"large_results_{limit}",
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                ))
                print(f"✗ Limit={limit}: FAILED - {e}")

        return self._calculate_metrics("Large Result Sets", results)

    def test_api_endpoints(self) -> PerformanceMetrics:
        """测试API端点性能"""
        print("\n" + "=" * 60)
        print("Testing API Endpoints Performance")
        print("=" * 60)

        endpoints = [
            ("POST", "/api/v1/search/fulltext", {"query": "aspirin", "limit": 10}),
            ("GET", "/health", {}),
        ]

        results = []

        for method, endpoint, data in endpoints:
            start = time.time()
            try:
                if method == "POST":
                    response = requests.post(
                        f"{self.api_base_url}{endpoint}",
                        json=data,
                        timeout=10
                    )
                else:
                    response = requests.get(
                        f"{self.api_base_url}{endpoint}",
                        timeout=10
                    )

                duration = (time.time() - start) * 1000

                success = response.status_code == 200
                results.append(TestResult(
                    test_name=f"api_{method}_{endpoint.replace('/', '_')}",
                    duration_ms=duration,
                    success=success,
                    result_count=1 if success else 0,
                    error_message=f"Status {response.status_code}" if not success else "",
                    metadata={"endpoint": endpoint, "method": method, "status": response.status_code}
                ))

                status = "✓" if success else "✗"
                print(f"{status} {method} {endpoint}: {duration:.2f}ms (Status: {response.status_code})")

            except requests.exceptions.RequestException as e:
                duration = (time.time() - start) * 1000
                results.append(TestResult(
                    test_name=f"api_{method}_{endpoint.replace('/', '_')}",
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                ))
                print(f"✗ {method} {endpoint}: FAILED - {e}")

        return self._calculate_metrics("API Endpoints", results)

    def _calculate_metrics(self, test_name: str, results: List[TestResult]) -> PerformanceMetrics:
        """计算性能指标"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if not successful:
            return PerformanceMetrics(
                test_name=test_name,
                total_requests=len(results),
                successful_requests=0,
                failed_requests=len(failed),
                avg_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                p50_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                requests_per_second=0,
                avg_result_count=0,
                details=results
            )

        durations = [r.duration_ms for r in successful]
        result_counts = [r.result_count for r in successful]

        durations.sort()

        def percentile(data: List[float], p: float) -> float:
            """计算百分位数"""
            k = (len(data) - 1) * p
            f = int(k)
            c = f + 1 if c < len(data) else f
            if f == c:
                return data[f]
            d = k - f
            return data[f] * (1 - d) + data[c] * d

        return PerformanceMetrics(
            test_name=test_name,
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            avg_response_time_ms=statistics.mean(durations),
            min_response_time_ms=min(durations),
            max_response_time_ms=max(durations),
            p50_response_time_ms=percentile(durations, 0.50),
            p95_response_time_ms=percentile(durations, 0.95),
            p99_response_time_ms=percentile(durations, 0.99),
            requests_per_second=0,  # Will be calculated for concurrent tests
            avg_result_count=statistics.mean(result_counts) if result_counts else 0,
            details=results
        )

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("PharmaKG Search Performance Testing")
        print("=" * 60)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API URL: {self.api_base_url}")
        print(f"Neo4j URI: {settings.NEO4J_URI}")

        try:
            # Run all test suites
            self.results.append(self.test_fulltext_search())
            self.results.append(self.test_fuzzy_search())
            self.results.append(self.test_suggestions())
            self.results.append(self.test_aggregation_search())
            self.results.append(self.test_concurrent_requests(num_concurrent=10))
            self.results.append(self.test_large_result_sets())
            self.results.append(self.test_api_endpoints())

        except Exception as e:
            print(f"\nTest suite failed: {e}")
            import traceback
            traceback.print_exc()

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print("\n" + "=" * 60)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 60)

        # Check against success criteria
        criteria = {
            "search_response_time_p95": 500,  # ms
            "api_availability": 99,  # %
        }

        passed = []
        failed = []

        for metrics in self.results:
            print(f"\n{metrics.test_name}:")
            print(f"  Total requests: {metrics.total_requests}")
            print(f"  Successful: {metrics.successful_requests}")
            print(f"  Failed: {metrics.failed_requests}")
            print(f"  Avg response time: {metrics.avg_response_time_ms:.2f}ms")
            print(f"  Min response time: {metrics.min_response_time_ms:.2f}ms")
            print(f"  Max response time: {metrics.max_response_time_ms:.2f}ms")
            print(f"  P50 response time: {metrics.p50_response_time_ms:.2f}ms")
            print(f"  P95 response time: {metrics.p95_response_time_ms:.2f}ms")
            print(f"  P99 response time: {metrics.p99_response_time_ms:.2f}ms")

            if metrics.requests_per_second > 0:
                print(f"  Throughput: {metrics.requests_per_second:.2f} req/s")

            # Check criteria
            if metrics.p95_response_time_ms > 0 and metrics.p95_response_time_ms <= criteria["search_response_time_p95"]:
                passed.append(f"{metrics.test_name} - P95 response time")
            elif metrics.p95_response_time_ms > 0:
                failed.append(f"{metrics.test_name} - P95 response time ({metrics.p95_response_time_ms:.2f}ms > {criteria['search_response_time_p95']}ms)")

        print("\n" + "=" * 60)
        print("SUCCESS CRITERIA CHECK")
        print("=" * 60)

        if passed:
            print("\n✓ Passed:")
            for item in passed:
                print(f"  - {item}")

        if failed:
            print("\n✗ Failed:")
            for item in failed:
                print(f"  - {item}")

        # Calculate overall metrics
        total_requests = sum(m.total_requests for m in self.results)
        total_successful = sum(m.successful_requests for m in self.results)
        total_failed = sum(m.failed_requests for m in self.results)
        success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0

        print(f"\nOverall success rate: {success_rate:.2f}%")
        print(f"Total test duration: {duration:.2f}s")

        # Prepare report data
        report = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "api_base_url": self.api_base_url,
                "neo4j_uri": settings.NEO4J_URI,
            },
            "success_criteria": {
                "search_response_time_p95_ms": criteria["search_response_time_p95"],
                "api_availability_percent": criteria["api_availability"],
            },
            "overall_results": {
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "success_rate_percent": round(success_rate, 2),
            },
            "test_suites": [m.to_dict() for m in self.results],
            "passed_criteria": passed,
            "failed_criteria": failed,
        }

        # Save report to file
        report_path = project_root / "docs" / "SEARCH_PERFORMANCE_REPORT.md"
        self._save_markdown_report(report, report_path)

        json_report_path = project_root / "docs" / "SEARCH_PERFORMANCE_REPORT.json"
        with open(json_report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nReports saved:")
        print(f"  - {report_path}")
        print(f"  - {json_report_path}")

        return report

    def _save_markdown_report(self, report: Dict[str, Any], path: Path):
        """保存Markdown格式的报告"""
        with open(path, 'w') as f:
            f.write("# PharmaKG Search Performance Report\n\n")
            f.write(f"**Generated**: {report['test_run']['end_time']}\n")
            f.write(f"**Duration**: {report['test_run']['duration_seconds']:.2f}s\n\n")

            f.write("## Test Configuration\n\n")
            f.write(f"- **API URL**: {report['test_run']['api_base_url']}\n")
            f.write(f"- **Neo4j URI**: {report['test_run']['neo4j_uri']}\n\n")

            f.write("## Success Criteria\n\n")
            f.write(f"- **P95 Response Time**: < {report['success_criteria']['search_response_time_p95_ms']}ms\n")
            f.write(f"- **API Availability**: > {report['success_criteria']['api_availability_percent']}%\n\n")

            f.write("## Overall Results\n\n")
            f.write(f"| Metric | Value |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Total Requests | {report['overall_results']['total_requests']} |\n")
            f.write(f"| Successful | {report['overall_results']['successful_requests']} |\n")
            f.write(f"| Failed | {report['overall_results']['failed_requests']} |\n")
            f.write(f"| Success Rate | {report['overall_results']['success_rate_percent']}% |\n\n")

            f.write("## Test Suite Results\n\n")

            for suite in report['test_suites']:
                f.write(f"### {suite['test_name']}\n\n")
                f.write(f"| Metric | Value |\n")
                f.write(f"|--------|-------|\n")
                f.write(f"| Total Requests | {suite['total_requests']} |\n")
                f.write(f"| Successful | {suite['successful_requests']} |\n")
                f.write(f"| Failed | {suite['failed_requests']} |\n")
                f.write(f"| Avg Response Time | {suite['avg_response_time_ms']}ms |\n")
                f.write(f"| Min Response Time | {suite['min_response_time_ms']}ms |\n")
                f.write(f"| Max Response Time | {suite['max_response_time_ms']}ms |\n")
                f.write(f"| P50 Response Time | {suite['p50_response_time_ms']}ms |\n")
                f.write(f"| P95 Response Time | {suite['p95_response_time_ms']}ms |\n")
                f.write(f"| P99 Response Time | {suite['p99_response_time_ms']}ms |\n")

                if suite['requests_per_second'] > 0:
                    f.write(f"| Throughput | {suite['requests_per_second']} req/s |\n")

                f.write(f"| Avg Result Count | {suite['avg_result_count']:.1f} |\n\n")

            f.write("## Criteria Check\n\n")

            if report['passed_criteria']:
                f.write("### ✓ Passed Criteria\n\n")
                for item in report['passed_criteria']:
                    f.write(f"- {item}\n")
                f.write("\n")

            if report['failed_criteria']:
                f.write("### ✗ Failed Criteria\n\n")
                for item in report['failed_criteria']:
                    f.write(f"- {item}\n")
                f.write("\n")

            f.write("## Recommendations\n\n")

            # Generate recommendations based on results
            recommendations = []

            for suite in report['test_suites']:
                if suite['p95_response_time_ms'] > report['success_criteria']['search_response_time_p95_ms']:
                    recommendations.append(
                        f"- **{suite['test_name']}**: P95 response time exceeds target. "
                        f"Consider optimizing queries or adding caching."
                    )

                if suite['failed_requests'] > 0:
                    recommendations.append(
                        f"- **{suite['test_name']}**: {suite['failed_requests']} failed requests. "
                        f"Review error handling and retry logic."
                    )

            if not recommendations:
                recommendations.append("- All performance targets met! Continue monitoring.")
            else:
                recommendations.insert(0, "Based on test results, consider the following optimizations:\n")

            for rec in recommendations:
                f.write(f"{rec}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Test PharmaKG search performance")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Number of concurrent requests to test (default: 10)"
    )

    args = parser.parse_args()

    tester = SearchPerformanceTester(api_base_url=args.api_url)

    try:
        tester.setup()
        report = tester.run_all_tests()

        # Exit with appropriate code
        if report['failed_criteria']:
            print("\n❌ Some performance criteria not met")
            sys.exit(1)
        else:
            print("\n✅ All performance criteria met!")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
