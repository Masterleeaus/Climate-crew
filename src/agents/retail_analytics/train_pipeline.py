import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.agents.retail_analytics.causal_learning import CausalLearner

# Configure logging
logging.basicConfig(level=logging.INFO)

def run_training():
    print("Initializing Causal Learner...")
    # Adjust path if needed, CausalLearner defaults to 'data/real_causal_data.csv' relative to CWD
    # We are running from project root usually
    learner = CausalLearner(data_path="data/real_causal_data.csv", model_dir="models")
    
    print("Starting training...")
    result = learner.train()
    
    print(f"Training Complete. Result: {result}")

if __name__ == "__main__":
    run_training()
