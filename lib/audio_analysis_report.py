import os
import json
import openai
import time
from dotenv import load_dotenv
from pydub import AudioSegment
from tenacity import retry, wait_random_exponential, stop_after_attempt
import base64
import requests
import re
import yt_dlp

load_dotenv()

def split_audio(file_path, chunk_size=20*1024*1024):  # 20MB in bytes
    audio = AudioSegment.from_mp3(file_path)
    duration = len(audio)
    chunks = []

    file_size = os.path.getsize(file_path)
    bytes_per_millisecond = file_size / duration
    
    chunk_length_ms = int(chunk_size / bytes_per_millisecond)

    os.makedirs('chunks', exist_ok=True)
    for i in range(0, duration, chunk_length_ms):
        chunk = audio[i:i+chunk_length_ms]
        chunk_path = os.path.join('chunks', f"chunk_{i}.mp3")
        chunk.export(chunk_path, format="mp3")
        chunks.append(chunk_path)
    return chunks

def transcribe_audio(audio_chunk_path):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            with open(audio_chunk_path, 'rb') as audio_file:
                response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language='ko',
                )
            
            return response['text']
        except openai.error.RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(20)  # Wait for 20 seconds before retrying
            else:
                raise
        except Exception as e:
            print(f"Transcription failed on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                raise

def llm_answer_request(instruction, prompt, model='gpt-4o'):

    messages = [{"role": "system", "content": instruction},
                {"role": "user", "content": prompt}]

    response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0,
            response_format= {"type": "json_object"}
        )

    output_text = response['choices'][0]['message']['content'].replace("\'", '')
    return output_text

def read_instruction(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        instruction = file.read()
    return instruction

@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(10))
def keyword_extraction(script, synonym_dict, model='gpt-4o'):
    instruction = read_instruction('prompt/prompt_fnl.txt')
    input_json = {"script" : script, "synonym_dict" : synonym_dict}
    
    prompt = f"""
    {input_json}

    * Output
    """
    res = llm_answer_request(instruction, prompt, model=model)
    ans = json.loads(res)

    return ans

