import os
import logging
import torch
import transformers
from datetime import datetime
from transformers import GenerationConfig, AutoTokenizer, AutoModelForCausalLM
from langchain_huggingface import HuggingFacePipeline
from app.models.inference import create_pipeline, generate_recommendations

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
transformers.utils.logging.set_verbosity_error()

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

def get_mock_data():
    # return {
    #     "pm_current": 0,
    #     "pm_this_week": 0,
    #     "averagePm": [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]],
    #     "averageCleanTime": [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]],
    #     "averageCleanAmount": [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]]
    # }
    # return {
    #     "pm_current": 50,
    #     "pm_this_week": 45,
    #     "averagePm": [[0, 0, 0, 0, 0, 0, 0], [50, 48, 46, 47, 49, 50, 45]],
    #     "averageCleanTime": [[0, 0, 0, 0, 0, 0, 0], [15, 16, 14, 17, 19, 21, 23]],
    #     "averageCleanAmount": [[0, 0, 0, 0, 0, 0, 0], [120, 130, 140, 150, 160, 170, 180]]
    # }
    return {
        "pm_current": 50,
        "pm_this_week": 45,
        "averagePm": [[40, 42, 38, 37, 45, 44, 43], [50, 48, 46, 47, 49, 50, 45]],
        "averageCleanTime": [[10, 12, 15, 18, 20, 22, 25], [150, 160, 140, 170, 190, 210, 230]],
        "averageCleanAmount": [[100, 110, 120, 130, 140, 150, 160], [120, 130, 140, 150, 160, 170, 180]]
    }

def run_inference(device_id: int):
    try:
        tokenizer, model = load_model()
        pipe = create_pipeline(model, tokenizer)
        llm = HuggingFacePipeline(pipeline=pipe)

        data = get_mock_data()
        recommendations = generate_recommendations(data, llm)

        return {"deviceId": device_id, "recommendations": recommendations}

    except Exception as e:
        logger.error(f"Error in run_inference: {e}")
        return {"deviceId": device_id, "recommendations": ["서비스 오류가 발생했습니다."] * 4}

# python -m app.models.model_test
if __name__ == "__main__":
    result = run_inference(801)
    print(result)