#!/usr/bin/env python3
"""
Comprehensive Test Runner for Grid Trading Bot

Runs all test suites including:
- Unit tests
- Integration tests
- UI tests
- Error scenario tests
- Performance benchmarks
- Edge case tests
"""

import sys
import os
import time
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any
import logging
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveTestRunner:
    """Comprehensive test runner for all test suites."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.total_duration = 0
        self.overall_stats = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def run_all_tests(self, include_performance: bool = True, include_ui: bool = True) -> Dict[str, Any]:
        """
        Run all test suites.
        
        Args:
            include_performance: Whether to include performance tests
            include_ui: Whether to include UI tests
            
        Returns:
            Comprehensive test results
        """
        logger.info("Starting comprehensive test suite")
        start_time = time.time()
        
        # Define test suites
        test_suites = [
            {
                'name': 'Core Unit Tests',
                'path': 'tests/services',
                'description': 'Core service unit tests',
                'critical': True
            },
            {
                'name': 'Integration Tests',
                'path': 'tests/integration',
                'description': 'Integration tests',
                'critical': True
            },
            {
                'name': 'Configuration Tests',
                'path': 'tests/config',
                'description': 'Configuration management tests',
                'critical': True
            },
            {
                'name': 'Error Scenario Tests',
                'path': 'tests/error_scenarios',
                'description': 'Error handling and edge case tests',
                'critical': False
            }
        ]
        
        # Add UI tests if requested
        if include_ui:
            test_suites.append({
                'name': 'UI Component Tests',
                'path': 'tests/web_ui',
                'description': 'Web UI component and callback tests',
                'critical': False
            })
        
        # Add performance tests if requested
        if include_performance:
            test_suites.append({
                'name': 'Performance Benchmarks',
                'path': 'tests/performance',
                'description': 'Performance and load tests',
                'critical': False
            })
        
        # Run each test suite
        for suite in test_suites:
            logger.info(f"Running {suite['name']}...")
            result = self._run_test_suite(suite)
            self.test_results[suite['name']] = result
            
            # Update overall statistics
            self._update_overall_stats(result)
        
        self.total_duration = time.time() - start_time
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report()
        
        # Print summary
        self._print_comprehensive_summary(report)
        
        return report
    
    def run_critical_tests_only(self) -> Dict[str, Any]:
        """Run only critical test suites for CI/CD."""
        logger.info("Running critical tests only")
        
        critical_suites = [
            {
                'name': 'Core Unit Tests',
                'path': 'tests/services',
                'description': 'Core service unit tests',
                'critical': True
            },
            {
                'name': 'Integration Tests',
                'path': 'tests/integration',
                'description': 'Integration tests',
                'critical': True
            },
            {
                'name': 'Configuration Tests',
                'path': 'tests/config',
                'description': 'Configuration management tests',
                'critical': True
            }
        ]
        
        start_time = time.time()
        
        for suite in critical_suites:
            logger.info(f"Running {suite['name']}...")
            result = self._run_test_suite(suite)
            self.test_results[suite['name']] = result
            self._update_overall_stats(result)
        
        self.total_duration = time.time() - start_time
        
        report = self._generate_comprehensive_report()
        self._print_comprehensive_summary(report)
        
        return report
    
    def _run_test_suite(self, suite: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific test suite."""
        test_path = self.project_root / suite['path']
        
        if not test_path.exists():
            logger.warning(f"Test path not found: {suite['path']}")
            return {
                'status': 'skipped',
                'reason': 'Test path not found',
                'duration': 0,
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 0,
                'output': ''
            }
        
        try:
            # Build pytest command
            cmd = [
                sys.executable, '-m', 'pytest',
                str(test_path),
                '-v',
                '--tb=short',
                '--disable-warnings',
                '--maxfail=10',  # Stop after 10 failures
                f'--timeout=300'  # 5 minute timeout per test
            ]
            
            # Add coverage for critical tests
            if suite.get('critical', False):
                cmd.extend(['--cov=core', '--cov=config', '--cov-report=term-missing'])
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=1800  # 30 minute timeout for entire suite
            )
            duration = time.time() - start_time
            
            # Parse pytest output
            stats = self._parse_pytest_output(result.stdout)
            
            return {
                'status': 'completed',
                'return_code': result.returncode,
                'duration': duration,
                'output': result.stdout,
                'errors': result.stderr,
                **stats
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test suite {suite['name']} timed out")
            return {
                'status': 'timeout',
                'duration': 1800,
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 1,
                'output': '',
                'error_message': 'Test suite timed out'
            }
        
        except Exception as e:
            logger.error(f"Error running test suite {suite['name']}: {e}")
            return {
                'status': 'error',
                'duration': 0,
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 1,
                'output': '',
                'error_message': str(e)
            }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, int]:
        """Parse pytest output to extract statistics."""
        stats = {
            'tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        lines = output.split('\n')
        
        # Look for summary lines
        for line in lines:
            line = line.strip().lower()
            
            # Parse summary line like "5 passed, 2 failed, 1 skipped in 10.5s"
            if 'passed' in line or 'failed' in line or 'skipped' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        try:
                            stats['passed'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == 'failed' and i > 0:
                        try:
                            stats['failed'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == 'skipped' and i > 0:
                        try:
                            stats['skipped'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == 'error' and i > 0:
                        try:
                            stats['errors'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
        
        stats['tests'] = stats['passed'] + stats['failed'] + stats['skipped'] + stats['errors']
        return stats
    
    def _update_overall_stats(self, result: Dict[str, Any]):
        """Update overall statistics with suite results."""
        if result['status'] == 'completed':
            self.overall_stats['total_tests'] += result.get('tests', 0)
            self.overall_stats['passed'] += result.get('passed', 0)
            self.overall_stats['failed'] += result.get('failed', 0)
            self.overall_stats['skipped'] += result.get('skipped', 0)
            self.overall_stats['errors'] += result.get('errors', 0)
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        # Calculate success rate
        total_tests = self.overall_stats['total_tests']
        passed_tests = self.overall_stats['passed']
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Identify problem areas
        problem_suites = []
        for suite_name, result in self.test_results.items():
            if result.get('failed', 0) > 0 or result.get('errors', 0) > 0 or result.get('status') != 'completed':
                problem_suites.append({
                    'name': suite_name,
                    'failed': result.get('failed', 0),
                    'errors': result.get('errors', 0),
                    'status': result.get('status', 'unknown')
                })
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics()
        
        return {
            'summary': {
                **self.overall_stats,
                'success_rate': success_rate,
                'total_duration': self.total_duration
            },
            'suite_results': self.test_results,
            'problem_areas': problem_suites,
            'recommendations': recommendations,
            'quality_metrics': quality_metrics,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if self.overall_stats['failed'] > 0:
            recommendations.append(f"Fix {self.overall_stats['failed']} failing tests before deployment")
        
        if self.overall_stats['errors'] > 0:
            recommendations.append(f"Investigate {self.overall_stats['errors']} test errors")
        
        if self.overall_stats['skipped'] > 10:
            recommendations.append(f"Review {self.overall_stats['skipped']} skipped tests - may indicate missing dependencies")
        
        # Check for slow test suites
        slow_suites = []
        for suite_name, result in self.test_results.items():
            if result.get('duration', 0) > 300:  # 5 minutes
                slow_suites.append(suite_name)
        
        if slow_suites:
            recommendations.append(f"Optimize slow test suites: {', '.join(slow_suites)}")
        
        # Check success rate
        total_tests = self.overall_stats['total_tests']
        success_rate = (self.overall_stats['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate < 95:
            recommendations.append("Test success rate below 95% - investigate failing tests")
        elif success_rate == 100:
            recommendations.append("All tests passing! Consider adding more edge case tests")
        
        return recommendations
    
    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate code quality metrics based on test results."""
        total_tests = self.overall_stats['total_tests']
        
        if total_tests == 0:
            return {'error': 'No tests found'}
        
        return {
            'test_coverage_estimate': min(100, (total_tests / 50) * 100),  # Rough estimate
            'reliability_score': (self.overall_stats['passed'] / total_tests) * 100,
            'test_efficiency': total_tests / max(1, self.total_duration / 60),  # tests per minute
            'error_rate': (self.overall_stats['failed'] + self.overall_stats['errors']) / total_tests * 100
        }
    
    def _print_comprehensive_summary(self, report: Dict[str, Any]):
        """Print comprehensive test summary."""
        print("\n" + "="*100)
        print("COMPREHENSIVE TEST SUITE SUMMARY")
        print("="*100)
        
        summary = report['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Errors: {summary['errors']}")
        print(f"Total Duration: {summary['total_duration']:.1f} seconds")
        
        print("\nQUALITY METRICS:")
        print("-" * 50)
        metrics = report['quality_metrics']
        if 'error' not in metrics:
            print(f"Reliability Score: {metrics['reliability_score']:.1f}%")
            print(f"Test Efficiency: {metrics['test_efficiency']:.1f} tests/minute")
            print(f"Error Rate: {metrics['error_rate']:.1f}%")
        
        print("\nSUITE BREAKDOWN:")
        print("-" * 50)
        for suite_name, result in report['suite_results'].items():
            status = result.get('status', 'unknown')
            duration = result.get('duration', 0)
            tests = result.get('tests', 0)
            passed = result.get('passed', 0)
            failed = result.get('failed', 0)
            
            print(f"{suite_name}:")
            print(f"  Status: {status}")
            print(f"  Tests: {tests} (✓{passed} ✗{failed})")
            print(f"  Duration: {duration:.1f}s")
        
        if report['problem_areas']:
            print("\nPROBLEM AREAS:")
            print("-" * 50)
            for problem in report['problem_areas']:
                print(f"• {problem['name']}: {problem['failed']} failed, {problem['errors']} errors")
        
        if report['recommendations']:
            print("\nRECOMMENDATIONS:")
            print("-" * 50)
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec}")
        
        print("="*100)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Run comprehensive Grid Trading Bot tests')
    parser.add_argument('--critical-only', action='store_true', help='Run only critical tests')
    parser.add_argument('--no-performance', action='store_true', help='Skip performance tests')
    parser.add_argument('--no-ui', action='store_true', help='Skip UI tests')
    parser.add_argument('--output', type=str, help='Output file for detailed report')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = ComprehensiveTestRunner()
    
    try:
        if args.critical_only:
            report = runner.run_critical_tests_only()
        else:
            report = runner.run_all_tests(
                include_performance=not args.no_performance,
                include_ui=not args.no_ui
            )
        
        # Save detailed report if requested
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nDetailed report saved to: {output_path}")
        
        # Exit with appropriate code
        if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running comprehensive tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
