# The Midnight Ride 비공식 한국어 패쳐

Fallout 4 모딩 가이드 **The Midnight Ride (TMR)** 환경에 한국어 번역을 안전하게 적용하는 비공식 패쳐입니다.

원본 게임과 기존 MO2 모드 파일은 직접 수정하지 않습니다. 패쳐는 별도의 `Output/mods` 트리를 생성하며, 사용자가 결과 모드를 MO2에 복사하고 활성화하는 방식입니다.

> 이 프로젝트는 ModdingLinked 또는 The Midnight Ride 제작진의 공식 번역/도구가 아닙니다.

## v1.0.0 주요 기능

- Fallout 4 본편 + 공식 DLC 한국어 리소스를 별도 MO2 모드로 출력
- TMR 활성 플러그인 자동 탐지
- 현재 검증 버전은 미리 생성한 번역 payload로 빠르게 적용
- 플러그인 업데이트 또는 신규 플러그인 감지 시 레코드 기반 fallback 번역
- 모드 전용 SST가 있으면 **모드 전용 번역을 최우선 적용**
- 나머지 override 레코드는 **Fallout4.esm + 공식 DLC 번역을 상속**
- PRP처럼 별도 SST가 없어도 바닐라 장소명/표시 문자열을 덮어쓰는 플러그인 대응
- MCM JSON 번역은 현재 설치된 config에 병합하여 새 옵션을 보존
- `Interface/Translations` 번역 지원
- Fallout 4 영문판 런타임에 맞춰 한국어 내용이어도 `_en` 파일명을 유지

검증에 사용한 TMR Extended 프로필 기준으로 비공식 플러그인 59개를 검사했으며, 현재 버전용 빠른 payload 43개와 모드 전용 direct 사전 19개를 준비했습니다. 표시 문자열이 없는 기능성/그래픽 플러그인은 별도 번역 파일을 생성하지 않습니다.

## 준비물

- The Midnight Ride가 설치된 Mod Organizer 2 인스턴스
- Fallout 4 영문판 기반 환경
- 별도의 Fallout 4 본편 한국어 리소스 폴더
  - 기본적으로 `FO4_AE_1.11.191.Kor` 구조를 기대합니다.
  - 이 저장소와 릴리즈에는 본편 한국어 리소스를 포함하지 않습니다.

한국어 리소스 폴더에는 최소한 다음 폴더가 있어야 합니다.

- `Interface`
- `Strings`

`Programs` 폴더가 있으면 함께 출력합니다.

## 사용 방법

1. GitHub Releases에서 `TMR-Korean-Patcher-v1.0.0.zip`을 내려받아 압축을 풉니다.
2. `TMR-Korean-Patcher.exe`를 실행합니다.
3. `ModOrganizer.ini`가 있는 TMR MO2 폴더를 선택합니다.
4. `FO4_AE_1.11.191.Kor` 한국어 리소스 폴더를 선택합니다.
5. **Output 생성**을 누릅니다.
6. 생성된 `Output/mods` 안의 폴더들을 TMR의 `mods` 폴더로 복사합니다.
7. MO2에서 다음 모드를 활성화하고 원본 모드보다 높은 우선순위(보통 아래쪽)에 둡니다.
   - `TMR Korean - Base Game`
   - `TMR Korean - Plugins`
   - `TMR Korean - MCM`

패쳐가 같은 이름의 ESP/ESM/ESL을 출력하는 경우, MO2의 파일 우선순위로 원본 플러그인을 덮어쓰는 방식입니다. 원본 모드 폴더 자체는 변경하지 않습니다.

## 번역 적용 우선순위

플러그인 텍스트는 다음 순서로 처리합니다.

1. 현재 검증 버전과 해시가 일치하면 검증된 payload 사용
2. 모드 전용 direct 번역 사전
3. Fallout 4 본편/공식 DLC의 동일 레코드 번역 상속
4. 안전하게 매칭되지 않는 문자열은 변경하지 않음

Fallback은 현재 영문 원문까지 확인하므로, 모드가 의도적으로 문구를 바꾼 경우 과거 바닐라 번역을 강제로 덮어쓰지 않습니다.

## MCM / Interface

지원되는 MCM 번역 사전:

- Complex Vendors
- Crafting Highlight Fix
- Legendaries They Can Use
- Unlimited Survival Mode
- Upscaling (모드가 활성화된 경우)

지원되는 `Interface/Translations`:

- Mod Configuration Menu
- Safe Travels

## 안전 원칙

- 게임 `Data` 폴더 직접 수정 안 함
- 기존 MO2 모드 파일 직접 수정 안 함
- 선택한 TMR MO2 인스턴스와 사용자가 지정한 한국어 리소스만 읽음
- 결과는 패쳐 폴더의 `Output`에만 생성
- 번역된 플러그인은 저장 후 다시 읽어 레코드 수와 마스터 목록을 검증
- 원본 마스터 순서를 유지

## 개발

주요 구성:

- `tmrkr.py`: MO2/TMR 인벤토리 및 안전 경로 처리
- `tmrkr_output.py`: Output 생성 및 exact/fallback 선택
- `tmrkr_gui.py`: Windows GUI
- `tmrkr_mcm.py`: MCM JSON 병합
- `tmrkr_sst.py`: xTranslator SST 파서
- `tools/TmrPluginTranslator`: Fallout 4 플러그인 번역 백엔드
- `tools/prepare_release_data.py`: 릴리즈 TranslationData 생성 도구

플러그인 백엔드는 **Mutagen.Bethesda.Fallout4**를 사용합니다.

## 라이선스 / 출처

프로그램 소스는 GPL-3.0으로 배포합니다. 자세한 내용은 `LICENSE`와 `THIRD_PARTY_NOTICES.md`를 확인하세요.

- Mutagen: GPL-3.0
- xTranslator: MPL-2.0 — SST 형식과 매칭 동작을 검토할 때 참고했으며 xTranslator 바이너리/소스는 릴리즈에 포함하지 않습니다.

Fallout, Fallout 4 및 관련 상표와 게임 데이터의 권리는 각 권리자에게 있습니다.
