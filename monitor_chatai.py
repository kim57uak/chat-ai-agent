#!/usr/bin/env python3
"""Chat AI Agent 리소스 모니터링 도구"""

import psutil
import time
import sys
from datetime import datetime

def find_chatai_process():
    """Chat AI Agent 프로세스 찾기"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('main.py' in str(cmd) for cmd in cmdline):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def format_bytes(bytes_val):
    """바이트를 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f}TB"

def monitor_process(interval=2):
    """프로세스 모니터링 (메모리 누수 감지 포함)"""
    print("🔍 Chat AI Agent 프로세스 검색 중...")
    
    proc = find_chatai_process()
    if not proc:
        print("❌ Chat AI Agent 프로세스를 찾을 수 없습니다.")
        print("💡 main.py가 실행 중인지 확인하세요.")
        return
    
    print(f"✅ 프로세스 발견: PID {proc.pid}")
    print(f"📊 모니터링 시작 (Ctrl+C로 종료)\n")
    print("=" * 80)
    
    # 메모리 누수 감지용 변수
    mem_history = []  # 실시간 표시용 (최근 30개)
    all_mem_samples = []  # 전체 샘플 저장 (최종 분석용)
    max_history = 30
    leak_threshold = 1.5  # 1.5MB/분 이상 증가 시 경고
    
    # GC 작동 감지용
    peak_memory = 0
    gc_detected_count = 0
    last_significant_drop = 0
    
    start_time = time.time()
    
    try:
        iteration = 0
        while True:
            try:
                # CPU 사용률
                cpu_percent = proc.cpu_percent(interval=0.1)
                
                # 메모리 정보
                mem_info = proc.memory_info()
                mem_percent = proc.memory_percent()
                
                # 자식 프로세스 포함
                children = proc.children(recursive=True)
                total_cpu = cpu_percent
                total_mem = mem_info.rss
                
                for child in children:
                    try:
                        total_cpu += child.cpu_percent(interval=0.1)
                        total_mem += child.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # 전체 샘플 저장 (최종 분석용)
                all_mem_samples.append(total_mem)
                
                # GC 작동 감지 (10MB 이상 감소 시)
                if total_mem < peak_memory - (10 * 1024 * 1024):
                    gc_detected_count += 1
                    last_significant_drop = (peak_memory - total_mem) / (1024 * 1024)
                    peak_memory = total_mem
                elif total_mem > peak_memory:
                    peak_memory = total_mem
                
                # 실시간 표시용 히스토리 (최근 30개만)
                mem_history.append(total_mem)
                if len(mem_history) > max_history:
                    mem_history.pop(0)
                
                # 전체 메모리 비율 계산 (자식 프로세스 포함)
                total_mem_percent = (total_mem / psutil.virtual_memory().total) * 100
                
                # 메모리 상태 분석
                leak_status = ""
                if len(mem_history) >= 15:
                    # 최근 메모리 증가율 계산 (MB/분)
                    time_span = len(mem_history) * interval / 60  # 분 단위
                    mem_increase = (mem_history[-1] - mem_history[0]) / (1024 * 1024)  # MB
                    leak_rate = mem_increase / time_span if time_span > 0 else 0
                    
                    # GC 작동 여부 표시
                    gc_status = f" (GC: {gc_detected_count}회)" if gc_detected_count > 0 else ""
                    
                    # 최근 감소량 표시
                    if last_significant_drop > 0:
                        gc_status += f" [-{last_significant_drop:.0f}MB]"
                    
                    # 메모리 상태 판단
                    if abs(leak_rate) < 0.3:
                        leak_status = f" ✅ 안정{gc_status}"
                    elif leak_rate > 0.5:
                        if gc_detected_count > 0:
                            leak_status = f" 📊 증가중 +{leak_rate:.1f}MB/분{gc_status}"
                        else:
                            leak_status = f" ⚠️ 누수의심 +{leak_rate:.1f}MB/분 (GC 미작동)"
                    elif leak_rate < -0.5:
                        leak_status = f" 📉 감소중 {leak_rate:.1f}MB/분{gc_status}"
                    else:
                        leak_status = f" ✅ 안정{gc_status}"
                else:
                    leak_status = " ⏳ 분석중..."
                
                # 출력
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\r[{timestamp}] "
                      f"CPU: {total_cpu:5.1f}% | "
                      f"메모리: {format_bytes(total_mem):>8} ({total_mem_percent:4.1f}%) | "
                      f"자식: {len(children):2d}개{leak_status}",
                      end='', flush=True)
                
                iteration += 1
                time.sleep(interval)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print("\n\n❌ 프로세스가 종료되었습니다.")
                break
                
    except KeyboardInterrupt:
        print("\n\n📊 모니터링 종료 - 최종 분석")
        if all_mem_samples:
            # 전체 모니터링 시간 계산
            total_time = (time.time() - start_time) / 60  # 분 단위
            total_increase = (all_mem_samples[-1] - all_mem_samples[0]) / (1024 * 1024)  # MB
            avg_rate = total_increase / total_time if total_time > 0 else 0
            
            print(f"총 모니터링 시간: {total_time:.1f}분")
            print(f"메모리 변화: {total_increase:+.1f}MB")
            print(f"평균 증가율: {avg_rate:+.2f}MB/분")
            
            # 최소/최대 메모리 표시 (전체 샘플 기준)
            min_mem = min(all_mem_samples) / (1024 * 1024)
            max_mem = max(all_mem_samples) / (1024 * 1024)
            print(f"메모리 범위: {min_mem:.1f}MB ~ {max_mem:.1f}MB (변동폭: {max_mem - min_mem:.1f}MB)")
            
            # GC 작동 분석
            print(f"\nGC 작동 감지: {gc_detected_count}회")
            if gc_detected_count > 0:
                gc_frequency = total_time / gc_detected_count if gc_detected_count > 0 else 0
                print(f"GC 평균 주기: {gc_frequency:.1f}분마다")
            
            # 최종 판단
            if gc_detected_count == 0:
                print("\n🚨 심각: GC가 작동하지 않음 - 메모리 누수 확실")
            elif avg_rate > leak_threshold:
                print(f"\n⚠️  경고: GC 작동 중이나 증가율 높음 ({avg_rate:+.2f}MB/분)")
                print("   → 장시간 사용 시 메모리 부족 가능")
            elif avg_rate > 0.5:
                print(f"\n📊 정상: GC 작동 중, 완만한 증가 ({avg_rate:+.2f}MB/분)")
                print("   → 정상적인 메모리 사용 패턴")
            else:
                print("\n✅ 우수: 메모리 안정적으로 관리됨")
                print("   → GC가 효과적으로 작동 중")

