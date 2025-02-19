import logging
from typing import Optional, List, Dict, Any
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_core.example_selectors import LengthBasedExampleSelector

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

EXAMPLE_TEMPLATE = "입력: {input}\n출력: {output}"

def generate_input_string(case: str, insight_number: int, data: Dict[str, Any]) -> str:
    try:
        if case == "one_week":
            if insight_number == 1:
                return f"현재 미세먼지 농도: {int(round(data['pm_current'], 0))}, 이번주 평균 미세먼지 농도: {int(round(data['pm_this_week'], 0))}"
            elif insight_number == 2:
                return f"이번주 미세먼지 농도: {int(round(data['pm_this_week'], 0))}"
            elif insight_number == 3:
                this_week_clean_time = int(round(sum(data['averageCleanTime'][1]), 0))
                return f"이번주 총 공기 정화 시간: {this_week_clean_time}"
            elif insight_number == 4:
                this_week_clean_amount = int(round(sum(data['averageCleanAmount'][1]), 0))
                return f"이번주 총 공기 정화량: {this_week_clean_amount}"
        
        elif case == "two_week":
            if insight_number == 1:
                return f"현재 미세먼지 농도: {int(round(data['pm_current'], 0))}, 이번주 평균 미세먼지 농도: {int(round(data['pm_this_week'], 0))}"
            elif insight_number == 2:
                last_week_pm_values = [float(value) for value in data['averagePm'][0] if isinstance(value, (int, float))]
                last_week_pm = int(round(sum(last_week_pm_values) / len(last_week_pm_values), 0)) if last_week_pm_values else 0
                return f"이번주 미세먼지 농도: {int(round(data['pm_this_week'], 0))}, 저번주 미세먼지 농도: {last_week_pm}"
            elif insight_number == 3:
                this_week_clean_time = int(round(sum(data['averageCleanTime'][1]), 0))
                last_week_clean_time = int(round(sum(data['averageCleanTime'][0]), 0))
                return f"이번주 총 공기 정화 시간: {this_week_clean_time}, 저번주 총 공기 정화 시간: {last_week_clean_time}"
            elif insight_number == 4:
                this_week_clean_amount = int(round(sum(data['averageCleanAmount'][1]), 0))
                last_week_clean_amount = int(round(sum(data['averageCleanAmount'][0]), 0))
                return f"이번주 총 공기 정화량: {this_week_clean_amount}, 저번주 총 공기 정화량: {last_week_clean_amount}"
    except KeyError as e:
        logger.error(f"Missing key in data dictionary: {e}")
    except TypeError as e:
        logger.error(f"Data type error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in generate_input_string: {e}")
    return ""

def generate_prefix_string(case: str, insight_number: int) -> str:
    try:
        if case == "one_week":
            if insight_number == 1:
                return f"출력은 반드시 '현재 미세먼지 농도가 ___로 이번주 평균 미세먼지 농도보다 높습니다/낮습니다/비슷합니다' 형식을 따라야 합니다.\n"
            elif insight_number == 2:
                return f"출력은 반드시 '이번주 평균 미세먼지 농도는 ___입니다' 형식을 따라야 합니다.\n"
            elif insight_number == 3:
                return f"출력은 반드시 '이번주 총 공기 정화 시간은 ___시간입니다' 형식을 따라야 합니다.\n"
            elif insight_number == 4:
                return f"출력은 반드시 '이번주 총 공기 정화량은 ___입니다' 형식을 따라야 합니다.\n"
        
        elif case == "two_week":
            if insight_number == 1:
                return f"출력은 반드시 '현재 미세먼지 농도가 ___로 이번주 평균 미세먼지 농도보다 높습니다/낮습니다/비슷합니다' 형식을 따라야 합니다.\n"
            elif insight_number == 2:
                return f"출력은 반드시 '이번주 평균 미세먼지 농도는 ___로 저번주 미세먼지 농도 ___ 대비 __% 높습니다/낮습니다/비슷합니다' 형식을 따라야 합니다.\n"
            elif insight_number == 3:
                return f"출력은 반드시 '이번주 총 공기 정화 시간은 ___시간으로 저번주 총 공기 정화 시간 ___ 대비 __% 증가했습니다/감소했습니다/비슷합니다' 형식을 따라야 합니다.\n"
            elif insight_number == 4:
                return f"출력은 반드시 '이번주 총 공기 정화량은 ___로 저번주 총 공기 정화량 ___ 대비 __% 증가했습니다/감소했습니다/비슷합니다' 형식을 따라야 합니다.\n"
    except KeyError as e:
        logger.error(f"Missing key in data dictionary: {e}")
    except TypeError as e:
        logger.error(f"Data type error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in generate_input_string: {e}")
    return ""

