import time
import json
import requests
import subprocess
import pandas as pd
from datetime import datetime

def get_osd_df(active_mgr_ip, token_heders):
    osd_df_url = f"https://{active_mgr_ip}:8443/api/osd"
    try:
        osd_df_response = requests.get(osd_df_url, headers=token_heders, verify=False, timeout=5)
        if osd_df_response.status_code == 200:
            osd_df_raw_data = osd_df_response.json()
        refined_data = []
        for osd in osd_df_raw_data:
            stats = osd.get('osd_stats', {})
            kb = stats.get('kb', 0)
            kb_used = stats.get('kb_used', 0)
            
            refined_data.append({
                'id': osd.get('id'),
                'status': osd.get('state', ['unknown', 'unknown'])[1],
                'crush_weight': osd.get('tree', {}).get('crush_weight', 0.0),
                'percent_use': (kb_used / kb * 100) if kb > 0 else 0.0
            })
            
            # 리스트를 데이터프레임으로 변환하여 반환
            return pd.DataFrame(refined_data)
    except Exception as e:
        print(f"OSD API Error: {e}")
    
    # 에러 발생 시 빈 데이터프레임 반환
    return pd.DataFrame()

def bytes_to_gigabytes(bytes_value):
    return bytes_value / (1024 ** 3)
# def get_health_full(active_mgr_ip, token_heders):
#     health_full_url = f"https://{active_mgr_ip}:8443/api/health/full"
#     try:
#         health_full_response = requests.get(health_full_url, headers=token_heders, verify=False, timeout=5)
#         if health_full_response.status_code == 200:
#             health_full_data = health_full_response.json()
        

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
    osd_df = get_osd_df(active_mgr_ip, token_headers)

    # 3. 데이터 패키징
    return {
        "pg_info_str": pg_info_str,
        "total_avail_gb": total_avail_gb or 0,
        "total_gb": total_gb or 1,
        "total_used_raw_gb": total_used_raw_gb or 0,
        "osd_in_count": osd_in_count or 0,
        "osd_up_count": osd_up_count or 0,
        "osd_df": osd_df,
        # "health_detail_raw": health_detail_raw
        }

if __name__ == "__main__":
    # 테스트용 (실제 실행 시에는 main.py에서 호출)
    # headers = {"Authorization": "Bearer ..."}
    # print(main("10.110.0.105", headers))
    pass