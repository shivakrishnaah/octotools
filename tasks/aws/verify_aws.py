import os
import json
import argparse
import concurrent.futures
import tqdm
from pydantic import BaseModel
from octotools.engine.openai import ChatOpenAI
from tasks.utils import ResultAnalyzer


class AWSToolsVerifier:
    def __init__(self, llm_engine=None):
        self.llm_engine = llm_engine or ChatOpenAI(model_string="gpt-4o", is_multimodal=False, enable_cache=True)
        print(f"\OpenAI engine {self.llm_engine.model_string} initialized.\n")




def load_data(data_file):
    with open(data_file, 'r') as f:
        return {data["pid"]: data for data in json.load(f)}


def parse_args():
    parser = argparse.ArgumentParser(description="Verify AWS tools in dataset responses")
    parser.add_argument("--data_file", type=str, required=True, help="The file containing the dataset")
    parser.add_argument("--output_file", type=str, default="verified_results.json", help="File to save verified results")
    parser.add_argument("--max_workers", type=int, default=16, help="Max number of parallel workers")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("#" * 50)
    print(f"Arguments: {args}")
    print("#" * 50)

    verifier = AWSToolsVerifier()
    
    results = load_data(args.data_file)
    results, correct = verifier.score_results(results, max_workers=args.max_workers)
    
    accuracy = round(correct / len(results) * 100, 2)
    print(f"\nAccuracy: {accuracy}% ({correct}/{len(results)})")

    with open(args.output_file, 'w') as f:
        json.dump(results, f, indent=4)
        print(f"Results saved to {args.output_file}")
