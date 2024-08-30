import os
import json
import base64
from jinja2 import Template
from datetime import datetime
from PIL import Image
import io

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def image_to_base64(image_path, quality=95):
    if not os.path.exists(image_path):
        print(f"Image file {image_path} does not exist.")
        return ""
    with Image.open(image_path) as img:
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=quality)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
def generate_html(output_path, include_graphs=False):
    # JSON 파일 로드
    analyst_data = load_json('data/analyst_data.json')
    company_data = load_json('data/company_data.json')
    financial_data = load_json('data/financial_data.json')
    report_data = load_json('data/report_data.json')
    summary_data = load_json('data/summary_data.json')
    
    # 로고 이미지를 Base64로 인코딩
    logo_path = 'static/image/kb_logo.png'
    logo_base64 = image_to_base64(logo_path)

    # 갤러리 이미지 로드 및 Base64 인코딩 (include_graphs가 True일 때만)
    if include_graphs:
        gallery_folder = 'static/image/gallery'
        for section in report_data['report_content']:
            if 'tag' in section:
                section['images'] = []
                for image_file in section['tag'].split(','):
                    image_path = os.path.join(gallery_folder, image_file.strip())
                    image_base64 = image_to_base64(image_path)
                    if image_base64:
                        section['images'].append(image_base64)
    else:
        # 그래프를 포함하지 않을 경우, 이미지 관련 데이터 제거
        for section in report_data['report_content']:
            if 'tag' in section:
                del section['tag']
            if 'images' in section:
                del section['images']

    # index.html 템플릿 로드
    with open('static/index.html', 'r', encoding='utf-8') as file:
        template_content = file.read()

    # Jinja2 템플릿 생성
    template = Template(template_content)

    # HTML 생성
    html_content = template.render(
        analystData=analyst_data,
        companyData=company_data,
        financialData=financial_data,
        reportData=report_data,
        summaryData=summary_data,
        currentDate=datetime.now().strftime("%Y-%m-%d"),
        logoBase64=logo_base64,
        includeGraphs=include_graphs,  # 템플릿에 그래프 포함 여부 전달
    )

    # HTML 파일 저장
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

if __name__ == "__main__":
    generate_html('output/report.html', include_graphs=True)