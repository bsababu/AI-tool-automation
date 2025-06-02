import os
from typing import Dict, List, Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
    ContextualPrecisionMetric,
    SummarizationMetric,
    HallucinationMetric
)
from deepeval.test_case import LLMTestCase


if trace.get_tracer_provider().__class__.__name__ == "NoOpTracerProvider":
    trace.set_tracer_provider(TracerProvider())

def create_test_case(query: str, response: str, repo_data: Dict[str, Any]) -> LLMTestCase:
    """
    Create a test case for evaluating the response quality.
    
    Args:
        query: The user's query
        response: The agent's response
        repo_data: Repository analysis data
    
    Returns:
        LLMTestCase: A test case for evaluation
    """
    # Extract relevant context as list of plain strings
    context = []
    
    if "profile" in repo_data:
        profile_str = str(repo_data['profile'])
        context.append(f"Repository profile: {profile_str}")
    
    if "estimated" in repo_data:
        estimated = repo_data["estimated"]
        if "estimated_Memory" in estimated:
            memory_str = str(estimated['estimated_Memory'])
            context.append(f"Memory requirement: {memory_str}")
            
        if "estimated_CPU_cores" in estimated:
            cpu_str = str(estimated['estimated_CPU_cores'])
            context.append(f"CPU cores needed: {cpu_str}")
            
        if "estimated_network_bandwidth" in estimated:
            network_str = str(estimated['estimated_network_bandwidth'])
            context.append(f"Network bandwidth required: {network_str}")
    
    context = [str(item) for item in context]
    
    test_case = LLMTestCase(
        input=query,
        actual_output=response,
        context=context if context else None, 
        expected_output=None
    )
    
    return test_case

def evaluate_response(query: str, response: str, repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate the quality of an agent's response.
    
    Args:
        query: The user's query
        response: The agent's response
        repo_data: Repository analysis data
    
    Returns:
        Dict containing evaluation metrics and scores
    """
    
    test_case = create_test_case(query, response, repo_data)
    
    metrics = {
        'Answer Relevancy': AnswerRelevancyMetric(),
        'Contextual Relevancy': ContextualRelevancyMetric(),
        'Contextual Precision': ContextualPrecisionMetric(),
        'Hallucination': HallucinationMetric(),
    }
    
    results = {}
    total_score = 0
    valid_metrics = 0
    
    # Evaluate each metric
    for metric_name, metric in metrics.items():
        try:
            metric.measure(test_case)
            score = metric.score
            results[metric_name] = {
                'score': score,
                'threshold': metric.threshold,
                'passed': score >= metric.threshold if hasattr(metric, 'threshold') else None
            }
            total_score += score
            valid_metrics += 1
        except Exception as e:
            results[metric_name] = {
                'score': 0,
                'error': str(e)
            }
    
    # Calculate overall score
    if valid_metrics > 0:
        results['overall_score'] = total_score / valid_metrics
    else:
        results['overall_score'] = 0
    
    return results