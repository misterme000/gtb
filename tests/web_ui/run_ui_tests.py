#!/usr/bin/env python3
"""
UI Test Runner for Grid Trading Bot Web UI

Comprehensive test runner for all UI-related tests including:
- Component tests
- Callback integration tests  
- End-to-end user journey tests
- Performance tests
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UITestRunner:
    """Comprehensive UI test runner with reporting and analysis."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent.parent
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all UI tests and return comprehensive results.
        
        Returns:
            Dictionary with test results and statistics
        """
        logger.info("Starting comprehensive UI test suite")
        start_time = time.time()
        
        # Test suites to run
        test_suites = [
            {
                'name': 'Component Tests',
                'file': 'test_ui_components.py',
                'description': 'Tests for individual UI components'
            },
            {
                'name': 'Callback Integration Tests',
                'file': 'test_callback_integration.py',
                'description': 'Tests for callback functions and interactions'
            },
            {
                'name': 'End-to-End Tests',
                'file': 'test_end_to_end.py',
                'description': 'Complete user journey tests'
            }
        ]
        
        # Run each test suite
        for suite in test_suites:
            logger.info(f"Running {suite['name']}...")
            result = self._run_test_suite(suite)
            self.test_results[suite['name']] = result
        
        # Calculate overall statistics
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        report = self._generate_test_report(total_time)
        
        # Print summary
        self._print_test_summary(report)
        
        return report
    
    def run_specific_test(self, test_name: str) -> Dict[str, Any]:
        """
        Run a specific test file.
        
        Args:
            test_name: Name of the test file (without .py extension)
            
        Returns:
            Test results for the specific test
        """
        test_file = f"{test_name}.py"
        test_path = self.test_dir / test_file
        
        if not test_path.exists():
            logger.error(f"Test file not found: {test_file}")
            return {"error": f"Test file not found: {test_file}"}
        
        logger.info(f"Running specific test: {test_name}")
        
        suite = {
            'name': test_name,
            'file': test_file,
            'description': f'Specific test: {test_name}'
        }
        
        result = self._run_test_suite(suite)
        return result
    
    def _run_test_suite(self, suite: Dict[str, str]) -> Dict[str, Any]:
        """
        Run a specific test suite.
        
        Args:
            suite: Test suite configuration
            
        Returns:
            Test results for the suite
        """
        test_file = self.test_dir / suite['file']
        
        if not test_file.exists():
            logger.warning(f"Test file not found: {suite['file']}")
            return {
                'status': 'skipped',
                'reason': 'Test file not found',
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'duration': 0,
                'output': ''
            }
        
        try:
            # Run pytest on the specific file
            cmd = [
                sys.executable, '-m', 'pytest',
                str(test_file),
                '-v',
                '--tb=short',
                '--disable-warnings'
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300  # 5 minute timeout
            )
            duration = time.time() - start_time
            
            # Parse pytest output
            output_lines = result.stdout.split('\n')
            test_stats = self._parse_pytest_output(output_lines)
            
            # Update overall statistics
            self.total_tests += test_stats['tests']
            self.passed_tests += test_stats['passed']
            self.failed_tests += test_stats['failed']
            self.skipped_tests += test_stats['skipped']
            
            return {
                'status': 'completed',
                'return_code': result.returncode,
                'duration': duration,
                'output': result.stdout,
                'errors': result.stderr,
                **test_stats
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test suite {suite['name']} timed out")
            return {
                'status': 'timeout',
                'duration': 300,
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'output': '',
                'errors': 'Test suite timed out after 5 minutes'
            }
        
        except Exception as e:
            logger.error(f"Error running test suite {suite['name']}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'duration': 0,
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'output': '',
                'errors': str(e)
            }
    
    def _parse_pytest_output(self, output_lines: List[str]) -> Dict[str, int]:
        """
        Parse pytest output to extract test statistics.
        
        Args:
            output_lines: Lines of pytest output
            
        Returns:
            Dictionary with test statistics
        """
        stats = {
            'tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Look for the summary line
        for line in output_lines:
            if 'passed' in line or 'failed' in line or 'skipped' in line:
                # Parse lines like "5 passed, 2 failed, 1 skipped"
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
        
        stats['tests'] = stats['passed'] + stats['failed'] + stats['skipped']
        return stats
    
    def _generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """
        Generate comprehensive test report.
        
        Args:
            total_time: Total execution time
            
        Returns:
            Comprehensive test report
        """
        # Calculate success rate
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        # Identify problem areas
        problem_suites = []
        for suite_name, result in self.test_results.items():
            if result.get('failed', 0) > 0 or result.get('status') != 'completed':
                problem_suites.append({
                    'name': suite_name,
                    'failed': result.get('failed', 0),
                    'status': result.get('status', 'unknown'),
                    'errors': result.get('errors', '')
                })
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return {
            'summary': {
                'total_tests': self.total_tests,
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'skipped': self.skipped_tests,
                'success_rate': success_rate,
                'total_time': total_time
            },
            'suite_results': self.test_results,
            'problem_areas': problem_suites,
            'recommendations': recommendations,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if self.failed_tests > 0:
            recommendations.append("Review failed tests and fix underlying issues")
        
        if self.skipped_tests > 0:
            recommendations.append("Investigate skipped tests - they may indicate missing dependencies")
        
        # Check for specific issues
        for suite_name, result in self.test_results.items():
            if result.get('status') == 'timeout':
                recommendations.append(f"Optimize {suite_name} - tests are taking too long")
            
            if result.get('status') == 'error':
                recommendations.append(f"Fix setup issues in {suite_name}")
        
        if not recommendations:
            recommendations.append("All tests passing! Consider adding more edge case tests")
        
        return recommendations
    
    def _print_test_summary(self, report: Dict[str, Any]):
        """Print a formatted test summary."""
        print("\n" + "="*80)
        print("UI TEST SUITE SUMMARY")
        print("="*80)
        
        summary = report['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Total Time: {summary['total_time']:.2f} seconds")
        
        print("\nSUITE BREAKDOWN:")
        print("-" * 40)
        for suite_name, result in report['suite_results'].items():
            status = result.get('status', 'unknown')
            duration = result.get('duration', 0)
            tests = result.get('tests', 0)
            passed = result.get('passed', 0)
            failed = result.get('failed', 0)
            
            print(f"{suite_name}:")
            print(f"  Status: {status}")
            print(f"  Tests: {tests} (Passed: {passed}, Failed: {failed})")
            print(f"  Duration: {duration:.2f}s")
        
        if report['problem_areas']:
            print("\nPROBLEM AREAS:")
            print("-" * 40)
            for problem in report['problem_areas']:
                print(f"• {problem['name']}: {problem['failed']} failed tests")
        
        if report['recommendations']:
            print("\nRECOMMENDATIONS:")
            print("-" * 40)
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec}")
        
        print("="*80)


def main():
    """Main function to run UI tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Grid Trading Bot UI Tests')
    parser.add_argument(
        '--test',
        type=str,
        help='Run specific test file (without .py extension)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create test runner
    runner = UITestRunner()
    
    try:
        if args.test:
            # Run specific test
            result = runner.run_specific_test(args.test)
            print(f"\nTest Results for {args.test}:")
            print(f"Status: {result.get('status', 'unknown')}")
            if 'duration' in result:
                print(f"Duration: {result['duration']:.2f}s")
            if result.get('output'):
                print("Output:")
                print(result['output'])
        else:
            # Run all tests
            report = runner.run_all_tests()
            
            # Save report to file
            import json
            report_file = Path(__file__).parent / 'ui_test_report.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\nDetailed report saved to: {report_file}")
    
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
