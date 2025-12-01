import base64
from loguru import logger
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_base64_or_path(input_string):
    # 移除可能的前缀（如 "data:image/jpeg;base64,"）
    stripped_string = re.sub(r'^data:image/.+;base64,', '', input_string)
    
    # 检查是否是有效的文件路径
    if os.path.exists(input_string):
        return "path"
    
    # 检查是否可能是 base64
    try:
        # 尝试解码
        base64.b64decode(stripped_string)
        # 检查是否只包含 base64 字符
        if re.match(r'^[A-Za-z0-9+/]+={0,2}$', stripped_string):
            return "base64"
    except:
        pass
    # 如果既不是有效路径也不是 base64，返回 "unknown"
    return "unknown"

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

class ClfResult(BaseModel):
    """Classification result."""
    result: bool = Field(description="true or flase, classification result.")

FIX_SIGNAL="""### Assessment Opinion:
Warning

⚠️ IMPORTANT NOTICE ⚠️

The analysis has detected unusually intense negative emotions in the drawing. 
This has triggered a safety mechanism in our system.

We strongly recommend seeking immediate assistance from a qualified mental health professional. 
Your well-being is paramount, and a trained expert can provide the support you may need at this time.

Remember, it's okay to ask for help. You're not alone in this. """

class HTPModel(object):
    def __init__(self, text_model, multimodal_model = None, language: str = "en", use_cache: bool = True):
        self.text_model = text_model
        self.multimodal_model = multimodal_model if multimodal_model else text_model
        # set language
        assert language == "en", "Language must be 'en'."
        self.language = language
        logger.info(f"HTPModel initialized with language: {language}")
        # set cache
        if use_cache:
            set_llm_cache(SQLiteCache("cache.db"))
            logger.info("Cache enabled.")
        # init token usage
        self.usage = {
            "total": 0,
            "prompt": 0,
            "completion": 0
        }
    
    def refresh_usage(self):
        self.usage = {
            "total": 0,
            "prompt": 0,
            "completion": 0
        }
    
    def update_usage(self, response):
        """Update token usage from Gemini response metadata"""
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            self.usage["total"] += response.usage_metadata.get('input_tokens', 0) + response.usage_metadata.get('output_tokens', 0)
            self.usage["prompt"] += response.usage_metadata.get('input_tokens', 0)
            self.usage["completion"] += response.usage_metadata.get('output_tokens', 0)
        
    def get_prompt(self, stage: str):
        assert stage in ["overall", "house", "tree", "person"], "Stage should be either 'overall', 'house', 'tree', or 'person'."

        if stage == "overall":
            feature_prompt = open(f"src/prompt/{self.language}/overall_feature.txt", "r", encoding="utf-8").read()
            analysis_prompt = open(f"src/prompt/{self.language}/overall_analysis.txt", "r", encoding="utf-8").read()
        elif stage == "house":
            feature_prompt = open(f"src/prompt/{self.language}/house_feature.txt", "r", encoding="utf-8").read()
            analysis_prompt = open(f"src/prompt/{self.language}/house_analysis.txt", "r", encoding="utf-8").read()
        elif stage == "tree":
            feature_prompt = open(f"src/prompt/{self.language}/tree_feature.txt", "r", encoding="utf-8").read()
            analysis_prompt = open(f"src/prompt/{self.language}/tree_analysis.txt", "r", encoding="utf-8").read()
        elif stage == "person":
            feature_prompt = open(f"src/prompt/{self.language}/person_feature.txt", "r", encoding="utf-8").read()
            analysis_prompt = open(f"src/prompt/{self.language}/person_analysis.txt", "r", encoding="utf-8").read()
            
        return feature_prompt, analysis_prompt
    
    def basic_analysis(self, image_path: str, stage: str):
        feature_prompt, analysis_prompt = self.get_prompt(stage)
        
        feature_input = "Organize the feature extraction results into a **clear and concise** markdown format."
        analysis_input = "Please analyze the features based on professional knowledge and the image features provided by the assistant, and organize the results in markdown format."
            
        # 判断输入是 base64 还是路径
        if is_base64_or_path(image_path) == "path":
            image_data = encode_image(image_path)
        elif is_base64_or_path(image_path) == "base64":
            image_data = image_path
        else:
            raise ValueError("Invalid image path or base64 string.")
        
        feature_prompt = ChatPromptTemplate.from_messages([
            ("system", feature_prompt),
            (
                "user", 
                [
                    {"type": "image_url", "image_url": {'url': 'data:image/jpeg;base64,{image_data}'}},
                    {"type": "text", "text": feature_input}
                ]
            )]
        )
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", analysis_prompt),
            (
                "user",
                [
                    {"type": "image_url", "image_url": {'url': 'data:image/jpeg;base64,{image_data}'}},
                    {"type": "text", "text": analysis_input}
                ]
            )]
        )
        logger.info(f"{stage} analysis started.")
        chain = feature_prompt | self.multimodal_model
        feature_response = chain.invoke({
            "image_data": image_data
        })
        feature_result = feature_response.content
        self.update_usage(feature_response)
        
        chain = analysis_prompt | self.text_model
        analysis_response = chain.invoke({
            "image_data": image_data,
            "FEATURES": feature_result
        })
        analysis_result = analysis_response.content
        self.update_usage(analysis_response)
            
        logger.info(f"{stage} analysis completed.")
        
        return feature_result, analysis_result
    
    def merge_analysis(self, results: dict):
        logger.info("merge analysis started.")
        merge_prompt = open(f"src/prompt/{self.language}/analysis_merge.txt", "r", encoding="utf-8").read()
        merge_inputs = open(f"src/prompt/{self.language}/merge_format.txt", "r", encoding="utf-8").read()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", merge_prompt),
            (
                "user",
                [
                    {"type": "text", "text": merge_inputs}
                ]
            )]
        )
        chain = prompt | self.text_model
        response = chain.invoke({
            "overall_analysis": results["overall"]["analysis"],
            "house_analysis": results["house"]["analysis"],
            "tree_analysis": results["tree"]["analysis"],
            "person_analysis": results["person"]["analysis"]
        })
        result = response.content
        self.update_usage(response)
        
        logger.info("merge analysis completed.")
        return result
    
    def final_analysis(self, results: dict):
        logger.info("final analysis started.")
        final_prompt = open(f"src/prompt/{self.language}/final_result.txt", "r", encoding="utf-8").read()
        
        inputs = "Based on the analysis results: \n{merge_result}\n, write your professional HTP test report."
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", final_prompt),
            ("user", inputs)
        ])
        
        chain = prompt | self.text_model
        response = chain.invoke({
            "merge_result": results["merge"]
        })
        result = response.content
        self.update_usage(response)
        
        logger.info("final analysis completed.")
        return result
    
    def signal_analysis(self, results: dict):
        logger.info("signal analysis started.")
        signal_prompt = open(f"src/prompt/{self.language}/signal_judge.txt", "r", encoding="utf-8").read()
        inputs = "{final_result}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", signal_prompt),
            ("user", inputs)
        ])
        
        chain = prompt | self.text_model
        response = chain.invoke({
            "final_result": results["final"]
        })
        result = response.content
        self.update_usage(response)
        
        logger.info("signal analysis completed.")
        return result
    
    def result_classification(self, results: dict):
        logger.info("result classification started.")
        classification_prompt = open(f"src/prompt/{self.language}/clf.txt", "r", encoding="utf-8").read()
        inputs = "{result}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", classification_prompt),
            ("user", inputs + "{format_instructions}")
        ])
        # chain = prompt | self.multimodal_model.with_structured_output(ClfResult)
        from langchain_core.output_parsers import JsonOutputParser
        
        parse = JsonOutputParser(pydantic_object=ClfResult)
        chain = prompt | self.multimodal_model | parse
        response = chain.invoke({
            "result": results["signal"],
            "format_instructions": parse.get_format_instructions()
        })
        result = response
        
        if type(result) == dict:
            result = result["result"]
        if type(result) == str:
            if result == "true":
                result = True
            elif result == "false":
                result = False
                
        logger.info(f"result classification completed. Result: {result}")
        if type(result) == bool:
            return result
        else:
            return True
        
    def person_final_report(self, person_features: str, person_analysis: str):
        """Generates the final, formatted report for the Person drawing."""
        logger.info("Generating final Person report.")
        final_report_prompt_text = open(f"src/prompt/{self.language}/person_final_report.txt", "r", encoding="utf-8").read()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", final_report_prompt_text),
            (
                "user",
                "VISUAL FEATURES:\n{features}\n\nPSYCHOLOGICAL INTERPRETATIONS:\n{analysis}"
            )
        ])
        
        chain = prompt | self.text_model
        response = chain.invoke({
            "features": person_features,
            "analysis": person_analysis
        })
        result = response.content
        self.update_usage(response)
        
        logger.info("Final Person report generated.")
        return result

    def pluto_workflow(self, image_path: str, language: str = "en"):
        """
        A streamlined workflow for the PLUTO project that analyzes ONLY the Person drawing.
        It returns a structured report with blank fields for House and Tree.
        """
        self.refresh_usage()
        self.language = language

        # 1. Analyze only the Person drawing (Feature Extraction and Interpretation)
        logger.info("Starting PLUTO workflow for Person analysis.")
        person_features, person_analysis = self.basic_analysis(image_path, "person")

        # 2. Generate the final, formatted report using the new prompt
        final_report_content = self.person_final_report(person_features, person_analysis)

        # 3. Assemble the final output object in the desired format
        # This keeps the output structure consistent with the original, but with blank data.
        blank_analysis = {"feature": "Not analyzed.", "analysis": "Not applicable."}
        
        results = {
            "overall": blank_analysis,
            "house": blank_analysis,
            "tree": blank_analysis,
            "person": {
                "feature": person_features,
                "analysis": person_analysis
            },
            "merge": "Not applicable for Person-only analysis.",
            "final": final_report_content, # This is your main output!
            "signal": "Please review the final report for a qualitative summary.",
            "classification": None, # Classification is not performed in this simplified flow
            "fix_signal": None,
            "usage": self.usage
        }
        
        logger.info("PLUTO workflow completed.")
        return results

    # Keep the original workflow method in case you need it, but your project will call pluto_workflow
    def workflow(self, image_path: str, language: str = "en"):
        self.refresh_usage()
        # update language
        self.language = language
        
        with ThreadPoolExecutor(max_workers = 4) as executor:
            futures = {
                executor.submit(self.basic_analysis, image_path, stage): stage for stage in ["overall", "house", "tree", "person"]
            }
            
            results = {}
            for future in as_completed(futures):
                stage = futures[future]
                feature_result, analysis_result = future.result()
                results[stage] = {
                    "feature": feature_result,
                    "analysis": analysis_result
                }
            results["usage"] = self.usage
        
        results["merge"] = self.merge_analysis(results)
        results["final"] = self.final_analysis(results)
        results["signal"] = self.signal_analysis(results)
        results["classification"] = self.result_classification(results)
        if results["classification"] == False:
            results["fix_signal"] = FIX_SIGNAL
        else:
            results["fix_signal"] = None
            
        logger.info("HTP analysis workflow completed.")
        
        return results