def generate_fewshot_prompt(data: Dict[str, Any], case: str, insight_number: int) -> Optional[FewShotPromptTemplate]:
    if case == "no_data":
        return None
        
    try:
        examples = generate_examples(case, insight_number)
        input_string = generate_input_string(case, insight_number, data)
        prefix_string = generate_prefix_string(case, insight_number)
        
        if not input_string:
            logger.warning(f"Empty input string generated for case {case}, insight {insight_number}")
            return None
        
        example_prompt = PromptTemplate(
            input_variables=["input", "output"],
            template=EXAMPLE_TEMPLATE
        )
        
        example_selector = LengthBasedExampleSelector(
            examples=examples,
            example_prompt=example_prompt,
            max_length=2000
        )

        few_shot_prompt = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=example_prompt,
            # prefix=(
            #     "당신의 역할은 주어진 예시를 그대로 따라, 주어진 단어와 문장구조로 요약을 생성하는 것입니다.\n"
            #     + prefix_string +
            #     "추가적인 단어나 설명은 반드시 제외하세요.\n"
            #     "아래 예시들을 참고하여 결과를 생성하세요."
            # ),
            prefix=(
                "당신의 역할은 주어진 예시를 그대로 따라, 동일한 단어와 문장구조로 요약을 생성하는 것입니다.\n"
                "출력은 반드시 아래 예시와 동일한 형식, 단어, 구문을 사용하여 한 문장으로 작성되어야 합니다. "
                "추가적인 단어나 설명은 반드시 제외하세요.\n"
                "아래 예시들을 참고하여 결과를 생성하세요.\n"
            ),

            suffix="\n모델추론결과\n입력: {input}\n출력:",
            input_variables=["input"]
        )
        
        final_prompt = few_shot_prompt.format(input=input_string)
        print("\n\n\n")
        print(str(insight_number) + ". 프 롬 프 트")
        print(str(final_prompt))
        print("\n")
        return str(final_prompt)

    except Exception as e:
        logger.error(f"Error generating few-shot prompt: {e}")
        return None

