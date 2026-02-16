#!/usr/bin/env python3
"""psycopg3 바이너리 호환성 & import 진단 스크립트.

사용법:
    python scripts/check_psycopg.py                # 기본 진단
    python scripts/check_psycopg.py --test-connection  # DB 연결까지 테스트
"""

import argparse
import platform
import struct
import sys
import time


def _section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def check_platform() -> None:
    """Mac architecture 및 Python 빌드 정보."""
    _section("플랫폼 정보")
    print(f"  OS          : {platform.system()} {platform.release()}")
    print(f"  Machine     : {platform.machine()}")
    print(f"  Python      : {sys.version}")
    print(f"  Pointer size: {struct.calcsize('P') * 8}-bit")

    if platform.system() == "Darwin" and platform.machine() == "arm64":
        print("  ℹ️  Apple Silicon (arm64) 감지 — arm64 wheel 필요")
    elif platform.system() == "Darwin":
        print("  ℹ️  Intel Mac (x86_64) 감지")


def check_import(module_name: str, attr: str | None = None) -> tuple[bool, float]:
    """모듈 import 테스트 및 소요 시간 측정."""
    start = time.monotonic()
    try:
        mod = __import__(module_name, fromlist=[attr] if attr else [])
        elapsed = time.monotonic() - start
        version = getattr(mod, "__version__", "N/A")
        print(f"  ✅ {module_name:40s}  {elapsed:.3f}s  (v{version})")
        return True, elapsed
    except ImportError as exc:
        elapsed = time.monotonic() - start
        print(f"  ❌ {module_name:40s}  FAILED: {exc}")
        return False, elapsed


def check_psycopg_binary() -> None:
    """psycopg C 확장 모듈(psycopg-binary) 로드 여부 확인."""
    _section("psycopg-binary (C 확장) 확인")
    try:
        import psycopg  # noqa: F811

        impl = getattr(psycopg, "__impl__", None)
        if impl:
            print(f"  Implementation: {impl}")

        # Check C module
        try:
            from psycopg import _cmodule  # noqa: F401

            print("  ✅ C 모듈 (_cmodule) 로드 성공 — 최적 성능")
        except ImportError:
            print("  ⚠️  C 모듈 없음 — pure-Python fallback (느릴 수 있음)")
            print("     해결: pip install 'psycopg[binary]>=3.2.0'")

        # Check binary package directly
        try:
            import psycopg_binary  # noqa: F401

            print("  ✅ psycopg_binary 패키지 확인됨")
        except ImportError:
            print("  ⚠️  psycopg_binary 미설치 — C 확장 wheel 없음")

    except ImportError:
        print("  ❌ psycopg 자체가 설치되지 않음")


def check_imports() -> None:
    """핵심 패키지 import 테스트."""
    _section("Import 테스트 (소요 시간 측정)")

    total_start = time.monotonic()

    check_import("psycopg")
    check_import("psycopg_pool")
    check_import("langgraph.checkpoint.postgres.aio")

    total = time.monotonic() - total_start
    print(f"\n  총 소요 시간: {total:.3f}s")

    if total > 3.0:
        print("  ⚠️  Import가 3초 이상 — 네트워크 문제 또는 바이너리 불일치 가능성")
    elif total > 1.0:
        print("  ℹ️  Import가 1초 이상 — 정상 범위지만 모니터링 권장")
    else:
        print("  ✅ Import 시간 정상")


def test_connection(dsn: str | None = None) -> None:
    """실제 PostgreSQL 연결 테스트."""
    _section("DB 연결 테스트")

    if dsn is None:
        try:
            from src.config import settings

            dsn = settings.postgres_dsn
            print(f"  DSN: {dsn[:30]}...")
        except Exception as exc:
            print(f"  ❌ config 로드 실패: {exc}")
            return

    try:
        import psycopg

        start = time.monotonic()
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            row = conn.execute("SELECT version()").fetchone()
            elapsed = time.monotonic() - start
            print(f"  ✅ 연결 성공 ({elapsed:.3f}s)")
            print(f"  PostgreSQL: {row[0][:60]}...")
    except Exception as exc:
        print(f"  ❌ 연결 실패: {exc}")
        print("     DB가 실행 중인지 확인하세요 (docker compose up -d)")


def main() -> None:
    parser = argparse.ArgumentParser(description="psycopg3 진단 스크립트")
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="실제 DB 연결까지 테스트",
    )
    parser.add_argument("--dsn", help="PostgreSQL DSN (기본: config에서 읽음)")
    args = parser.parse_args()

    print("🔍 psycopg3 진단 시작")

    check_platform()
    check_imports()
    check_psycopg_binary()

    if args.test_connection:
        test_connection(args.dsn)

    print(f"\n{'─' * 50}")
    print("  진단 완료")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
