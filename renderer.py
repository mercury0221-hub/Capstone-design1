"""matplotlib으로 방 배치 결과를 컬러 평면도 PNG 한 장으로 렌더링한다."""

import os

import matplotlib

matplotlib.use("Agg")  # GUI 없이 파일로만 저장

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


def draw_layout(grid, cfg, output_path="output/layout.png"):
    """방 배치 grid를 컬러 평면도 PNG로 저장한다.

    Args:
        grid: solve()가 반환한 2D 리스트. grid[i][j] = 방 id(str) 또는 None.
        cfg: constraints.json을 파싱한 dict (grid, rooms 포함).
        output_path: 저장 경로 (기본 "output/layout.png").
    """
    width = cfg["grid"]["width"]
    height = cfg["grid"]["height"]
    room_ids = [room["name"] for room in cfg["rooms"]]
    colors = [room["color"] for room in cfg["rooms"]]

    # 방 id → 정수 인덱스 매핑 (imshow + ListedColormap용).
    idx_of = {k: n for n, k in enumerate(room_ids)}
    z = np.full((height, width), -1, dtype=int)
    for i in range(height):
        for j in range(width):
            if grid[i][j] is not None:
                z[i][j] = idx_of[grid[i][j]]

    cmap = ListedColormap(colors)

    fig, ax = plt.subplots(figsize=(width / 1.5, height / 1.5))
    ax.imshow(z, cmap=cmap, vmin=0, vmax=len(room_ids) - 1, origin="upper")

    # 옅은 회색 격자선 (셀 경계).
    ax.set_xticks(np.arange(-0.5, width, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, height, 1), minor=True)
    ax.grid(which="minor", color="lightgray", linewidth=0.8)
    ax.tick_params(which="both", bottom=False, left=False,
                   labelbottom=False, labelleft=False)

    # 방 이름을 각 방 영역의 중심(셀 좌표 평균)에 표시.
    for k in room_ids:
        cells = [(i, j) for i in range(height) for j in range(width)
                 if grid[i][j] == k]
        if not cells:
            continue
        cy = sum(i for i, _ in cells) / len(cells)
        cx = sum(j for _, j in cells) / len(cells)
        ax.text(cx, cy, k, ha="center", va="center",
                fontsize=10, fontweight="bold", color="#333333")

    # 범례 (방 이름 + 색상)를 도면 우측에 배치.
    handles = [Patch(facecolor=room["color"], edgecolor="gray", label=room["name"])
               for room in cfg["rooms"]]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5),
              frameon=False, title="Rooms")

    ax.set_title("Co-Layout MVP Result", fontsize=13, fontweight="bold")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
