import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from financial_parser import clean_number,calculate_ratios,normalize
class T(unittest.TestCase):
 def test_numbers(self):
  self.assertEqual(clean_number("1,234"),1234); self.assertEqual(clean_number("(100)"),-100); self.assertIsNone(clean_number("-"))
 def test_ratios(self):
  rows=[{"year":2023,"revenue":100,"gross_profit":40,"operating_income":10,"net_income":8,"assets":100,"equity":50,"current_assets":40,"current_liabilities":20,"inventory":10,"receivables":10,"payables":8,"debt":20,"net_debt":10,"ebitda":15,"cfo":12,"interest_expense":2,"pretax_income":10},{"year":2024,"revenue":120,"gross_profit":48,"operating_income":12,"net_income":9,"assets":110,"equity":55,"current_assets":45,"current_liabilities":25,"inventory":12,"receivables":11,"payables":9,"debt":18,"net_debt":8,"ebitda":16,"cfo":14,"interest_expense":2,"pretax_income":12}]
  r=calculate_ratios(rows); self.assertAlmostEqual(r[-1]["operating_margin"],10); self.assertAlmostEqual(r[-1]["current_ratio"],1.8); self.assertAlmostEqual(r[-1]["revenue_growth"],20); self.assertAlmostEqual(r[-1]["cfo_to_net_income"],14/9)
 def test_normalize(self):
  p={"_fs_div_used":"CFS","list":[{"sj_div":"BS","account_nm":"자산총계","thstrm_amount":"100"},{"sj_div":"BS","account_nm":"부채총계","thstrm_amount":"40"},{"sj_div":"BS","account_nm":"자본총계","thstrm_amount":"60"},{"sj_div":"IS","account_nm":"매출액","thstrm_amount":"120"},{"sj_div":"IS","account_nm":"영업이익","thstrm_amount":"10"},{"sj_div":"IS","account_nm":"당기순이익","thstrm_amount":"8"}]}
  r=normalize(p,2025,"11011"); self.assertEqual(r["fs_div"],"CFS"); self.assertEqual(r["revenue"],120); self.assertEqual(r["assets"],100)
if __name__=="__main__":unittest.main()
