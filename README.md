# Capstone-design1 — Co-Layout MVP

Co-Layout 논문(arXiv:2511.12474)의 **(b) Optimization 파트**를 최소 기능(MVP)으로 구현한 코드.
JSON 제약조건을 입력받아 **PuLP + CBC**로 격자 기반 방 배치를 최적화하고,
**matplotlib**으로 컬러 평면도 PNG 1장을 출력한다.

## 구성

```
.
├── main.py          # 실행 진입점 (로드 → 풀이 → 렌더)
├── constraints.json # 입력: 격자 크기 + 방별 목표 면적/색상
├── solver.py        # 이진 변수 + 비겹침 제약 + 면적 제약 + CBC 풀이
├── renderer.py      # matplotlib 컬러 평면도 출력
├── output/          # 결과 저장 (layout.png)
└── prompt.md        # 구현에 사용한 단계별 프롬프트 기록
```

## 실행

```bash
pip install -r requirements.txt
python main.py
```

성공하면 `output/layout.png`가 생성된다.

```
=== Co-Layout MVP ===
[1/3] 제약조건 로드... 완료
[2/3] 최적화 (CBC)... 완료 (status: Optimal)
[3/3] 도면 생성... 완료
---------------------
output/layout.png 저장됨
=====================
```

> Windows에서 `python`이 인식되지 않으면 `py main.py`로 실행. 한글 출력이 깨지면
> `PYTHONUTF8=1`을 붙인다.

## MVP 범위

- **구현**: JSON 파싱 · 이진 변수 · 비겹침 제약 · 면적 제약 · PNG 출력
- **제외**: 인접 제약 · 복도 연결성 · 목적 함수 · 가구 배치 · Coarse-to-Fine ·
  LLM 에이전트 · Blender 렌더링

## 알려진 한계

면적은 목표값과 정확히 일치하지만, 목적함수·인접 제약이 없어 방이 직사각형 한
덩어리로 모이지 않는다(일부 방이 여러 조각으로 분리됨). 확장하려면 인접 제약 +
목적함수(rectangularity / shape)를 추가해야 한다. 자세한 구현 과정은 `prompt.md` 참고.
