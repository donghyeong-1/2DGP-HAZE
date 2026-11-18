"""T21의 두 걸음에 사용할 관절 배치 안내를 만든다."""
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("prior_guide", ROOT.parent / "hero_run_v1/pose_guides.py")
guide = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guide)
guide.ROOT = ROOT
guide.draw_sheet(guide.RUN, 2, "step_A_guide.png")
other = [
    (f"{i+5} " + ["FAR HEEL", "FAR DOWN", "NEAR PASSES", "AIR / NEAR LEADS"][i],
     hip, shoulder, far_leg, near_leg, far_arm, near_arm)
    for i, (_, hip, shoulder, near_leg, far_leg, near_arm, far_arm) in enumerate(guide.RUN)
]
guide.draw_sheet(other, 2, "step_B_guide.png")
