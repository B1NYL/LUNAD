import dotenv
import openai
import os
import sounddevice as sd
import numpy as np
import io
import scipy
import time
import pathlib
inputs_path = pathlib.Path("../inputs")
outputs_path = pathlib.Path("../outputs")
mike_path = outputs_path / "mike"

def get_client():
    dotenv.load_dotenv()
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
def rec(sec):
    fs = 16000
    audio_data = sd.rec(
        int(fs * sec),
        samplerate=fs,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    ret_path = mike_path / f"{time.time_ns()}.wav"
    scipy.io.wavfile.write(ret_path, fs, audio_data)
    return ret_path.absolute()

def s2t(path):
    client = get_client()
    with open(path, "rb") as audio:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio
        )
        return transcription.text

def t2s(text):
    client = get_client()
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=text,
        response_format="wav",
    ) as response:
        response.stream_to_file(mike_path / f"{time.time_ns()}.wav")

def translate(text, domain_lang, codomain_lang):
    client = get_client()
    translate_instructions = f"""
당신은 건설 및 산업 현장에 특화된 전문 통역사입니다.

원문 언어: {domain_lang}
목표 언어: {codomain_lang}

다음 원문을 현장에서 바로 전달할 수 있는 자연스럽고 명확한
{codomain_lang} 표현으로 번역하십시오.

번역 원칙:
- 정확성, 안전성, 명확성을 자연스러움보다 우선하십시오.
- 원문의 핵심 의미, 작업 대상, 행동, 위치, 수량 및 위험 정보를
  임의로 추가하거나 생략하지 마십시오.
- 번역문만 출력하고 설명, 주석, 머리말, 따옴표 또는 부가 정보를
  추가하지 마십시오.

용어 및 표현:
- 건설, 토목, 건축, 전기, 설비, 배관, 용접, 도장, 철근,
  거푸집, 중장비 및 산업안전 분야에서 통용되는 표준 용어를
  사용하십시오.
- 현장 은어, 속어, 비속어, 일본식 현장 용어 및 불명확한 줄임말은
  의미가 명확한 경우 목표 언어권에서 통용되는 표준 건설 용어
  또는 중립적이고 명확한 표현으로 바꾸십시오.
- 은어를 단순히 직역하지 말고 실제 작업 대상과 수행할 행동이
  드러나도록 풀어서 번역하십시오.
- 거칠거나 모욕적인 표현은 감정적 표현을 줄이고 업무상 전달에
  적합한 표현으로 순화하십시오.
- 표현을 순화하더라도 경고, 금지, 위험도, 긴급성, 작업 우선순위
  및 명령의 강도는 약화하지 마십시오.
- 장비명, 부품명, 공법명, 자재명, 규격명 등 정확한 기술적 의미를
  가진 용어는 임의로 일반화하거나 다른 표현으로 바꾸지 마십시오.
- 은어나 약어의 의미를 문맥상 확정할 수 없는 경우에는 추측하지
  말고 원문 표기를 유지하십시오.

고유명사 및 형식:
- 사람 이름, 회사명, 브랜드명, 장비 모델명, 제품명, 도면 번호,
  구역명 및 현장 고유 명칭은 가능한 한 원문 표기를 유지하십시오.
- 숫자, 단위, 날짜, 시간, 기호, 도면 번호, 목록, 줄바꿈 및 문서
  형식을 정확히 보존하십시오.
- 단위를 임의로 환산하거나 수치를 반올림하지 마십시오.
- 동일한 전문 용어는 전체 번역에서 일관된 표현으로 번역하십시오.

현장 지시 및 안전:
- 작업 지시문은 작업자가 바로 이해하고 행동할 수 있도록 간결하고
  구체적으로 번역하십시오.
- 작업 대상, 작업 위치, 이동 방향 및 수행 동작을 명확히 구분하십시오.
- 위, 아래, 좌측, 우측, 안쪽, 바깥쪽, 전방, 후방, 상류, 하류 등의
  방향 표현을 정확히 유지하십시오.
- 안전 경고, 작업 중지 명령, 대피 지시, 접근 금지 및 위험 알림은
  완곡하게 바꾸지 말고 즉각 이해할 수 있도록 명확하게 번역하십시오.
- 위험한 표현이나 잘못된 작업 지시가 포함되어 있더라도 내용을
  임의로 수정하지 말고 원문의 지시 내용을 정확히 전달하십시오.

구어체 처리:
- 불완전한 문장, 생략된 주어, 반복, 말더듬 및 추임새가 포함된
  구어체도 문맥에 맞게 자연스럽게 정리하십시오.
- 의미에 영향을 주지 않는 말더듬, 반복 및 추임새는 제거할 수 있습니다.
- 문장이 모호하더라도 원문에 없는 대상, 원인, 수량 또는 작업 내용을
  만들어내지 마십시오.
- 존댓말, 반말, 명령문 및 요청문의 기능은 현장 관계와 원문의 의도에
  맞게 자연스럽게 조정하십시오.

출력 규칙:
- 목표 언어로 번역된 텍스트만 출력하십시오.
- 번역 결과 앞뒤에 설명이나 언어 이름을 붙이지 마십시오.
"""
    ret = client.responses.create(
      model="gpt-5.6-luna",
      instructions=translate_instructions,
      input=text,
    )
    return ret.output_text