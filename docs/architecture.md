# TMR Korean Patcher Architecture

## 1. 목표

패쳐는 사용자의 Fallout 4/TMR 설치를 직접 수정하지 않고, MO2에서 덮어쓸 수 있는 별도 Output을 생성한다.

최종 출력 모드는 다음 세 계층으로 분리한다.

- `TMR Korean - Base Game`: 본편/공식 DLC 한국어 리소스
- `TMR Korean - Plugins`: ESP/ESM/ESL 번역본
- `TMR Korean - MCM`: MCM JSON 및 Interface/Translations

## 2. 플러그인 적용 전략

### Exact fast path

릴리즈 시 검증한 원본 SHA-256과 사용자의 플러그인 해시가 같으면 미리 검증한 번역 payload를 그대로 사용한다.

이 경로는 가장 빠르며 런타임에서 레코드 재분석이 필요 없다.

### Updated/new fallback

해시가 달라지거나 릴리즈 이후 새 플러그인이 활성화된 경우 `TmrPluginTranslator`가 현재 플러그인을 읽고 번역을 병합한다.

우선순위:

1. 모드 전용 direct SST 매핑
2. Fallout4.esm + 공식 DLC 번역 상속

본편/DLC 상속은 owner/FormID/현재 영문 원문을 기준으로 하며, QUST/TERM처럼 같은 필드가 반복되는 레코드는 xTranslator의 REC:FIELD + rec_id 의미를 보존해 적용한다.

모드가 영문 원문을 변경한 경우 해당 항목은 자동 번역하지 않는다.

## 3. 본편/DLC fallback bank

개발 단계에서 다음 사전을 하나의 fallback bank로 생성한다.

- Fallout4.esm
- DLCRobot.esm
- DLCWorkshop01.esm
- DLCCoast.esm
- DLCWorkshop02.esm
- DLCWorkshop03.esm
- DLCNukaWorld.esm

SSU8 구형 SST는 마스터 인덱스를 공식 마스터 순서로 복원한다. Custom TXT SST 항목은 플러그인 fallback bank에서 제외한다.

## 4. MCM

SimpleMcmJsonTranslator의 신뢰된 로컬 DB는 개발 단계에서 JSON 매핑으로 내보낸다. 릴리즈 런타임은 BinaryFormatter DB를 읽지 않는다.

런타임은 현재 설치된 `config.json`을 읽고 문자열 값만 번역하므로 모드 업데이트로 추가된 설정 구조를 최대한 보존한다.

## 5. Interface/Translations

Custom TXT SST는 릴리즈 준비 단계에서 단순 source → Korean JSON으로 변환한다. 런타임에 xTranslator는 필요 없다.

Fallout 4가 영문판 베이스로 실행되므로 출력 파일명은 `*_en.txt`를 유지한다.

## 6. 본편 한국어 리소스

본편 한국어 리소스는 릴리즈에 포함하지 않는다. 사용자가 로컬 폴더를 선택하면 `Interface`, `Strings`, `Programs`을 Output에 그대로 복사한다.

파일명을 임의로 `_ko`로 바꾸지 않는다.

## 7. 저장 검증

번역 백엔드는 플러그인 저장 후 다시 읽어 다음을 확인한다.

- 레코드 FormKey 집합/개수
- 마스터 목록 및 순서
- 출력 파일 재파싱 가능 여부

원본 플러그인은 쓰기 대상으로 열지 않는다.

## 8. 배포

릴리즈 ZIP은 다음을 포함한다.

- `TMR-Korean-Patcher.exe`
- `TranslationData/catalog.json`
- exact plugin payloads
- direct mappings
- base/DLC fallback bank
- self-contained `TmrPluginTranslator.exe`
- MCM/Interface JSON mappings
- LICENSE / THIRD_PARTY_NOTICES

Python, .NET Runtime, xTranslator 설치는 릴리즈 사용자에게 요구하지 않는다.
