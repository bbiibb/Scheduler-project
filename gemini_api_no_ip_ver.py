# -*- coding: utf-8 -*-

#pip install google-generativeai

import google.generativeai as genai
import json
import os

GOOGLE_API_KEY = "API키"  # 실제 API 키로 교체하세요.
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

characters = {
    "easy": "너는 친근하고 가벼운 말투의 비서야. 사용자를 격려하는 말투로 간단하고 따뜻하게 대화해.",
    "hard": "너는 엄격한 말투의 비서야. 효율적이고 명확한 답변을 제공하며 사용자가 루틴을 지키도록 꼼꼼히 관리해. 불필요한 대화는 피하고 핵심만 전달해"
}

# 대화 기록과 요약
history = []
summary = ""
routine_check = True
character_mode = "easy"

# 대화 요약 함수
def summarize_history(old_history):
    text = "\n".join([f"User: {turn['user']}\nAssistant: {turn['assistant']}" for turn in old_history])
    prompt = f"다음 대화를 3줄로 요약해줘:\n{text}"
    response = model.generate_content(prompt)
    return response.text.strip()

# 프롬프트 빌더
def build_prompt(user_input, history, summary, character_prompt, routine_check):
    base_instructions = f"""
{character_prompt} 모드로 할게.
너는 일정과 루틴을 관리하는 한국어 비서야.
출력은 자연어 문장으로 한다.
아래의 요약과 최근 대화를 참고해서 답해
출력은 표준화된 형식을 따르고, ✅ 일정은 리스트 형식 (예: - 08:00 운동)
사용자 입력을 이해해서 일정 관리에 도움이 되는 말을 해
스케줄링 관련 대화엔, 테스크의 예상 소요시간을 제시하고 소요시간 및 중요도를 고려해서 적절히 분배해줘
사용자의 발화에 일정이 포함되면, 일정 시작 / 종료 시간을 구체적으로 정리하도록 해
일정에 '장소'가 언급된 경우, 장소 이동 시간을 반드시 고려하여 일정을 자동으로 조정해.
 - 기본 규칙 : 같은 지역 (캠퍼스 내부, 집 앞 상가)은 10분, 서울 주요 도심간 이동은 50분 가량으로 설정해
 사용자가 직접 이동시간을 말하지 않아도 비서가 스스로 합리적인 이동시간을 넣도록 해
공부나 일을 하는 스케줄인 경우엔, 반드시 중간에 쉬는시간을 삽입하도록 해.


기능:
1. 루틴 체크 기능 (on/off): on이면 상담사가 사용자의 루틴 여부를 묻는다.
2. 사용자가 루틴을 안 했다고 하면 "내일로 미뤄드릴까요?"라고 제안한다.
3. 사용자가 "내일로 미뤄줘"라고 하면 내일 같은 시간으로 옮겼다고 답한다.
4. 사용자가 "루틴 등록"을 요청하면 루틴 추가 완료 메시지를 제공한다.
5. 일정은 명확하게 설명한다. (예: "내일 오전 8시 운동 일정이 등록되었습니다.")
"""
    if not routine_check:
        base_instructions += "\n현재 루틴 체크는 off 상태이므로 루틴 여부를 묻지 않는다.\n"

    conversation = f"<system>\n{base_instructions}\n\n"
    conversation += f"[대화 요약]\n{summary}\n\n"
    conversation += "[최근 대화]\n"
    for turn in history[-5:]:
        conversation += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"
    conversation += f"User: {user_input}\nAssistant:"
    return conversation


# 채팅 함수
def chat(user_input, character_mode, routine_check):
    global history, summary
    #오래된 히스토리 요약
    if len(history) > 5:
        summary = summarize_history(history[:-5])
        history = history[-5:]

    character_prompt = characters.get(character_mode, characters["easy"])
    #캐릭터 선택
    prompt = build_prompt(user_input, history, summary, character_prompt, routine_check)
    response = model.generate_content(prompt)

    answer = response.text.strip()
    history.append({"user": user_input, "assistant": answer})
    return answer

# 실행 예시
if __name__ == "__main__":
    character_mode = input("상담사 모드 선택 (easy/hard): ").strip()
    if character_mode not in characters:
        character_mode = "easy"
    print(f"{character_mode} 모드 상담사를 시작합니다. (종료: exit, 루틴체크 on/off 가능)")

    while True:
        user_input = input("나: ")
        if user_input.lower() in ["exit", "quit", "종료"]:
            print("대화를 종료합니다.")
            break
        elif "루틴체크 off" in user_input.lower():
            routine_check = False
            print("루틴 체크 기능을 끕니다.")
            continue
        elif "루틴체크 on" in user_input.lower():
            routine_check = True
            print("루틴 체크 기능을 켭니다.")
            continue

        answer = chat(user_input, character_mode, routine_check)
        print(f"상담사: {answer}")