import unittest
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env before imports that might need it
load_dotenv()

from src.agents.climatex_audit_agent import ClimateXAuditAgent

class TestClimateXAuditLive(unittest.TestCase):
    def setUp(self):
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.firms_key = os.getenv("FIRMS_API_KEY")
        
        if not self.google_key:
            self.skipTest("GOOGLE_API_KEY not found in .env")
        if not self.firms_key:
            self.skipTest("FIRMS_API_KEY not found in .env")
            
        # Initialize REAL Agent
        self.agent = ClimateXAuditAgent(
            google_api_key=self.google_key,
            firms_api_key=self.firms_key
        )
        
        # Ensure artifacts dir exists
        os.makedirs("artifacts/reports", exist_ok=True)

    def test_live_amazon_audit(self):
        print("\n\n=== STARTING LIVE CLIMATEX AUDIT (AMAZON) ===")
        print("This process uses Deep Research (LLM) and NASA FIRMS (Real-time Data).")
        print("Please wait (may take 2-5 minutes)...")        
        query = "Audit Carbon Project Beta in Amazon Rainforest"
        lat = -3.4653
        lon = -62.2159
        
        result_summary = self.agent.perform_full_audit(query, lat, lon)
        
        print("\n=== AUDIT COMPLETE ===")
        print(result_summary)
        files = os.listdir("artifacts/reports")
        pdf_files = [f for f in files if f.endswith(".pdf") and "ClimateX_Audit_" in f]
        
        self.assertTrue(len(pdf_files) > 0, "No PDF report was generated.")
        
        latest_pdf = max([os.path.join("artifacts/reports", f) for f in pdf_files], key=os.path.getctime)
        print(f"\n[SUCCESS] Report Generated: {os.path.abspath(latest_pdf)}")
        print(f"File Size: {os.path.getsize(latest_pdf)} bytes")
        
        self.assertGreater(os.path.getsize(latest_pdf), 1000, "PDF seems too small to be valid.")

if __name__ == '__main__':
    unittest.main()
