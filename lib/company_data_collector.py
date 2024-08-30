import requests
import pandas as pd
import json
import math
from io import StringIO

def fetch_webpage_data(company_code):
    """네이버 금융에서 기업 데이터를 가져옵니다."""
    URL = f"https://finance.naver.com/item/main.nhn?code={company_code}"
    response = requests.get(URL)
    html_string = StringIO(response.text)
    return pd.read_html(html_string)

def extract_dataframe_info(dataframe, data):
    """데이터프레임에서 정보를 추출하여 데이터 딕셔너리에 추가합니다."""
    for _, row in dataframe.iterrows():
        keys = str(row[0]).replace(' ', '').split('l')
        
        if isinstance(row[1], str):
            values = row[1].replace(' ', '').split('l')
        elif isinstance(row[1], (int, float)):
            values = [str(row[1])]
        else:
            values = ['N/A']  # 다른 타입의 경우 'N/A'로 처리
        
        if len(keys) == len(values):
            for i in range(len(keys)):
                data['company_data'][keys[i]] = values[i]
        else:
            # 키와 값의 개수가 일치하지 않을 경우
            data['company_data'][keys[0]] = values[0] if values else 'N/A'
            
    return data

def convert_to_json_safe(value):
    """값을 JSON 안전 형식으로 변환합니다."""
    if isinstance(value, float):
        if math.isnan(value):
            return None
        return str(value)  # 모든 float를 문자열로 변환하여 정밀도 유지
    return value

def collect_company_basic_info(company_code):
    """기업의 기본 정보를 수집하고 JSON 파일로 저장합니다."""
    dataframe_list = fetch_webpage_data(company_code)
    
    data = {
        'company_data': {
            '종가날짜': dataframe_list[2].iloc[1, :]['날짜'],
            '종가': dataframe_list[2].iloc[1, :]['종가']
        }
    }

    for i in [5, 6, 7, 8]:
        data = extract_dataframe_info(dataframe_list[i], data)
    
    # "액면가"와 "매매단위" 제거
    data['company_data'].pop('액면가', None)
    data['company_data'].pop('매매단위', None)

    # 데이터 구조화 함수
    def safe_get(dict_obj, key, default='N/A'):
        return dict_obj.get(key, default)

    # EPS와 BPS 키 찾기
    eps_key = next((k for k in data['company_data'] if k.startswith('EPS')), 'EPS')
    bps_key = next((k for k in data['company_data'] if k.startswith('BPS')), 'BPS')

    structured_data = {
        "company_data": {
            "market_info": {
                "종가": str(safe_get(data['company_data'], '종가')),
                "종가날짜": safe_get(data['company_data'], '종가날짜'),
                "시가총액": safe_get(data['company_data'], '시가총액'),
                "시가총액순위": safe_get(data['company_data'], '시가총액순위'),
                "상장주식수": safe_get(data['company_data'], '상장주식수')
            },
            "foreign_ownership": {
                "외국인한도주식수": safe_get(data['company_data'], '외국인한도주식수(A)'),
                "외국인보유주식수": safe_get(data['company_data'], '외국인보유주식수(B)'),
                "외국인소진율": safe_get(data['company_data'], '외국인소진율(B/A)')
            },
            "investment_metrics": {
                "투자의견": safe_get(data['company_data'], '투자의견'),
                "목표주가": safe_get(data['company_data'], '목표주가'),
                "52주최고": safe_get(data['company_data'], '52주최고'),
                "52주최저": safe_get(data['company_data'], '최저'),
                "PER": safe_get(data['company_data'], 'PER'),
                "EPS": safe_get(data['company_data'], eps_key),
                "추정PER": safe_get(data['company_data'], '추정PER'),
                "추정EPS": safe_get(data['company_data'], '추정EPS'),
                "PBR": safe_get(data['company_data'], 'PBR'),
                "BPS": safe_get(data['company_data'], bps_key),
                "배당수익률": safe_get(data['company_data'], '배당수익률')
            }
        }
    }

    with open('data/company_data.json', 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)

def collect_company_financial_info(company_code):
    """기업의 재무 정보를 수집하고 JSON 파일로 저장합니다."""
    dataframe_list = fetch_webpage_data(company_code)
    
    annual_performance_df = dataframe_list[3]['최근 연간 실적']
    annual_performance_df.columns = annual_performance_df.columns.get_level_values(0)
    
    main_financial_info = dataframe_list[3]['주요재무정보']['주요재무정보']
    combined_df = pd.concat([main_financial_info, annual_performance_df], axis=1)
    
    required_columns = ['매출액', '영업이익', '당기순이익', 'ROE(지배주주)', 'EPS(원)', 'PER(배)', 'PBR(배)', '시가배당률(%)']
    filtered_df = combined_df[combined_df['주요재무정보'].isin(required_columns)].reset_index(drop=True)

    financial_data = {
        "headers": ["항목"] + filtered_df.columns[1:].tolist(),
        "financial_data": [
            [convert_to_json_safe(item) for item in row]
            for row in filtered_df.values.tolist()
        ]
    }

    with open('data/financial_data.json', 'w', encoding='utf-8') as f:
        json.dump(financial_data, f, ensure_ascii=False, indent=2)
