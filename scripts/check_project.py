#!/usr/bin/env python3
#===========================================================
# PharmaKG - 项目自动化检查脚本
# Pharmaceutical Knowledge Graph - Project Validation Script
#===========================================================
# 版本: v1.0
# 描述: 自动检查项目各模块和文档完整性
#===========================================================

import os
import sys
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

BOLD = "\033[1m"


class ProjectChecker:
    """PharmaKG 项目检查器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[Dict] = []
        self.check_summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }

    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_colors = {
            "INFO": BLUE,
            "SUCCESS": GREEN,
            "ERROR": RED,
            "WARNING": YELLOW
        }
        color = level_colors.get(level, RESET)
        print(f"{color}[{timestamp}]{RESET} {message}")

    def check_file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        full_path = self.project_root / file_path
        exists = full_path.exists()

        self._add_result(
            category="文件存在性",
            item=file_path,
            passed=exists,
            details=f"文件{'存在' if exists else '不存在'}"
        )
        return exists

    def check_directory_exists(self, dir_path: str) -> bool:
        """检查目录是否存在"""
        full_path = self.project_root / dir_path
        exists = full_path.is_dir()

        self._add_result(
            category="目录结构",
            item=dir_path,
            passed=exists,
            details=f"目录{'存在' if exists else '不存在'}"
        )
        return exists

    def check_python_syntax(self, file_path: str) -> bool:
        """检查 Python 文件语法"""
        full_path = self.project_root / file_path

        if not full_path.exists():
            return False

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            return True
        except SyntaxError as e:
            self._add_result(
                category="代码语法",
                item=file_path,
                passed=False,
                details=f"语法错误: {str(e)}"
            )
            return False
        except Exception as e:
            self._add_result(
                category="代码语法",
                item=file_path,
                passed=False,
                details=f"检查失败: {str(e)}"
            )
            return False

    def check_import_in_file(self, file_path: str, import_name: str) -> bool:
        """检查文件是否包含特定导入"""
        full_path = self.project_root / file_path

        if not full_path.exists():
            return False

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    if any(alias.name == import_name for alias in node.names):
                        return True
                elif isinstance(node, ast.ImportFrom):
                    if node.module == import_name:
                        return True
                    if any(alias.name == import_name for alias in node.names):
                        return True
            return False
        except Exception:
            return False

    def check_docker_compose_config(self) -> bool:
        """检查 Docker Compose 配置"""
        compose_file = self.project_root / "deployment/docker-compose.yml"

        if not compose_file.exists():
            self._add_result(
                category="部署配置",
                item="docker-compose.yml",
                passed=False,
                details="配置文件不存在"
            )
            return False

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            # 检查必需的服务
            required_services = ["neo4j", "api"]
            services = config.get("services", {})

            for service in required_services:
                if service not in services:
                    self._add_result(
                        category="部署配置",
                        item=f"服务 {service}",
                        passed=False,
                        details=f"服务 {service} 未在配置中定义"
                    )
                    return False

            self._add_result(
                category="部署配置",
                item="docker-compose.yml",
                passed=True,
                details="配置有效"
            )
            return True
        except Exception as e:
            self._add_result(
                category="部署配置",
                item="docker-compose.yml",
                passed=False,
                details=f"配置解析失败: {str(e)}"
            )
            return False

    def run_module_checks(self):
        """运行模块检查"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("检查代码模块...", "INFO")

        modules = {
            "api": ["api/main.py", "api/config.py", "api/database.py"],
            "etl": [
                "etl/__init__.py",
                "etl/config.py",
                "etl/cli.py",
                "etl/scheduler.py",
                "etl/extractors/base.py",
                "etl/transformers/base.py",
                "etl/loaders/neo4j_batch.py"
            ],
            "pipelines": [
                "etl/pipelines/rd_pipeline.py",
                "etl/pipelines/clinical_pipeline.py",
                "etl/pipelines/sc_pipeline.py",
                "etl/pipelines/regulatory_pipeline.py"
            ],
            "graph_analytics": [
                "graph_analytics/__init__.py",
                "graph_analytics/algorithms.py",
                "graph_analytics/inference.py",
                "graph_analytics/embeddings.py",
                "graph_analytics/visualization.py",
                "graph_analytics/api.py"
            ],
            "ml_analytics": [
                "ml_analytics/__init__.py",
                "ml_analytics/models.py",
                "ml_analytics/predictors.py",
                "ml_analytics/reasoning.py"
            ],
            "deployment": [
                "deployment/docker-compose.yml",
                "deployment/Dockerfile",
                "deployment/nginx.conf",
                "deployment/deploy.sh"
            ]
        }

        for module_name, files in modules.items():
            self.log(f"\n检查模块: {module_name}", "INFO")
            for file_path in files:
                self.check_file_exists(file_path)

    def run_documentation_checks(self):
        """运行文档检查"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("检查文档...", "INFO")

        docs = [
            ("README.md", "项目主文档"),
            ("CHECKLIST.md", "检查清单文档"),
            ("deployment/README.md", "部署文档")
        ]

        for doc_path, desc in docs:
            exists = self.check_file_exists(doc_path)
            if exists:
                # 检查文档是否非空
                full_path = self.project_root / doc_path
                with open(full_path, 'r') as f:
                    content = f.read()
                    if len(content.strip()) > 100:
                        self._add_result(
                            category="文档质量",
                            item=doc_path,
                            passed=True,
                            details=f"{desc}内容完整"
                        )
                    else:
                        self._add_result(
                            category="文档质量",
                            item=doc_path,
                            passed=False,
                            details=f"{desc}内容过少"
                        )

    def run_dependency_checks(self):
        """运行依赖检查"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("检查依赖...", "INFO")

        # 检查 requirements.txt
        req_file = self.project_root / "api/requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                requirements = f.read()

            # 关键依赖检查
            key_packages = [
                "fastapi",
                "neo4j",
                "pydantic",
                "uvicorn",
                "py2neo",
                "numpy",
                "pandas"
            ]

            for package in key_packages:
                if package in requirements.lower():
                    self._add_result(
                        category="依赖",
                        item=f"package:{package}",
                        passed=True,
                        details=f"{package} 在 requirements.txt 中"
                    )
        else:
            self._add_result(
                category="依赖",
                item="requirements.txt",
                passed=False,
                details="requirements.txt 不存在"
            )

    def run_integration_checks(self):
        """运行集成检查"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("检查集成...", "INFO")

        # 检查 API 主文件是否导入图分析模块
        api_main = self.project_root / "api/main.py"
        if api_main.exists():
            with open(api_main, 'r') as f:
                content = f.read()

            # 检查是否导入了 AnalyticsAPI
            if "AnalyticsAPI" in content or "graph_analytics" in content:
                self._add_result(
                    category="集成",
                    item="API-图分析集成",
                    passed=True,
                    details="API 已集成图分析模块"
                )
            else:
                self._add_result(
                    category="集成",
                    item="API-图分析集成",
                    passed=False,
                    details="API 未集成图分析模块"
                )

    def run_deployment_checks(self):
        """运行部署检查"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("检查部署配置...", "INFO")

        # 检查部署脚本可执行权限
        deploy_script = self.project_root / "deployment/deploy.sh"
        if deploy_script.exists():
            is_executable = os.access(deploy_script, os.X_OK)
            self._add_result(
                category="部署配置",
                item="deploy.sh 可执行权限",
                passed=is_executable,
                details=f"{'有' if is_executable else '无'}执行权限"
            )
        else:
            self._add_result(
                category="部署配置",
                item="deploy.sh",
                passed=False,
                details="部署脚本不存在"
            )

        # 检查 Docker Compose 配置
        self.check_docker_compose_config()

    def run_all_checks(self) -> Dict[str, Dict]:
        """运行所有检查"""
        self.log(f"{BOLD}PharmaKG 项目检查{RESET}", "INFO")
        self.log(f"项目路径: {self.project_root}", "INFO")
        self.log(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log("执行人: 自动化检查脚本\n", "INFO")

        # 运行各类检查
        self.run_module_checks()
        self.run_documentation_checks()
        self.run_dependency_checks()
        self.run_integration_checks()
        self.run_deployment_checks()

        # 生成总结报告
        return self._generate_summary_report()

    def _add_result(self, category: str, item: str, passed: bool, details: str = ""):
        """添加检查结果"""
        self.check_summary["total"] += 1

        if passed:
            self.check_summary["passed"] += 1
            status = "✅"
        else:
            self.check_summary["failed"] += 1
            status = "❌"

        self.results.append({
            "category": category,
            "item": item,
            "status": status,
            "details": details
        })

    def _generate_summary_report(self) -> Dict[str, Dict]:
        """生成总结报告"""
        self.log("\n" + "=" * 60, "INFO")
        self.log(f"{BOLD}检查报告总结{RESET}", "INFO")
        self.log("=" * 60, "INFO")

        # 按类别统计
        category_stats = {}
        for result in self.results:
            cat = result["category"]
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "passed": 0, "failed": 0}
            category_stats[cat]["total"] += 1
            if result["status"] == "✅":
                category_stats[cat]["passed"] += 1
            else:
                category_stats[cat]["failed"] += 1

        # 打印类别统计
        for category, stats in category_stats.items():
            total = stats["total"]
            passed = stats["passed"]
            failed = stats["failed"]
            rate = (passed / total * 100) if total > 0 else 0

            status_color = GREEN if rate >= 80 else YELLOW if rate >= 60 else RED
            self.log(
                f"{category}: {passed}/{total} ({rate:.1f}%)",
                "INFO"
            )

        # 打印总体统计
        self.log("\n" + "-" * 60, "INFO")
        total = self.check_summary["total"]
        passed = self.check_summary["passed"]
        failed = self.check_summary["failed"]
        rate = (passed / total * 100) if total > 0 else 0

        overall_status = "✅ 通过" if rate >= 80 else "⚠️ 需改进" if rate >= 60 else "❌ 不通过"

        self.log(f"\n{BOLD}总体统计:{RESET}", "INFO")
        self.log(f"  总检查项: {total}")
        self.log(f"  通过: {GREEN}{passed}{RESET} ({rate:.1f}%)")
        self.log(f"  失败: {RED}{failed}{RESET}")

        self.log(f"\n{BOLD}状态: {overall_status}{RESET}\n", "INFO")

        # 打印失败的检查项
        if failed > 0:
            self.log("失败的检查项:", "WARNING")
            for result in self.results:
                if result["status"] == "❌":
                    self.log(f"  [{result['category']}] {result['item']}: {result['details']}", "ERROR")

        return {
            "summary": self.check_summary,
            "categories": category_stats,
            "detailed_results": self.results
        }

    def save_report(self, output_file: str = None):
        """保存检查报告到文件"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.project_root / f"check_report_{timestamp}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# PharmaKG 项目检查报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 检查统计\n\n")
            f.write(f"- 总检查项: {self.check_summary['total']}\n")
            f.write(f"- 通过: {self.check_summary['passed']}\n")
            f.write(f"- 失败: {self.check_summary['failed']}\n\n")
            f.write("## 详细结果\n\n")

            for result in self.results:
                f.write(f"- {result['status']} **{result['category']}**: {result['item']}\n")
                f.write(f"  - {result['details']}\n")

        self.log(f"\n报告已保存到: {output_file}", "SUCCESS")


def main():
    """主函数"""
    # 获取项目根目录（假设脚本在 scripts/ 目录下）
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # 创建检查器
    checker = ProjectChecker(project_root)

    try:
        # 运行所有检查
        report = checker.run_all_checks()

        # 保存报告
        checker.save_report()

        # 根据检查结果设置退出码
        if report["summary"]["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"{RED}检查过程中发生错误: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
