# Invoice Engine Comparison - System Summary

## 1) 프로젝트 목적
- 미국 영문 invoice를 4개 서비스로 파싱하고, 실무 서빙 관점까지 고려해 엔진을 최종 1개 선정한다.
- 비교 대상:
  - Veryfi
  - Nanonets
  - Google Document AI (Custom Extractor only)
  - Upstage (Universal Extraction)
- 인식 서비스 사이트 수: **총 4개**

## 2) 확정된 핵심 원칙
- 벤더 응답은 `raw JSON` 그대로 저장한다.
- 비교/운영 공통 처리를 위해 `normalized JSON`을 별도로 생성한다.
- 벤더별 차이는 adapter 레이어에서 흡수한다.
  - 인증/요청 포맷
  - 응답 매핑
  - 에러/타임아웃/재시도 정책

## 3) 데이터셋/샘플링 방향
- 현재 인보이스 타입은 4종.
- 권장 표본:
  - 최소: `4종 x 3건 = 12건`
  - 권장: `4종 x 5건 = 20건`
- 입력 폴더 구조:
  - `invoices/input/<invoice_type>/*`

## 4) 현재 구현 상태
- 로컬 CLI 기반 벤치 파이프라인 구현 완료:
  - scan / manifest / run
- 벤더별 어댑터 파일 분리 완료:
  - `src/invoice_benchmark/adapters/veryfi.py`
  - `src/invoice_benchmark/adapters/nanonets.py`
  - `src/invoice_benchmark/adapters/gdocai.py`
  - `src/invoice_benchmark/adapters/upstage.py`
- 레지스트리 분리:
  - `src/invoice_benchmark/adapters/registry.py`

## 5) 벤더별 운용 모드 (현재 프로젝트 기준)
- Veryfi: Invoice OCR API (prebuilt baseline)
- Nanonets: Custom Model
- Google Document AI: Custom Extractor only
- Upstage: Universal Extraction (information-extraction)

## 6) 실호출 검증 결과 (소형 샘플 기준)
- Veryfi: 호출 성공 (HTTP 201)
- Google Document AI: 호출 성공 (HTTP 200)
- Nanonets: 호출 성공 (HTTP 200)
- Upstage Universal Extraction: 호출 성공 (HTTP 200)

## 7) 실무 서빙 관점 의사결정 (중요)
- 결론: 완전 단일 스키마 강제도, 문서별 완전 개별 스키마도 비효율.
- 권장: **하이브리드 전략**
  - 공통 코어 스키마 1개(내부 표준)
  - 타입군(family)별 추출 스키마/모델
  - 의미가 근본적으로 다른 테이블 구조만 분리
- 타입 선택 UX:
  - 사용자 수동 선택만 의존하지 말고
  - 자동 분류 + 사용자 override 구조 권장

## 8) 스키마 전략 (서비스 운영용)
- 내부 표준은 `normalized_invoice_v1` 유지
- 추출 단계는 family별로 유연하게 운영
- 분리 기준:
  - line item 의미/컬럼 체계가 다름
  - 필수 비즈니스 필드가 다름
  - 특정 family 혼입 시 오탐/누락 반복

## 9) 주요 파일/경로
- 프로젝트 설명: `README.md`
- 공통 스키마: `schemas/normalized_invoice_v1.schema.json`
- 벤치 템플릿: `benchmarks/report_template.md`
- 실행 산출물:
  - raw: `artifacts/raw/`
  - normalized: `artifacts/normalized/`
  - metrics: `artifacts/metrics/`

## 10) 보안/운영 주의
- API 키/토큰은 `.env`로만 관리 (커밋 금지)
- 짧은 수명의 토큰(예: GCP access token)은 만료 시 재발급 필요
- 채팅에 노출된 키는 반드시 rotate(재발급) 권장

## 10-1) 인증 방식 요약
- Google Document AI: **OAuth 기반 Bearer access token** (`GDOCAI_ACCESS_TOKEN`)
- Veryfi: **API key 계열** (Client ID + Username + API Key 조합)
- Nanonets: **API key 계열** (Basic Auth username에 API key)
- Upstage: **API key 계열** (Bearer API Key)

## 11) 다음 액션
1. 12건 또는 20건 manifest 확정
2. 4개 벤더 동일 샘플 일괄 실행
3. 필드별 정확도/속도/비용/운영성 리포트 작성
4. family 분리 기준에 따라 최종 엔진 선정

## 12) 고정 샘플 인덱스 (4종 x 1건)
- 목적: 빠른 스모크 테스트를 항상 같은 파일로 재실행하기 위함
- 기준: 각 타입 폴더에서 **페이지 수 최소 + 파일 크기 최소** 우선
- 실행 manifest: `invoices/manifests/sample_index_4x1.csv`

| index_id | invoice_type | relative_path |
|---|---|---|
| S1 | BEE SALES | `BEE SALES/05-20-2024 36949.pdf` |
| S2 | EBD | `EBD/06-29-2023 57156.pdf` |
| S3 | Outre | `Outre/SINV1647411.pdf` |
| S4 | SNG | `SNG/3000275215-IVC(06062024).PDF` |

## 13) 작업 재개 포인트
- 상세 TODO 및 재개 명령: `TODO.md`