def show_summary():
    """현재 상태 요약"""
    proc = find_chatai_process()
    if not proc:
        print("❌ Chat AI Agent 프로세스를 찾을 수 없습니다.")
        return
    
    # 자식 프로세스 포함 메모리 계산
    children = proc.children(recursive=True)
    total_mem = proc.memory_info().rss
    for child in children:
        try:
            total_mem += child.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    total_mem_percent = (total_mem / psutil.virtual_memory().total) * 100
    
    print(f"\n📊 Chat AI Agent 상태 요약")
    print("=" * 60)
    print(f"PID:           {proc.pid}")
    print(f"상태:          {proc.status()}")
    print(f"CPU 사용률:    {proc.cpu_percent(interval=0.5):.1f}%")
    print(f"메모리 (전체): {format_bytes(total_mem)} ({total_mem_percent:.1f}%)")
    print(f"메모리 (메인): {format_bytes(proc.memory_info().rss)}")
    print(f"자식 프로세스: {len(children)}개")
    
    if children:
        print("\n자식 프로세스 목록:")
        for child in children[:10]:  # 최대 10개만 표시
            try:
                child_mem = child.memory_info().rss
                print(f"  - PID {child.pid}: {child.name()} ({format_bytes(child_mem)})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        show_summary()
    else:
        # 모니터링 간격 설정 (기본 2초)
        interval = 2
        if len(sys.argv) > 1:
            try:
                interval = int(sys.argv[1])
            except ValueError:
                pass
        monitor_process(interval)
