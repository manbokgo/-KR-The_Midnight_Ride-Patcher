"""GUI for the The Midnight Ride Korean patcher."""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import tmrkr
from tmrkr_output import build_output, BASE_MOD, PLUGIN_MOD, MCM_MOD


def program_folder() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def guess_base_package() -> str:
    candidates = [
        Path.home() / "Desktop" / "FO4_AE_1.11.191.Kor",
        Path.home() / "OneDrive" / "Desktop" / "FO4_AE_1.11.191.Kor",
    ]
    return str(next((p for p in candidates if p.is_dir()), ""))


class App:
    def __init__(self, window):
        self.window = window
        self.folder = program_folder()
        self.events = queue.Queue()
        self.output = None
        window.title(f"The Midnight Ride 한국어 패쳐 v{tmrkr.VERSION}")
        window.minsize(820, 390)

        frame = ttk.Frame(window, padding=22)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="The Midnight Ride MO2 폴더").grid(row=0, column=0, columnspan=3, sticky="w")
        default_mo2 = "C:/Modlists/TMR" if Path("C:/Modlists/TMR/ModOrganizer.ini").is_file() else ""
        self.mo2 = tk.StringVar(value=default_mo2)
        ttk.Entry(frame, textvariable=self.mo2).grid(row=1, column=0, sticky="ew", pady=(6, 14))
        ttk.Button(frame, text="찾아보기", command=self.choose_mo2).grid(row=1, column=1, padx=(8, 0), pady=(6, 14))

        ttk.Label(frame, text="Fallout 4 본편 한국어 리소스 폴더 (FO4_AE_1.11.191.Kor)").grid(
            row=2, column=0, columnspan=3, sticky="w")
        self.base = tk.StringVar(value=guess_base_package())
        ttk.Entry(frame, textvariable=self.base).grid(row=3, column=0, sticky="ew", pady=(6, 14))
        ttk.Button(frame, text="찾아보기", command=self.choose_base).grid(row=3, column=1, padx=(8, 0), pady=(6, 14))

        self.generate = ttk.Button(frame, text="Output 생성", command=self.start)
        self.generate.grid(row=4, column=0, sticky="w")
        self.open_button = ttk.Button(frame, text="Output 폴더 열기", command=self.open_output, state="disabled")
        self.open_button.grid(row=4, column=1, padx=(8, 0))

        self.status = tk.StringVar(value=(
            "원본 게임과 기존 MO2 모드는 수정하지 않습니다.\n"
            f"Output 생성 후 MO2에 {BASE_MOD}, {PLUGIN_MOD}, {MCM_MOD} 세 모드를 복사·활성화하세요."
        ))
        ttk.Label(frame, textvariable=self.status, wraplength=770, justify="left").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(18, 0))
        window.after(150, self.poll)

    def choose_mo2(self):
        folder = filedialog.askdirectory(title="ModOrganizer.ini가 있는 TMR 폴더")
        if folder:
            self.mo2.set(folder)

    def choose_base(self):
        folder = filedialog.askdirectory(title="FO4_AE_1.11.191.Kor 폴더")
        if folder:
            self.base.set(folder)

    def start(self):
        root = Path(self.mo2.get().strip())
        base = Path(self.base.get().strip())
        if not (root / "ModOrganizer.ini").is_file():
            messagebox.showerror("폴더 확인", "ModOrganizer.ini가 있는 TMR MO2 폴더를 선택해주세요.")
            return
        if not (base / "Strings").is_dir() or not (base / "Interface").is_dir():
            messagebox.showerror("한국어 리소스 확인", "올바른 FO4_AE_1.11.191.Kor 폴더를 선택해주세요.")
            return
        data = self.folder / "TranslationData"
        if not (data / "catalog.json").is_file():
            messagebox.showerror("패쳐 데이터 확인", "TranslationData/catalog.json을 찾을 수 없습니다.")
            return

        target = self.folder / "Output"
        if target.exists():
            target = self.folder / ("Output-" + datetime.now().strftime("%Y%m%d-%H%M%S"))

        self.generate.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.status.set("선택한 프로필을 검사하고 한국어 Output을 생성하고 있습니다.")

        def run():
            try:
                report = build_output(root, base, data, target)
                self.events.put(("done", target, report))
            except Exception as exc:
                self.events.put(("error", str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        try:
            event = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.generate.configure(state="normal")
            if event[0] == "error":
                self.status.set("생성에 실패했습니다. 원본 설치는 변경하지 않았습니다.")
                messagebox.showerror("생성 실패", event[1])
            else:
                _, target, report = event
                self.output = target
                exact = sum(x["status"] == "exact_payload" for x in report["plugins"])
                fallback = sum(x["status"] in {"updated_fallback", "new_inherited"} for x in report["plugins"])
                skipped = sum(x["status"] in {"known_no_translation_needed", "updated_no_match", "new_no_match"}
                              for x in report["plugins"])
                self.status.set(
                    f"완료: 빠른 적용 {exact} · 업데이트/신규 상속 {fallback} · 번역 불필요/대응 없음 {skipped}\n"
                    f"MCM {len(report['mcm'])}개 · Interface {len(report['interface'])}개\n"
                    f"{target}\n"
                    f"Output 안의 mods 폴더를 MO2 폴더로 복사하고 {BASE_MOD}, {PLUGIN_MOD}, {MCM_MOD}를 활성화하세요."
                )
                self.open_button.configure(state="normal")
        self.window.after(150, self.poll)

    def open_output(self):
        if self.output and self.output.is_dir():
            os.startfile(self.output)


def packaged_self_test(mo2_root: str, base_package: str) -> int:
    folder = program_folder()
    data = folder / "TranslationData"
    if not (data / "catalog.json").is_file():
        raise FileNotFoundError("TranslationData/catalog.json")
    if not (data / "Backend/TmrPluginTranslator.exe").is_file():
        raise FileNotFoundError("TranslationData/Backend/TmrPluginTranslator.exe")
    with tempfile.TemporaryDirectory(prefix="tmrkr-selftest-") as tmp:
        output = Path(tmp) / "Output"
        report = build_output(Path(mo2_root), Path(base_package), data, output)
        if not output.is_dir() or not report["plugins"]:
            raise RuntimeError("Output self-test failed")
        if not any(x["status"] == "exact_payload" for x in report["plugins"]):
            raise RuntimeError("Exact payload path was not exercised")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--self-test":
        raise SystemExit(packaged_self_test(sys.argv[2], sys.argv[3]))
    window = tk.Tk()
    App(window)
    window.mainloop()
