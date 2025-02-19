import os
import re
import json
import logging
import torch
import transformers
from datetime import datetime
from transformers import GenerationConfig, pipeline, AutoTokenizer, AutoModelForCausalLM
from langchain_huggingface import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy.orm import Session
from fastapi import Request
from app.database.crud import get_hourly_data
from app.services.json_load import load_device_json
from app.models.fewshot_prompt import generate_fewshot_prompt

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
transformers.utils.logging.set_verbosity_error()
    
def get_model_from_app_state(request: Request):
    tokenizer = request.app.state.tokenizer
    model = request.app.state.model
    if tokenizer is None or model is None:
        raise RuntimeError("AI Model is not loaded. Please check the startup logs.")
    return tokenizer, model

def load_model():
    try:
        logger.info("Loading the AI inference model...")

        # model_path = os.path.abspath("./app/models/fine_tuned_model_v3")
        model_path = os.path.abspath("./app/models/puricat-report")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map=None,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )

        model.generation_config = GenerationConfig(
            do_sample=False,
            temperature=None,
            top_p=None,
            top_k=None
        )

        logger.info("Model loaded successfully.")
        return tokenizer, model

    except Exception as e:
        logger.error(f"Failed to load model: {e}", exc_info=True)
        return None, None
    
def create_pipeline(model, tokenizer):
    
    return pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device=-1,
        max_new_tokens=200,
        do_sample=False,
        no_repeat_ngram_size=3,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id else 0,
        repetition_penalty=1.2
    )

def get_data(db: Session, device_id: int):
    try:
        logger.info("Fetching data for device_id: %s", device_id)

        hourly_data = get_hourly_data(db, device_id)
        pm_current = 0.0
        if hourly_data:
            pm_current = round(hourly_data.pm_current, 1) if hourly_data and hourly_data.pm_current is not None else 0.0

        daily_data = load_device_json(db, device_id)
        if not daily_data:
            logger.warning("No data found for device_id: %s", device_id)
            return {}
        
        average_pm = daily_data.get("averagePm", [[0] * 7, [0] * 7])
        this_week_pm_values = [float(value) for value in average_pm[1] if isinstance(value, (int, float))]  
        pm_this_week = int(round(sum(this_week_pm_values) / len(this_week_pm_values), 0)) if this_week_pm_values else 0

        data = {
            "pm_current": pm_current,
            "pm_this_week": pm_this_week,
            "averagePm": average_pm,
            "averageCleanTime": daily_data.get("averageCleanTime", [[0] * 7, [0] * 7]),
            "averageCleanAmount": daily_data.get("averageCleanAmount", [[0] * 7, [0] * 7])
        }

        return data

    except Exception as e:
        logger.error(f"Error getting data: {e}")
        return {}

def check_data_validity(data):
    if not data or data.get("pm_current") is None:
        return "no_data"

    average_pm = data.get("averagePm", [[0] * 7, [0] * 7])
    average_clean_time = data.get("averageCleanTime", [[0] * 7, [0] * 7])
    average_clean_amount = data.get("averageCleanAmount", [[0] * 7, [0] * 7])

    last_week_exists = any(val != 0 for val in average_pm[0]) or \
                       any(val != 0 for val in average_clean_time[0]) or \
                       any(val != 0 for val in average_clean_amount[0])

    this_week_exists = any(val != 0 for val in average_pm[1]) or \
                       any(val != 0 for val in average_clean_time[1]) or \
                       any(val != 0 for val in average_clean_amount[1])

    if not this_week_exists:
        return "no_data"
    
    return "two_week" if last_week_exists else "one_week"

def generate_recommendations(data, llm):
    recommendations = []
    
    case = check_data_validity(data)
    if case == "no_data":
        return ["아직 데이터가 충분하지 않습니다..."] * 4
    
    for insight_number in range(1, 5):
        formatted_prompt = generate_fewshot_prompt(data, case, insight_number)
        if not formatted_prompt:
            recommendations.append("아직 데이터가 충분하지 않습니다...")
            continue

        try:
            chain = RunnablePassthrough() | llm | StrOutputParser()
            raw_result = chain.invoke(formatted_prompt)
            result = clean_insight(raw_result)
            recommendations.append(result)
            print(result)

        except Exception as e:
            logger.error(f"Error generating insight {insight_number}: {e}")
            recommendations.append("인사이트 생성 중 오류가 발생했습니다.")

    return recommendations

def clean_insight(raw_output):
    if "출력:" in raw_output:
        content = raw_output.split("출력:")[-1].strip()
    else:
        content = raw_output.strip()
    
    match = re.search(r'^(.*?[.!?])\s', content + " ")
    if match:
        first_sentence = match.group(1).strip()
    else:
        first_sentence = content.split("\n")[0].strip()
    
    if not first_sentence or len(first_sentence) < 5:
        return "인사이트를 생성할 수 없습니다."
    
    cleaned = re.sub(r'<[^>]+>', '', first_sentence)
    cleaned = re.sub(r'\*\*|__', '', cleaned).strip()
    
    if cleaned[-1] not in ['.', '?', '!']:
        cleaned += '.'
    
    return cleaned

def log_inference_result(device_id: int, insight_number: int, prompt: str, result: str):
    log_data = {
        "device_id": device_id,
        "insight_number": insight_number,
        "prompt": str(prompt),
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
    logger.info(f"Inference result:\n{json.dumps(log_data, indent=2, ensure_ascii=False)}")

def run_inference(db: Session, device_id: int, request: Request):
    try:
        tokenizer, model = get_model_from_app_state(request)
        pipe = create_pipeline(model, tokenizer)
        llm = HuggingFacePipeline(pipeline=pipe)

        data = get_data(db, device_id)
        recommendations = generate_recommendations(data, llm)

        return {"deviceId": device_id, "recommendations": recommendations}

    except Exception as e:
        logger.error(f"Error in run_inference: {e}")
        return {"deviceId": device_id, "recommendations": ["서비스 오류가 발생했습니다."] * 4}