@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(10))
def stt_image_text_matching(stt_results, image_text_results, model='gpt-4o'):
    instruction = read_instruction('prompt/prompt_tag.txt')
    input_json = {
        "stt_results": stt_results,
        "image_text_results": image_text_results
    }
    
    prompt = f"""
    {json.dumps(input_json, ensure_ascii=False, indent=2)}

    * Output
    """
    res = llm_answer_request(instruction, prompt, model=model)
    ans = json.loads(res)

    return ans

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def image_to_text(image_path):
    # Getting the base64 string
    base64_image = encode_image(image_path)

    openai.api_key = os.getenv("OPENAI_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an expert in creating corporate reports. Rather than focusing on specific data or figures in the image, analyze and emphasize the main themes and subjects covered. Based on this analysis, draft a complete paragraph in Korean for the corporate report. Your paragraph should identify and explain the overall topic and key subjects of the image, interpreting general trends or significance rather than mentioning specific numbers or data. Use natural, flowing language to create a cohesive narrative. The paragraph should be well-organized and ready for inclusion in the report without further edits. If any English terms are present, use them as is. Construct sentences that end specifically with '-다', avoiding any sentences ending in '-습니다/-합니다'. This is crucial work, so proceed thoughtfully. Provide insightful analysis of the main themes and subjects after comprehensively assessing the provided image. The output limit is 500 tokens."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        # "max_tokens": 300
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response_json = response.json()
        if 'choices' in response_json:
            description = response_json['choices'][0]['message']['content']
        else:
            print("Unexpected response structure:", response_json)
            description = "No description available."
    except KeyError as e:
        print(f"KeyError: {e}")
        description = "Error: 'choices' not found in the response."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        description = "An error occurred while processing the request."
    
    return description

def add_paragraph_breaks(text, sentences_per_paragraph=2):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    paragraphs = []
    for i in range(0, len(sentences), sentences_per_paragraph):
        paragraph = ' '.join(sentences[i:i+sentences_per_paragraph])
        paragraphs.append(paragraph)
    return '\n\n'.join(paragraphs)

def process_content_list(content_list, sentences_per_paragraph=2):
    processed_list = []
    for item in content_list:
        processed_item = item.copy()
        processed_item['content'] = add_paragraph_breaks(item['content'], sentences_per_paragraph)
        processed_list.append(processed_item)
    return processed_list

# 처리된 결과 출력


def process_audio_file(file_path):
    try:
        print("Splitting audio into chunks...")
        audio_chunks = split_audio(file_path)

        with open('prompt/synonym_dict.txt', 'r', encoding='utf-8') as file:
            synonym_dict = file.read()
        synonym_dict = "{\n" + synonym_dict + "\n}"
        
        full_transcript = ""
        
        for i, chunk_path in enumerate(audio_chunks):
            print(f"Processing chunk {i+1}/{len(audio_chunks)}...")
            chunk_transcript = transcribe_audio(chunk_path)
            full_transcript += chunk_transcript + "\n\n"

        with open('output/stt_result.txt', 'w', encoding='utf-8') as file:
            file.write(full_transcript)

        pdf_folder = 'static/image/gallery'
        pdf_path = os.listdir(pdf_folder)

        image_description = {}
        for path in pdf_path:
            image_path = os.path.join(pdf_folder, path)
            text = image_to_text(image_path)
            image_description[path] = text

        print(f"Processing summary...")
        full_summary = keyword_extraction(full_transcript, synonym_dict)

        # stt_results = full_summary['key_summary'] 
        # updated_stt_results = stt_image_text_matching(stt_results, image_description)
        processed_data = process_content_list(full_summary['top_three_topic'], sentences_per_paragraph=2)

        result = {
            "report_content": full_summary["key_summary"]
        }
        corperate_report = {
            'summary' : full_summary['headline'],
            'key_points' : processed_data
        }

        return result, corperate_report
    except Exception as e:
        print(f"Processing failed: {str(e)}")
        raise


def sanitize_filename(filename):
    # 파일명에 사용할 수 없는 문자들을 제거합니다.
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def clean_title(title):
    # 제목에서 빨간 동그라미 이모지를 제거하고 대괄호 안의 텍스트만 추출합니다.
    title = title.replace('🔴', '')  # 빨간 동그라미 이모지 제거
    match = re.search(r'\[(.*?)\]', title)
    if match:
        return match.group(1)
    return title

def download_youtube_audio(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path + '/%(title)s.%(ext)s',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        title = info_dict.get('title', 'audio')
        
        # 제목에서 빨간 동그라미 이모지를 제거하고 대괄호 안의 내용을 추출합니다.
        new_title = clean_title(title)
        new_title = sanitize_filename(new_title)
        new_filename = f"{new_title}"
        ydl_opts['outtmpl'] = os.path.join(output_path, new_filename)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return ydl_opts['outtmpl']['default'] + ".mp3"

output_path = "./mp3/당잠사"  # MP3 파일을 저장할 경로


def generate_report(url):
    output_mp3_path = download_youtube_audio(url, output_path)
    original_result, corperate_report = process_audio_file(output_mp3_path)

    # Save the original result to a JSON file
    original_output_file_path = "data/report_data.json"
    with open(original_output_file_path, 'w', encoding='utf-8') as f:
        json.dump(original_result, f, ensure_ascii=False, indent=2)

    # Save the Corperate-style report to a new JSON file
    corperate_output_file_path = "data/summary_data.json"
    with open(corperate_output_file_path, 'w', encoding='utf-8') as f:
        json.dump(corperate_report, f, ensure_ascii=False, indent=2)

    print("Processing completed.")
    print(f"Original result saved to {original_output_file_path}")
    print(f"Corperate report saved to {corperate_output_file_path}")
