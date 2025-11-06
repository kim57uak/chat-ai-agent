"""
Test Runner
통합 테스트 및 성능 테스트 실행
"""

import sys
import subprocess
from pathlib import Path
from core.logging import get_logger

logger = get_logger("test_runner")


def run_integration_tests():
    """통합 테스트 실행"""
    logger.info("=" * 60)
    logger.info("Running Integration Tests")
    logger.info("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration", "-v", "--tb=short"],
        cwd=Path(__file__).parent
    )
    
    return result.returncode == 0


def run_performance_tests():
    """성능 테스트 실행"""
    logger.info("=" * 60)
    logger.info("Running Performance Tests")
    logger.info("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/performance", "-v", "--tb=short"],
        cwd=Path(__file__).parent
    )
    
    return result.returncode == 0


def main():
    """메인 실행"""
    logger.info("Starting Test Suite")
    
    # 통합 테스트
    integration_passed = run_integration_tests()
    
    # 성능 테스트
    performance_passed = run_performance_tests()
    
    # 결과 요약
    logger.info("=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    logger.info(f"Integration Tests: {'✓ PASSED' if integration_passed else '✗ FAILED'}")
    logger.info(f"Performance Tests: {'✓ PASSED' if performance_passed else '✗ FAILED'}")
    
    if integration_passed and performance_passed:
        logger.info("=" * 60)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("✗ SOME TESTS FAILED")
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
