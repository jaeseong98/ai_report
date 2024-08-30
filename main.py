import argparse
from lib import audio_analysis_report
from lib import company_data_collector
from lib import html_generator
from datetime import datetime
import os

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == '__main__':
    # 명령줄 인자 파서 설정
    parser = argparse.ArgumentParser(description='Generate company report with optional graph inclusion.')
    parser.add_argument('--graph', action='store_true', help='Include graphs in the report')
    parser.add_argument('--url', type=str, required=True, help='Path to the youtube for analysis')
    parser.add_argument('--company_code', type=str, default='051910', help='Company code (default: 051910 for LG화학)')
    args = parser.parse_args()

    # 결과물을 저장할 디렉토리 생성
    output_dir = 'output'
    ensure_directory_exists(output_dir)
    
    audio_analysis_report.generate_report(args.url)
    print("레포트 요약이 완료되었습니다.")
    
    company_data_collector.collect_company_basic_info(args.company_code)
    company_data_collector.collect_company_financial_info(args.company_code)
    print("데이터 수집 및 저장이 완료되었습니다.")
    
    # HTML 파일 생성
    html_path = os.path.join(output_dir, f'{datetime.now().strftime("%Y-%m-%d")}_report.html')
    html_generator.generate_html(html_path, include_graphs=args.graph)
    print(f"HTML 보고서가 생성되었습니다: {html_path}")

    print("모든 작업이 완료되었습니다.")