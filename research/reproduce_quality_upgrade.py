"""Offline replay of the quality upgrade using cached evidence, Python stdlib only."""
import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
for script in ['counterfactual_all_scope_v2.py','research_quality_analysis.py','candidate_window_sensitivity.py','verify_research_quality.py']:
 subprocess.run([sys.executable,str(R/script)],check=True)
print('Offline research replay complete. PDF/figures use separate optional authoring dependencies.')
