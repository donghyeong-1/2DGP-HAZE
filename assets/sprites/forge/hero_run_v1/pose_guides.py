"""달리기와 전환 원화에 첨부할 관절 배치 안내를 그린다."""
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
RUN = [
    # 제목, 골반 y, 어깨, 가까운 다리, 먼 다리, 가까운 팔, 먼 팔
    ("1 NEAR HEEL", 0, (9, -30), ((27, 25), (34, 52), 3), ((-26, 21), (-41, 46), -6),
     ((-13, -15), (-30, -22)), ((22, -12), (38, -29))),
    ("2 NEAR DOWN", 3, (9, -27), ((17, 27), (10, 55), 0), ((-29, 18), (-34, 34), -7),
     ((-8, -10), (-23, -16)), ((23, -10), (34, -25))),
    ("3 FAR PASSES", 0, (9, -30), ((-16, 29), (-22, 53), -7), ((31, 16), (15, 40), 0),
     ((12, -7), (26, -28)), ((-9, -14), (-19, -23))),
    ("4 AIR / FAR LEADS", -3, (9, -34), ((-26, 19), (-39, 43), -7), ((32, 16), (37, 46), 3),
     ((23, -15), (38, -34)), ((-12, -21), (-30, -27))),
]

TRANS = [
    ("1 START / LOAD", 6, (12, -20), ((18, 28), (23, 55), 0), ((-21, 29), (-31, 54), -4),
     ((12, 4), (26, -16)), ((-2, 1), (-19, -12))),
    ("2 START / DRIVE", 0, (11, -31), ((32, 14), (18, 40), 0), ((-26, 25), (-40, 53), -6),
     ((-15, -12), (-29, -20)), ((24, -13), (37, -28))),
    ("3 STOP / BRAKE", 0, (-10, -29), ((24, 23), (36, 55), 0), ((-16, 24), (-18, 54), -3),
     ((-24, -11), (-35, -22)), ((8, -11), (24, -24))),
    ("4 STOP / RECOVER", 5, (-2, -24), ((13, 26), (10, 55), 0), ((-11, 29), (-17, 55), 0),
     ((-13, -5), (-15, 16)), ((12, -6), (15, 15))),
    ("5 PIVOT / BRAKE", 4, (-9, -27), ((22, 27), (26, 55), 0), ((-19, 26), (-24, 53), -5),
     ((-23, -16), (-38, -23)), ((1, -2), (18, -12))),
]


def draw_sheet(poses, columns, name):
    cell_width, cell_height = 384, 470
    canvas = Image.new("RGB", (cell_width * columns, cell_height * 2), "#e8edf0")
    draw = ImageDraw.Draw(canvas)
    for i, (title, hip_y, shoulder, near_leg, far_leg, near_arm, far_arm) in enumerate(poses):
        x = (i % columns) * cell_width
        y = (i // columns) * cell_height
        draw.rectangle((x + 5, y + 5, x + cell_width - 6, y + cell_height - 6), fill="#f8fafb", outline="#c4cdd6")
        draw.text((x + 18, y + 16), title, fill="#1c2632", font_size=19)
        px, py = x + 180, y + 234

        def grid(point):
            return px + 3 * point[0], py + 3 * point[1]

        def limb(points, color, width=16):
            draw.line([grid(p) for p in points], fill=color, width=width, joint="curve")
            for p in points[1:-1]:
                a, b = grid(p)
                draw.ellipse((a-7, b-7, a+7, b+7), fill=color)

        hip = (0, hip_y)
        draw.line((x+28, py+180, x+cell_width-28, py+180), fill="#b9c7d3", width=2)
        limb([shoulder, *far_arm], "#33456e")
        for (knee, ankle, toe_drop), color in ((far_leg, "#33456e"), (near_leg, "#a65a24")):
            toe = (ankle[0]+11, ankle[1]+toe_drop)
            limb([hip, knee, ankle, toe], color, 18)
        limb([hip, shoulder], "#687789", 26)
        limb([shoulder, *near_arm], "#a65a24")
        hx, hy = grid((shoulder[0]+4, shoulder[1]-13))
        draw.ellipse((hx-21, hy-24, hx+21, hy+24), outline="#687789", width=5)
        draw.polygon(((hx+19, hy-5), (hx+29, hy+2), (hx+19, hy+8)), fill="#687789")
    canvas.save(ROOT / name)


def main():
    other = [(f"{i+5} " + ["FAR HEEL", "FAR DOWN", "NEAR PASSES", "AIR / NEAR LEADS"][i],
              hip, shoulder, far_leg, near_leg, far_arm, near_arm)
             for i, (_, hip, shoulder, near_leg, far_leg, near_arm, far_arm) in enumerate(RUN)]
    draw_sheet(RUN + other, 4, "run_pose_guide.png")
    draw_sheet(TRANS, 3, "transition_pose_guide.png")


if __name__ == "__main__":
    main()
