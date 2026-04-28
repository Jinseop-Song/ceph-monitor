import time
import json
import requests
import subprocess
import re
from datetime import datetime

# 터미널 명령어를 실행하고 결과를 텍스트로 반환하는 함수
def run_cli_command(cmd_list):
    try:
        # shell=False가 보안상 좋으므로 리스트 형태로 전달
        result = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT, encoding='utf-8')
        return result
    except subprocess.CalledProcessError as e:
        return f"CLI Error: {e.output}"
    except Exception as e:
        return f"Unexpected CLI Error: {str(e)}"

# 바이트를 기가바이트로 변환하는 함수
def bytes_to_gigabytes(bytes_value):
    return bytes_value / (1024 ** 3)

# Ceph Health 상태를 조회하는 함수
def get_pg_status(active_mgr_ip, token_headers):
    health_url = f"https://{active_mgr_ip}:8443/api/health/minimal"
    try:
        health_response = requests.get(health_url, headers=token_headers, verify=False, timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            pg_details = health_data.get('pg_info', {}).get('statuses', {})
            if pg_details:
                return ', '.join([f"{value} PGs - {key}" for key, value in pg_details.items()])
            return "No PG info available"
    except:
        pass
    return "API Error (PG Status)"

# Ceph Capacity 정보를 조회하는 함수
def get_cluster_capacity(active_mgr_ip, token_headers):
    capacity_url = f"https://{active_mgr_ip}:8443/api/health/get_cluster_capacity"
    try:
        capacity_response = requests.get(capacity_url, headers=token_headers, verify=False, timeout=5)
        if capacity_response.status_code == 200:
            capacity_data = capacity_response.json()
            return (
                bytes_to_gigabytes(capacity_data.get('total_avail_bytes', 0)),
                bytes_to_gigabytes(capacity_data.get('total_bytes', 0)),
                bytes_to_gigabytes(capacity_data.get('total_used_raw_bytes', 0))
            )
    except:
        pass
    return None, None, None

# OSD 상태를 조회하는 함수
def get_osd_status(active_mgr_ip, token_headers):
    osd_status_url = f"https://{active_mgr_ip}:8443/api/health/minimal"
    try:
        osd_status_response = requests.get(osd_status_url, headers=token_headers, verify=False, timeout=5)
        if osd_status_response.status_code == 200:
            osd_data = osd_status_response.json()
            osd_map = osd_data.get("osd_map", {}).get("osds", [])
            osd_in_count = sum(1 for osd in osd_map if osd.get("in") == 1)
            osd_up_count = sum(1 for osd in osd_map if osd.get("up") == 1)
            return osd_in_count, osd_up_count
    except:
        pass
    return None, None

# Main 함수 (more_info 생성)
def main(active_mgr_ip, token_headers):
    # 1. API 기반 숫자 데이터 수집 (알람 요약용)
    pg_info_str = get_pg_status(active_mgr_ip, token_headers)
    total_avail_gb, total_gb, total_used_raw_gb = get_cluster_capacity(active_mgr_ip, token_headers)
    osd_in_count, osd_up_count = get_osd_status(active_mgr_ip, token_headers)

    # 2. CLI 기반 원본 텍스트 수집 (스레드 상세 로그용)
    # 터미널에서 치던 그 맛 그대로 긁어옵니다.
    health_detail_raw = run_cli_command(["ceph", "health", "detail"])
    osd_df_raw = run_cli_command(["ceph", "osd", "df", "tree"]) # df tree로 더 자세하게!

    # 3. 데이터 패키징
    return {
        "pg_info_str": pg_info_str,
        "total_avail_gb": total_avail_gb or 0,
        "total_gb": total_gb or 1,
        "total_used_raw_gb": total_used_raw_gb or 0,
        "osd_in_count": osd_in_count or 0,
        "osd_up_count": osd_up_count or 0,
        # [추가] 터미널 커맨드 데이터
        "health_detail_raw": health_detail_raw,
        "osd_df_raw": osd_df_raw
    }

if __name__ == "__main__":
    # 테스트용 (실제 실행 시에는 main.py에서 호출)
    # headers = {"Authorization": "Bearer ..."}
    # print(main("10.110.0.105", headers))
    pass