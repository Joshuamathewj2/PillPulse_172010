from app.services.llm_service import generate
import json

def analyze_symptoms(answers: dict):
    prompt = f"""
Based on these symptoms, estimate risk level, possible conditions, and recommended actions.
Symptoms provided:
{json.dumps(answers, indent=2)}

Please return ONLY a valid JSON object matching exactly this structure:
{{
  "risk_level": "low" | "moderate" | "high",
  "possible_conditions": ["condition1", "condition2"],
  "recommendations": ["rec1", "rec2"]
}}
"""
    response_text = generate(prompt)
    
    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
        else:
            json_str = response_text.strip()
            
        result = json.loads(json_str)
        return result
    except Exception as e:
        print(f"Error parsing JSON from LLM: {e}")
        return {
            "risk_level": "moderate",
            "possible_conditions": ["Unknown condition"],
            "recommendations": ["Please consult a healthcare professional for an accurate diagnosis."]
        }
