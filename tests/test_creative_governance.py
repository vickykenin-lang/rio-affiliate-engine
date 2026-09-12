import json, unittest
from pathlib import Path
from scripts.creative_governance import record_actual,reserve_cost,validate_package,validate_prompt
from scripts.creative_provider import NovaCanvasProvider

class CreativeGovernanceTests(unittest.TestCase):
 def test_provider_is_default_deny(self):
  p=NovaCanvasProvider(); req=p.build_request('Original editorial illustration of organized pantry containers',1080,1080,7)
  with self.assertRaises(PermissionError): p.generate(req)
 def test_forbidden_copy_prompt_is_rejected(self): self.assertTrue(validate_prompt('Copy the product photo exactly'))
 def test_package_requires_disclosure_and_valid_hash(self):
  self.assertEqual(validate_package({'source_policy':'ORIGINAL_CONTEXTUAL','caption_text':'Useful idea #ad','creative_sha256':'a'*64}),[])
 def test_zero_budget_blocks_reservation(self):
  ledger={'approved_budget':0,'reserved':0,'actual_spend':0,'entries':[]}
  with self.assertRaises(PermissionError): reserve_cost(ledger,'CMP_X','req-1',0.01)
 def test_reservation_and_actual_are_idempotent(self):
  ledger={'approved_budget':1,'reserved':0,'actual_spend':0,'entries':[]}
  a=reserve_cost(ledger,'CMP_X','req-1',0.1,at='t1'); self.assertEqual(reserve_cost(a,'CMP_X','req-1',0.1),a)
  b=record_actual(a,'req-1',0.08,at='t2'); self.assertEqual(record_actual(b,'req-1',0.08),b); self.assertEqual(b['actual_spend'],0.08)
if __name__=='__main__': unittest.main()