def generate_examples(case: str, insight_number: int) -> List[Dict[str, str]]:
    examples = []
    
    if case == "one_week":
        variations = {
            1: [
                (10, 23, "현재 미세먼지 농도가 10으로 이번주 평균 미세먼지 농도보다 낮습니다."),
                (55, 45, "현재 미세먼지 농도가 55로 이번주 평균 미세먼지 농도보다 높습니다."),
                (30, 31, "현재 미세먼지 농도가 30으로 이번주 평균 미세먼지 농도와 비슷합니다."),
                (23, 32, "현재 미세먼지 농도가 23으로 이번주 평균 미세먼지 농도 대비 낮습니다."),
                (40, 35, "현재 미세먼지 농도가 40으로 이번주 평균 미세먼지 농도보다 높습니다.")
            ],
            2: [
                (45, "이번주 평균 미세먼지 농도는 45입니다."),
                (32, "이번주 평균 미세먼지 농도는 32입니다."),
                (55, "이번주 평균 미세먼지 농도는 55입니다."),
                (28, "이번주 평균 미세먼지 농도는 28입니다."),
                (40, "이번주 평균 미세먼지 농도는 40입니다.")
            ],
            3: [
                (19, "이번주 총 공기 정화 시간은 19시간입니다."),
                (24, "이번주 총 공기 정화 시간은 24시간입니다."),
                (15, "이번주 총 공기 정화 시간은 15시간입니다."),
                (30, "이번주 총 공기 정화 시간은 30시간입니다."),
                (22, "이번주 총 공기 정화 시간은 22시간입니다.")
            ],
            4: [
                (18, "이번주 총 공기 정화량은 18입니다."),
                (25, "이번주 총 공기 정화량은 25입니다."),
                (15, "이번주 총 공기 정화량은 15입니다."),
                (30, "이번주 총 공기 정화량은 30입니다."),
                (22, "이번주 총 공기 정화량은 22입니다.")
            ]
        }
        
        for example_values in variations[insight_number]:
            if insight_number == 1:
                current, avg, output = example_values
                example = {
                    "input": f"현재 미세먼지 농도: {current}, 이번주 평균 미세먼지 농도: {avg}",
                    "output": output.strip()
                }
            else:
                value, output = example_values
                if insight_number == 2:
                    example = {"input": f"이번주 미세먼지 농도: {value}", "output": output.strip()}
                elif insight_number == 3:
                    example = {"input": f"이번주 총 공기정화시간: {value}", "output": output.strip()}
                else:
                    example = {"input": f"이번주 총 공기정화량: {value}", "output": output.strip()}
            examples.append(example)
            
    elif case == "two_week":
        variations = {
            1: [
                (10, 19, "현재 미세먼지 농도가 10으로 이번주 평균 미세먼지 농도보다 낮습니다."),
                (45, 32, "현재 미세먼지 농도가 45로 이번주 평균 미세먼지 농도보다 높습니다."),
                (30, 30, "현재 미세먼지 농도가 30으로 이번주 평균 미세먼지 농도와 비슷합니다."),
                (15, 23, "현재 미세먼지 농도가 15로 이번주 평균 미세먼지 농도 대비 낮습니다."),
                (60, 35, "현재 미세먼지 농도가 60으로 이번주 평균 미세먼지 농도보다 높습니다.")
            ],
            2: [
                (45, 40, "이번주 평균 미세먼지 농도는 45로 저번주 미세먼지 농도 40 대비 12% 증가했습니다"),
                (35, 40, "이번주 평균 미세먼지 농도는 35로 저번주 미세먼지 농도 40 대비 13% 감소했습니다"),
                (40, 40, "이번주 평균 미세먼지 농도는 40으로 저번주 미세먼지 농도와 비슷합니다"),
                (50, 35, "이번주 평균 미세먼지 농도는 50으로 저번주 미세먼지 농도 35 대비 43% 증가했습니다"),
                (30, 45, "이번주 평균 미세먼지 농도는 30으로 저번주 미세먼지 농도 45 대비 33% 감소했습니다")
            ],
            3: [
                (19, 15, "이번주 총 공기정화시간은 19시간으로 저번주 총 공기정화시간 15시간 대비 27% 증가했습니다"),
                (12, 15, "이번주 총 공기정화시간은 12시간으로 저번주 총 공기정화시간 15시간 대비 20% 감소했습니다"),
                (15, 15, "이번주 총 공기정화시간은 15시간으로 저번주 총 공기정화시간과 비슷합니다"),
                (25, 18, "이번주 총 공기정화시간은 25시간으로 저번주 총 공기정화시간 18시간 대비 39% 증가했습니다"),
                (10, 16, "이번주 총 공기정화시간은 10시간으로 저번주 총 공기정화시간 16시간 대비 38% 감소했습니다")
            ],
            4: [
                (18, 15, "이번주 총 공기정화량은 18로 저번주 총 공기정화량 15 대비 20% 증가했습니다"),
                (12, 15, "이번주 총 공기정화량은 12로 저번주 총 공기정화량 15 대비 20% 감소했습니다"),
                (15, 15, "이번주 총 공기정화량은 15로 저번주 총 공기정화량과 비슷합니다"),
                (25, 18, "이번주 총 공기정화량은 25로 저번주 총 공기정화량 18 대비 39% 증가했습니다"),
                (10, 16, "이번주 총 공기정화량은 10으로 저번주 총 공기정화량 16 대비 38% 감소했습니다")
            ]
        }
        
        for example_values in variations[insight_number]:
            if insight_number == 1:
                current, avg, output = example_values
                example = {
                    "input": f"현재 미세먼지 농도: {current}, 이번주 평균 미세먼지 농도: {avg}",
                    "output": output.strip()
                }
            else:
                this_week, last_week, output = example_values
                if insight_number == 2:
                    example = {
                        "input": f"이번주 미세먼지 농도: {this_week}, 저번주 미세먼지 농도: {last_week}",
                        "output": output.strip()
                    }
                elif insight_number == 3:
                    example = {
                        "input": f"이번주 총 공기 정화 시간: {this_week}, 저번주 총 공기 정화 시간: {last_week}",
                        "output": output.strip()
                    }
                else:
                    example = {
                        "input": f"이번주 총 공기 정화량: {this_week}, 저번주 총 공기 정화량: {last_week}",
                        "output": output.strip()
                    }
            examples.append(example)
    
    return examples