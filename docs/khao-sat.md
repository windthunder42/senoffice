# Báo cáo khảo sát mã nguồn – dự án SenOffice

> Phạm vi: **chỉ khảo sát, chưa sửa mã**. Mọi số dòng trong báo cáo ứng với
> commit `70a8dda48` (nhánh `main` của bản fork `windthunder42/senoffice`).
>
> Thương hiệu đích: **SenOffice** (bộ phần mềm) – **Sen Văn bản** (Writer),
> **Sen Bảng tính** (Calc), **Sen Trình chiếu** (Impress); mã định danh gói
> `vn.senoffice.desktop`.

Phụ lục kèm theo (thư mục `docs/khao-sat/`):

| File | Nội dung |
|---|---|
| `thuong-hieu-can-thay.csv` | **Mọi** dòng chứa "Collabora" / "LibreOffice" / "CODA" (trừ thông báo bản quyền), kèm loại và hành động đề xuất – 18 643 dòng |
| `ban-quyen-giu-nguyen.csv` | Mọi file có thông báo bản quyền / giấy phép MPL – **GIỮ NGUYÊN** – 31 857 file (32 240 dòng) |
| `anh-logo.csv` | Các file ảnh / biểu tượng mang thương hiệu – 369 file |
| `thong-ke.txt` | Số liệu tổng hợp theo loại và theo khu vực |
| `quet-thuong-hieu.py` | Script sinh lại các file trên: `python3 docs/khao-sat/quet-thuong-hieu.py . /tmp/out` |

---

## Tóm tắt nhanh

1. Repo này là **monorepo**: chứa đủ giao diện web (`browser/`), lõi C++
   (`wsd/`, `kit/`, `common/`, `net/` và toàn bộ lõi LibreOffice ở `engine/`),
   cùng các vỏ ứng dụng desktop/mobile (`windows/`, `qt/`, `macos/`,
   `android/`, `ios/`, `wasm/`). **Không cần repo nào khác** để build bản
   Windows.
2. Bản Windows ("CODA-W") là một ứng dụng Win32 C++ dùng **WebView2** để hiển
   thị giao diện web, chạy lõi trong cùng tiến trình. Build bằng
   **Visual Studio 2026 + MSYS2 + Git Bash + Node.js**. Lõi phải **tự build**
   (không có bản dựng sẵn dùng được). Máy build nên có ≥ 8 nhân, 32 GB RAM,
   ≥ 100 GB SSD; build lần đầu ước tính 2–4 giờ.
3. GitHub Actions **khó** build trọn trên runner miễn phí (giới hạn 6 giờ/job,
   ổ đĩa nhỏ). Khuyến nghị runner tự quản (self-hosted) hoặc runner lớn trả phí.
4. Thay thương hiệu: phần lớn tên hiển thị điều khiển bằng **tham số configure**
   (`--with-app-name`, `--with-vendor`, `--with-app-branding`,
   `--with-product-name`, `--with-branding`, `-identity`…), số còn lại nằm rải
   rác trong khoảng **~250 dòng hiển thị cho người dùng** ngoài phần dịch
   thuật. ~30 000 dòng là header bản quyền MPL → **không được sửa**.
5. Chạy được trên **Windows 10 (≥ 1809, bản 64-bit)**, phụ thuộc WebView2
   Runtime. Có thể đóng gói .msi/.exe (WiX hoặc Inno Setup) nhưng cần tự đăng ký
   các COM shell extension mà hiện manifest APPX đang lo.
6. **Không tìm thấy telemetry, kiểm tra cập nhật hay báo lỗi tự động** trong bản
   Windows. Các kết nối ra ngoài chủ yếu là: AI (OpenAI/Groq/Together/Mistral –
   chỉ khi người dùng nhập API key), Zotero, liên kết mở trình duyệt, tiện ích
   mở rộng, tài liệu có liên kết ngoài, và bản thân WebView2/Microsoft.
7. Có thể gỡ an toàn: AI, Zotero, công cụ quản trị server, bản WASM/Qt/macOS,
   tiện ích mẫu, chữ ký điện tử eIDEasy, bớt ngôn ngữ/từ điển… (xem mục 7).

---

## 1. Cấu trúc repo

### 1.1. Sơ đồ tổng quát

```
senoffice/
├── browser/      ← GIAO DIỆN WEB (HTML/JS/TS/CSS) – chạy trong WebView2
├── wsd/          ← LÕI ONLINE C++: "coolwsd" – điều phối tài liệu, phiên làm việc
├── kit/          ← LÕI ONLINE C++: "kit" – cầu nối tới LibreOfficeKit (vẽ ô, sự kiện)
├── common/ net/  ← LÕI ONLINE C++: tiện ích chung, socket (FakeSocket trong bản desktop)
├── engine/       ← LÕI LIBREOFFICE (C++), ~1,5 GB – trước đây là repo "core" riêng
├── windows/      ← VỎ ỨNG DỤNG WINDOWS (Win32 + WebView2, Visual Studio)
├── qt/           ← vỏ Linux (Qt6 WebEngine) + flatpak + FreeBSD port
├── macos/        ← vỏ macOS (Swift/ObjC, WKWebView)
├── android/      ← vỏ Android (Java/Kotlin, WebView)
├── ios/          ← vỏ iOS (ObjC, WKWebView)
├── wasm/         ← bản chạy trong trình duyệt bằng WebAssembly
├── cypress_test/ test/ fuzzer/   ← kiểm thử
├── debian/ docker/ snap/ nix/ coolwsd.*  ← đóng gói bản server (không cần cho desktop)
└── configure.ac, Makefile.am, autogen.sh ← hệ build autotools phần "online"
```

Dung lượng: `engine/` 1,5 GB; `browser/` 320 MB; `windows/` 612 KB; phần C++
online (`wsd`+`kit`+`common`+`net`) ~5 MB.

### 1.2. Giao diện web – `browser/`

| Thư mục | Vai trò |
|---|---|
| `browser/html/cool.html.m4` | Trang HTML chính (sinh bằng m4), nạp bundle JS |
| `browser/src/` | Mã TypeScript/JavaScript (fork từ Leaflet): `control/` (thanh công cụ, menu, notebookbar, hộp thoại JSDialog), `map/` (xử lý sự kiện, clipboard, WOPI), `canvas/` (vẽ tài liệu), `app/` (socket, tiện ích), `slideshow/`, `docdispatcher.ts` (bảng lệnh) |
| `browser/css/` | CSS; `color-palette*.css` là bảng màu (chỗ đổi màu thương hiệu) |
| `browser/images/` | ~1 350 biểu tượng SVG (`lc_*.svg`), thư mục `dark/` cho giao diện tối |
| `browser/po/`, `browser/l10n/` | Bản dịch giao diện (có `ui-vi.po`, `core-vi.po`, `help-vi.po`) |
| `browser/welcome/` | Trình chiếu chào mừng (chạy cục bộ) |
| `browser/extensions/` | Hệ thống tiện ích mở rộng (Apps-Script shim) + 6 tiện ích mẫu `com.collaboraoffice.*` |
| `browser/admin/` | Bảng quản trị server – **không dùng** trong bản desktop |
| `browser/Makefile.am` | Danh sách file JS/TS đưa vào bundle |

Bản desktop đánh dấu bằng `window.ThisIsTheWindowsApp`, `window.mode.isCODesktop()`.

### 1.3. Lõi C++

| Lớp | Vị trí | Ghi chú |
|---|---|---|
| Lõi LibreOffice ("Collabora Office engine", COKit) | `engine/` | Toàn bộ mã LibreOffice: `sw` (Writer), `sc` (Calc), `sd` (Impress/Draw), `vcl`, `sfx2`, `desktop/source/lib` (LibreOfficeKit)… Đã được Collabora đổi tên thành "Collabora Office". Bản Windows build ở chế độ `--enable-headless`, `--enable-kit-always-active` (chỉ dùng qua LibreOfficeKit, không có giao diện VCL riêng) |
| Lõi online | `wsd/`, `kit/`, `common/`, `net/` | Trong bản desktop được biên dịch **tĩnh vào chính file .exe** (xem `windows/coda/CODA/CODA.vcxproj`, danh sách `ClCompile`), giao tiếp với giao diện qua "FakeSocket" thay vì WebSocket thật |

### 1.4. Vỏ ứng dụng desktop Windows – `windows/`

| File | Vai trò |
|---|---|
| `windows/coda/CODA/CODA.cpp` (~4 900 dòng) | Toàn bộ vỏ Win32: tạo cửa sổ, tab, WebView2, scheme `cool://`, cầu nối JS↔C++, mở/lưu file, in, clipboard, kéo-thả, đăng ký shell extension ODF, AI HTTP transport |
| `windows/coda/CODA/CODA.rc`, `CODA.ico`, `Resource.h` | Tài nguyên Windows (biểu tượng `IDI_CODA`) |
| `windows/coda/CODA/CODA.vcxproj`, `windows/coda/CODA.sln` | Dự án Visual Studio (ClangCL, NuGet `Microsoft.Web.WebView2` 1.0.3719.77) |
| `windows/coda/COConvert/` | Công cụ chuyển đổi dòng lệnh |
| `windows/coda/PrintPDFAndDelete/` | Tiện ích C# in PDF |
| `windows/coda/WebDriverThing/` | Công cụ kiểm thử tự động (C#) |
| `windows/coda/AppxManifest.xml.in`, `package_appx.py`, `PackagingLayout.xml.in`, `MakePri.xml`, `Assets/` | Đóng gói APPX/MSIX |
| `windows/coda/config.h.in`, `config.props.in` | Cấu hình biên dịch (APP_NAME, đường dẫn engine) |
| `windows/coda/build/autogen.sh`, `orchestrator.mk` | Build "một lệnh" (engine → online → bundle → MSBuild) |
| `windows/.config/*.winget`, `*.vsconfig` | Cấu hình WinGet cài máy build |
| `windows/clipboard.cpp` | Clipboard |

### 1.5. Repo khác trong tổ chức CollaboraOnline?

- **Mã nguồn bản desktop Windows nằm ngay trong repo này** (thư mục
  `windows/coda`). Theo `windows/coda/README.md` (dòng 18): *"All the source
  code now lives in a single Gerrit monorepo; the former Collabora Office core
  is the `engine/` subdirectory of the `online` repo, so there is no separate
  repository to clone any more."* Tức là repo gốc là **`CollaboraOnline/online`**
  (bản phản chiếu GitHub của Gerrit `gerrit.collaboraoffice.com/online`).
- Lõi trước đây nằm ở repo **`CollaboraOnline/core`** (nhánh
  `distro/collabora/…`), nay đã gộp vào `engine/`.
- Các phần **không** có trong repo (cần tự tạo cho SenOffice):
  - **Bản dịch đầy đủ của lõi**: repo `https://gerrit.collaboraoffice.com/translations`
    (clone vào `engine/translations`), cần nếu muốn giao diện hộp thoại lõi
    bằng tiếng Việt.
  - **Gói thương hiệu (branding)** chính thức của Collabora:
    `collabora-office-brand-<phiên bản>.tar.gz` tải từ collaboraoffice.com
    (xem `snap/snapcraft.yaml:563`, `qt/flatpak/com.collaboraoffice.Office.json:991`).
    Gói này là tài sản nhãn hiệu của Collabora → **không dùng**; SenOffice cần
    tự làm thư mục branding riêng (truyền qua `--with-app-branding`).
- Lưu ý quy trình: Collabora review mã qua **Gerrit**, không qua PR GitHub; CI của
  họ chạy trên **Jenkins** (`windows/.config/jenkins.winget`). Repo chỉ có
  `.github/workflows/codeql-analysis.yml` và `notify-website.yml` – **không** có
  workflow build Windows.

---

## 2. Quy trình build bản desktop Windows

### 2.1. Công cụ và phiên bản cần cài

Lấy từ `windows/coda/README.md`, `windows/.config/*.winget`, `*.vsconfig`:

| Công cụ | Phiên bản / nguồn | Ghi chú |
|---|---|---|
| Windows | Windows 10/11 64-bit (máy build) | Bật **Developer Mode** (để tạo symlink khi giải nén) |
| Visual Studio | **2026 Community** (kênh `VisualStudio.18.Release`), workload *Desktop development with C++* + *.NET desktop development*; danh sách thành phần chính xác ở `windows/.config/2026.vsconfig` (ARM64: `2026_cross.vsconfig`) | Bắt buộc VS 2026 (`--with-visual-studio=2026` trong `engine/distro-configs/CODAWindows.conf`) |
| Git for Windows (Git Bash) | mới nhất | `core.autocrlf=false`, `protocol.version=2` |
| MSYS2 | cài vào `C:\msys64` (winget `MSYS2.MSYS2`) | Gói: `autoconf automake libtool m4 make gcc bison flex gperf nasm zip unzip gettext gettext-devel patch pkgconf python python-lxml python-pip perl` |
| Node.js | LTS, **≥ 20**, npm ≥ 9 | Build bundle giao diện |
| Strawberry Perl Portable | 5.40.0.1 (64-bit UCRT) | `--with-strawberry-perl-portable=...` |
| GNU make cho MSVC | 4.4.1 | Tải từ `gerrit.collaboraoffice.com/extern/` |
| jom | 1.1.4 | nmake song song |
| pkgconf | 2.4.3 | |
| clang-format | 5.0.0 | Chỉ để định dạng mã |
| NuGet (qua `msbuild /restore`) | `Microsoft.Web.WebView2` 1.0.3719.77 | Tự tải khi build |

Cài nhanh (theo README):

```bat
winget configure windows/.config/configuration.winget   :: Visual Studio 2026
winget configure windows/.config/admin_deps.winget      :: chạy bằng quyền admin
winget configure windows/.config/user_steps.winget      :: chạy bằng user thường
```

### 2.2. Các bước build (tóm tắt)

**Cách 1 – một lệnh** (khuyến nghị, `windows/coda/build/autogen.sh`):

```bash
mkdir C:/so-build && cd C:/so-build          # thư mục build NGOÀI mã nguồn, không dấu cách
cat > autogen.input <<'EOF'
--with-distro=CODAWindows
--host=x86_64-pc-cygwin
--with-visual-studio=2026
--with-strawberry-perl-portable=C:\Users\<user>\co\spp
--with-external-tar=C:\Users\<user>\co\co-externaltar
EOF
C:/src/senoffice/windows/coda/build/autogen.sh
make CONFIG=Release APP_NAME='SenOffice' VENDOR='SenOffice' INFO_URL='https://senoffice.vn'
```

Kết quả: `online/windows/coda/x64/Release/program/<APP_NAME>.exe` cùng engine và
file giao diện.

**Cách 2 – từng bước**: build engine (`engine/autogen.sh` + `make`) → configure
online với `--enable-windowsapp --with-app-name=... --with-lo-builddir=...
--with-lo-path=...` → `make -C browser` → `msbuild /restore
/p:Configuration=Release /p:Platform=x64 windows\coda\CODA.sln`.

Lưu ý quan trọng:
- Cấu hình **Debug** của app bắt buộc engine build với `--enable-dbgutil` hoặc
  `--enable-msvc-debug-runtime`; bản phát hành dùng `CONFIG=Release`.
- `--with-lo-builddir` là đường dẫn kiểu Unix (`/c/...`), `--with-lo-path` là
  đường dẫn Windows.
- Đường dẫn mã nguồn và thư mục build **không được chứa dấu cách**.

### 2.3. Lõi LibreOffice lấy từ đâu?

- Lõi là thư mục **`engine/`** ngay trong repo (bản LibreOffice đã được Collabora
  chỉnh sửa, phiên bản `26.04.5.1` – `engine/configure.ac:21`).
- **Phải build lại từ mã nguồn.** Lý do:
  - App liên kết với thư viện tĩnh trong `workdir` của engine (POCO, zlib, zstd,
    libpng – `windows/coda/config.props.in`, biến `EngineLibDir`) và cần
    header của đúng bản engine đó;
  - Engine được cấu hình riêng cho desktop (`CODAWindows.conf`:
    `--enable-headless`, `--enable-kit-always-active`, `--enable-mergelibs`,
    `--disable-skia`, `--enable-cairo-rgba`…), khác hoàn toàn bản cài đặt
    LibreOffice thông thường → **không dùng được LibreOffice tải từ
    libreoffice.org**;
  - Thương hiệu của lõi (tên sản phẩm, logo `brand_cp`) chỉ đổi được khi build.
- Collabora có bản dựng sẵn toàn bộ app
  (`https://www.collaboraoffice.com/downloads/Collabora-Office-Windows-Snapshot/`,
  `windows/coda/README.md:190`) nhưng đó là sản phẩm mang nhãn hiệu Collabora,
  không phải SDK tách rời; không nên dùng làm nền cho SenOffice.
- **Mã nguồn thư viện bên thứ ba** (~134 tarball trong `engine/download.lst`)
  được tải khi build từ `https://gerrit.collaboraoffice.com/src`
  (`engine/Makefile.fetch:260`). Nên tạo **bản sao nội bộ** (mirror) và trỏ
  `--with-external-tar=` để không phụ thuộc máy chủ Collabora.

### 2.4. Cấu hình máy tối thiểu & thời gian build (ước tính)

Repo không ghi số liệu chính thức; các con số dưới đây là **ước tính** dựa trên
kinh nghiệm build LibreOffice trên Windows với cấu hình tương tự
(`--enable-symbols`, không ccache, không PCH) – cần đo lại trên máy thật.

| | Tối thiểu | Khuyến nghị |
|---|---|---|
| CPU | 4 nhân / 8 luồng x64 | 8–16 nhân |
| RAM | 16 GB | 32 GB (liên kết `mergelibs` có symbols tốn RAM) |
| Ổ đĩa | 60 GB trống, SSD | 100–150 GB NVMe (engine + symbols + tarball + node_modules) |
| Hệ điều hành | Windows 10 22H2 / Windows 11 x64 | Windows 11, tắt quét Defender cho thư mục build |

| Bước | 4 nhân | 8–16 nhân |
|---|---|---|
| Cài công cụ (lần đầu) | 1–2 giờ | 1–2 giờ |
| Build engine lần đầu | 5–8 giờ | 2–4 giờ |
| Configure + bundle giao diện | 10–20 phút | 5–10 phút |
| MSBuild app | 5–15 phút | 3–8 phút |
| Build tăng dần (sửa JS/CSS) | vài phút | vài phút |

Mẹo giảm thời gian: bỏ bớt ngôn ngữ (`--with-lang=vi en-US` thay vì
`INCLUDE:Langs` 41 ngôn ngữ), tắt `--enable-symbols` cho bản phát hành không
cần gỡ lỗi, bật ccache (`config.props.in` đã hỗ trợ `CODA_CCACHE`), tắt quét
Windows Defender cho thư mục build.

### 2.5. Có build được bằng GitHub Actions không?

**Có thể, nhưng không thực tế trên runner miễn phí.** Các giới hạn (theo tài
liệu GitHub tại thời điểm viết – cần kiểm tra lại khi triển khai):

| Giới hạn | Ảnh hưởng |
|---|---|
| Mỗi job trên runner do GitHub cung cấp tối đa **6 giờ** | Build engine lần đầu trên runner 4 nhân dễ vượt 6 giờ |
| Runner Windows tiêu chuẩn: repo công khai 4 vCPU/16 GB RAM; repo **riêng tư** chỉ 2 vCPU/7–8 GB RAM; SSD đảm bảo ~14 GB | Thiếu RAM khi liên kết; dung lượng đĩa đảm bảo nhỏ hơn nhiều so với ~60 GB cần thiết (thực tế ổ C:/D: còn trống nhiều hơn nhưng không được cam kết) |
| Repo riêng tư: phút miễn phí có hạn, phút Windows tính **x2** | Một lần build đầy đủ có thể tốn 600–1 000 phút quy đổi |
| `actions/cache` tối đa **10 GB**/repo | Không chứa hết `workdir` engine; chỉ cache được ccache/tarball |
| Ảnh runner `windows-2025` có thể chưa cài **Visual Studio 2026** | Phải cài trong job (thêm 30–60 phút) – cần kiểm tra |
| Kích thước artifact/lưu trữ có hạn mức | Bản build (~1–2 GB chưa nén) tốn hạn mức |
| Repo hiện **không có** workflow build Windows | Phải tự viết từ đầu (tham khảo `jenkins.winget`) |

Phương án khuyến nghị (theo thứ tự):
1. **Self-hosted runner** Windows (máy 16 nhân/64 GB/1 TB NVMe) đăng ký vào repo:
   không giới hạn 6 giờ (giới hạn job self-hosted là 5 ngày), giữ được
   `workdir` giữa các lần build → build tăng dần vài phút.
2. **Larger runner** trả phí của GitHub (8–16 nhân) + ccache lưu qua cache.
3. Tách pipeline: job A build engine (chỉ chạy khi `engine/` thay đổi, đẩy
   `instdir` + thư viện tĩnh lên bộ lưu trữ ngoài); job B (thường xuyên) chỉ
   build giao diện + app + đóng gói (dưới 30 phút, chạy được trên runner
   thường).

---

## 3. Vị trí tên, logo, URL "Collabora" / "LibreOffice" / "CODA"

### 3.1. Số liệu tổng hợp (toàn repo)

| Loại | Số dòng / file | Hành động |
|---|---|---|
| **Thông báo bản quyền / giấy phép MPL** | 32 240 dòng trong 31 857 file | **GIỮ NGUYÊN** (`ban-quyen-giu-nguyen.csv`) |
| Chữ hiển thị (gồm cả gói FreeBSD ~3 650 dòng) | 5 574 | THAY (`thuong-hieu-can-thay.csv`) |
| Chữ trong bản dịch `.po`/`.ts` | 3 272 | THAY ở chuỗi gốc rồi sinh lại / sửa bản `vi` |
| URL (ngoài bản dịch) | 649 | THAY hoặc GỠ |
| URL trong bản dịch | 1 132 | THAY ở chuỗi gốc |
| Mã định danh gói | 169 (+33 namespace Java Android) | THAY → `vn.senoffice.desktop` |
| Ảnh / biểu tượng | 369 file | THAY (`anh-logo.csv`) |
| Định danh trong mã (không hiển thị: `LibreOfficeKit`, `CODA_*`, `isCODesktop`, `org.libreoffice.*` UNO…) | 1 745 | **KHÔNG ĐỔI** – đổi gây vỡ build/API, không ai nhìn thấy |
| Chú thích mã, dữ liệu kiểm thử, tài liệu nội bộ, siêu dữ liệu bản dịch | 6 069 | Không bắt buộc |

Phân bố theo khu vực (chỉ các dòng không phải bản quyền):

| Khu vực | Chữ | Chữ (dịch) | URL | URL (dịch) | Mã gói | Định danh mã |
|---|---|---|---|---|---|---|
| Giao diện web `browser/` | 91 | 3 127 | 13 | 1 132 | 4 | 14 |
| Vỏ Windows `windows/` | 35 | 0 | 10 | 0 | 4 | 65 |
| Lõi online C++ | 20 | 0 | 6 | 0 | 1 | 7 |
| Lõi engine | 1 089 | 0 | 387 | 0 | 45 | 1 386 |
| Vỏ Qt (Linux/FreeBSD) | 3 833 | 58 | 125 | 0 | 40 | 75 |
| Vỏ macOS | 127 | 87 | 5 | 0 | 43 | 80 |
| Vỏ Android / iOS | 23 | 0 | 10 | 0 | 24 (+33) | 44 |
| Khác (build, docker, debian, tài liệu) | 354 | 0 | 93 | 0 | 8 | 66 |

> Bảng đầy đủ **từng dòng** (đường dẫn, số dòng, loại, hành động, khu vực,
> trích đoạn) nằm trong `docs/khao-sat/thuong-hieu-can-thay.csv` – mở bằng Excel
> hoặc LibreOffice và lọc theo cột `khu_vuc` / `loai`. Phân loại được làm tự động
> bằng quy tắc; một số dòng có thể bị xếp sai loại, cần duyệt lại khi thực hiện.

### 3.2. Danh sách ưu tiên cho bản Windows (những chỗ người dùng nhìn thấy)

Ký hiệu loại: **C** = chữ, **A** = ảnh, **U** = URL, **ID** = mã định danh gói,
**CFG** = tham số build (đổi bằng cấu hình, không cần sửa mã).

#### a) Tham số build – đổi ở đây là đổi được phần lớn tên hiển thị

| File | Dòng | Loại | Hiện tại | Đề xuất |
|---|---|---|---|---|
| `windows/coda/build/orchestrator.mk` | 25 | CFG/C | `APP_NAME ?= Collabora Office` | `SenOffice` (tên cửa sổ, tên .exe, thư mục `%LocalAppData%`) |
| `windows/coda/build/orchestrator.mk` | 26 | CFG/U | `INFO_URL ?= https://example.com/coda/info.html` | URL trang SenOffice |
| `windows/coda/build/orchestrator.mk` | 27 | CFG/C | `VENDOR ?=` | `SenOffice` |
| `engine/distro-configs/CODAWindows.conf` | 18 | CFG/A | `--with-branding=icon-themes/galaxy/brand_cp` | thư mục logo SenOffice |
| `engine/distro-configs/CODAWindows.conf` | 19 | CFG/C | `--with-vendor=Collabora Productivity Limited` | `--with-vendor=SenOffice` |
| `engine/distro-configs/CODAWindows.conf` | (thêm) | CFG/C | không có `--with-product-name` → mặc định lấy từ `AC_INIT` | thêm `--with-product-name=SenOffice` (thay `%PRODUCTNAME` trong mọi hộp thoại lõi) |
| `engine/configure.ac` | 21 | C/U | `AC_INIT([Collabora Office],[26.04.5.1],[],[],[https://www.collaboraoffice.org/])` | giữ nguyên nếu đã dùng `--with-product-name`; hoặc đổi tên/URL |
| `configure.ac` | 6 | U | `AC_INIT([coolwsd], …, [https://github.com/CollaboraOnline/online/issues], …, [https://www.collaboraoffice.org/])` | URL báo lỗi/trang chủ SenOffice |
| `configure.ac` | 273–277 | CFG | `--with-app-branding=<path>` (thư mục `branding.css`, logo, `welcome/`) | tạo thư mục branding SenOffice và truyền vào (`ONLINE_CONFIGURE_ARGS`) |
| `configure.ac` | 1213, 1215 | ID | `com.collabora.office.Mobile`, `org.collabora.app` | `vn.senoffice.desktop` (dùng `--with-app-package-name`) |
| `configure.ac` | 1228 | C | `APP_NAME="Collabora Online Development Edition"` | mặc định khi không truyền `--with-app-name` |
| `configure.ac` | 1258 | U | `INFO_URL='https://www.collaboraoffice.org/'` | URL SenOffice |
| `configure.ac` | 1449 | U | `brandProductURL … https://www.collaboraonline.com` | URL SenOffice hoặc để trống |
| `configure.ac` | 2782 | U | `UNLOCK_LINK="https://www.collaboraonline.com/subscriptions/"` | để trống |

#### b) Vỏ Windows và đóng gói

| File | Dòng | Loại | Nội dung |
|---|---|---|---|
| `windows/coda/AppxManifest.xml.in` | 10 | ID | `<Identity Name="%IDENTITY" … Publisher="CN=E9F172FF-9203-4DB8-A589-184C7A58C071">` – Publisher là của Collabora trên Microsoft Store |
| `windows/coda/AppxManifest.xml.in` | 13 | C | `<PublisherDisplayName>Collabora Productivity Ltd</PublisherDisplayName>` |
| `windows/coda/AppxManifest.xml.in` | 28 | ID | `<Application Id="CODA" …>` |
| `windows/coda/AppxManifest.xml.in` | 44, 47, 50 | C | `Collabora Office Thumbnail Handler / Property Handler / ODF Filter` |
| `windows/coda/package_appx.py` | 243 | ID | `PACKAGE_ID = 'CODA'` |
| `windows/coda/package_appx.py` | 263 | ID | `'CollaboraProductivityLtd.CollaboraOfficeDesktop'` → `vn.senoffice.desktop` |
| `windows/coda/package_appx.py` | 264 | C | `'Collabora Office Desktop'` |
| `windows/coda/package_appx.py` | 265 | C | `'Collabora Office.exe'` |
| `windows/coda/package_appx.py` | 327 | ID | `<uap:Protocol Name="vnd.libreoffice.command"/>` (giao thức dùng chung với LibreOffice – cân nhắc giữ) |
| `windows/coda/CODA/CODA.cpp` | 210, 213, 216, 4812 | C | Tên lớp cửa sổ `L"CODA"`, `CODADropOverlayWindow`, `CODAHiddenOwnerWindow` (không hiển thị, nhưng lộ trong công cụ hệ thống) |
| `windows/coda/CODA/CODA.cpp` | 2369 | C | `"Collabora Office ODF IFilter Persistent Handler"` (ghi vào registry) |
| `windows/coda/CODA/CODA.cpp` | 3651 | C | User-Agent HTTP `WinHttpOpen(L"CODA", …)` |
| `windows/coda/CODA/CODA.cpp` | 4782 | C | Tên log `Log::initialize("CODA", …)` |
| `windows/coda/CODA/CODA.rc` | (IDI_CODA) | A | `IDI_CODA ICON "CODA.ico"` |
| `windows/coda/CODA/CODA.ico` | – | A | Biểu tượng ứng dụng |
| `windows/coda/Assets/*.png` (9 file) | – | A | `logo.png`, `Square150x150Logo.png`, `Square44x44Logo*.png` |
| `windows/coda/CODA/CODA.vcxproj` | 25 | C | `<RootNamespace>CODA</RootNamespace>` (không hiển thị) |
| `windows/coda/README.md` | 4–190 | C/U | Tài liệu build (12 dòng) |
| `windows/.config/*.winget` | 18–73 | C/U | Mô tả cấu hình, URL tải công cụ từ `gerrit.collaboraoffice.com/extern` |
| `favicon.ico` | – | A | Favicon gốc repo |

#### c) Giao diện web hiển thị trong app

| File | Dòng | Loại | Nội dung |
|---|---|---|---|
| `browser/src/control/backstage/Sidebar.tsx` | 75 | C | `<span class="backstage-header-title">Collabora Office</span>` – **tiêu đề màn hình "Tệp" (backstage)** |
| `browser/css/backstage.css` | 81 | A | `url('images/collabora-office-white.svg')` – logo backstage |
| `browser/images/collabora-office-white.svg` | – | A | Logo trắng |
| `browser/images/lc_about.svg`, `browser/images/dark/lc_about.svg` | – | A | Biểu tượng "Giới thiệu" |
| `browser/images/coda-collab-*.svg` (6 file) | – | A | Hình minh họa hộp thoại cộng tác (tên file có "coda", nội dung không có logo) |
| `browser/html/cool.html.m4` | 269 | C | `<h1 id="product-name">Collabora Online</h1>` |
| `browser/src/control/Control.AboutDialog.ts` | 125–127 | C | Tên mặc định `'Collabora Online Development Edition (unbranded)'` khi không có `brandProductName` |
| `browser/src/control/Control.AboutDialog.ts` | 147 | U | Liên kết `https://gerrit.collaboraoffice.com/plugins/gitiles/online/+log/<hash>` |
| `browser/src/control/Toolbar.js` | 807 | C | Tên mặc định "(unbranded)" |
| `browser/src/layer/marker/ProgressOverlay.js` | 33 | C | Tên mặc định "(unbranded)" trên màn hình tải |
| `browser/src/map/Clipboard.js` | 1586 | C | Tên mặc định "(unbranded)" |
| `browser/src/map/handler/Map.WOPI.js` | 244 | C | `'Collabora Online'` mặc định |
| `browser/src/control/Control.LokDialog.js` | 305 | C | Thay `'Collabora Office'` trong tiêu đề hộp thoại lõi bằng `brandProductName` |
| `browser/src/control/Control.Zotero.js` | 1543 | C | `_('Unlinking citations will prevent Collabora Online …')` |
| `browser/src/map/handler/Map.VersionBar.js` | 50 | C | `_('Your Collabora Online server needs updating…')` |
| `browser/src/app/Util.ts` | 226 | U | `https://www.collaboraoffice.org/post/faq/` |
| `browser/src/control/Control.Menubar.ts` | 2741 | U | Báo lỗi: `https://github.com/CollaboraOnline/online/issues` |
| `browser/src/control/Control.Menubar.ts` | 2743 | U | Diễn đàn: `https://forum.collaboraonline.com` |
| `browser/src/canvas/sections/FormulaErrorHelpSection.ts` | 81 | U | Trợ giúp hàm: `https://help.collaboraoffice.com/` |
| `browser/src/slideshow/PresenterConsole.js` | 1095 | U | `https://collaboraonline.com` |
| `browser/src/control/Control.ServerAuditDialog.ts` | 60–198 | U | 15 liên kết `sdk.collaboraonline.com` (hộp thoại kiểm tra server – không dùng ở desktop) |
| `browser/welcome/welcome.html` | 9, 27, 28, 38, 39, 49, 50, 60 | C/U | Trình chiếu chào mừng "Collabora Online Development Edition" + liên kết – **thay bằng thư mục `welcome/` trong branding SenOffice** |
| `browser/descriptions/google-play.html` | 6–66 | C/U/ID | Mô tả trên Google Play (dùng cho Android sau này) |
| `browser/package.json` | 4, 51, 56 | C/U | Mô tả gói npm (không hiển thị) |
| `browser/po/*.po`, `browser/po/ui-vi.po` | nhiều | C/U | Bản dịch chứa "Collabora" – sửa chuỗi gốc + bản `vi` |
| `browser/extensions/com.collaboraoffice.*` | – | ID | 6 tiện ích mẫu – đề xuất gỡ (mục 7) |

#### d) Lõi C++ online và engine (hiển thị trong app)

| File | Dòng | Loại | Nội dung |
|---|---|---|---|
| `wsd/AIChatSession.cpp` | 114 | C | Lời nhắc hệ thống AI: `"You are a helpful assistant for Collabora Online."` |
| `wsd/COOLWSD.cpp` | 2787, 2952 | C/U | Thông điệp dòng lệnh (chế độ server) |
| `wsd/FileServer.cpp` | 1810 | U | CSP `img-src https://www.collaboraoffice.com/` (chế độ server) |
| `engine/icon-themes/galaxy/brand_cp/` | 8 file | A | `about.svg`, `intro.png`, `intro-highres.png`, `logo.svg`, `logo-sc.svg` (+ `_inverted`) – logo lõi |
| `engine/icon-themes/galaxy/brand_cp_snapshot/`, `engine/icon-themes/colibre/brand/` | 16 file | A | Biến thể logo |
| `engine/sysui/desktop/icons/` | 280 file | A | Biểu tượng loại tài liệu/ứng dụng của lõi (dùng cho bản cài đặt LibreOffice cổ điển, bản Windows CODA chủ yếu dùng `windows/coda/Assets`) |
| `engine/readlicense_oo/` | 26 | C | Văn bản giấy phép/readme đi kèm – xem kỹ, phần giấy phép giữ nguyên |
| `engine/officecfg/registry/data/...` | xem CSV | C/U | Cấu hình mặc định có URL Collabora |

Các vỏ khác (Qt, macOS, Android, iOS): xem CSV, lọc `khu_vuc`. Điểm chính khi
làm Android/iOS sau này: `android/app/appSettings.gradle.in:12` (`applicationId`),
`android/app/build.gradle:9` và `android/lib/build.gradle:9` (namespace
`org.libreoffice.*`), `ios/Mobile.xcodeproj/project.pbxproj:4147, 4213, 4243`
(`PRODUCT_BUNDLE_IDENTIFIER`), `ios/ExportOptions/cpci.plist:11, 13`,
`android/app/src/main/res/mipmap-*/ic_launcher.png`, `macos/coda/coda/Assets.xcassets/AppIcon.appiconset/`.

### 3.3. Những chỗ bắt buộc GIỮ NGUYÊN (bản quyền / giấy phép)

Giấy phép MPL 2.0 (mục 3.3–3.4) **cấm xóa hoặc thay đổi nội dung các thông báo
bản quyền, giấy phép, miễn trừ** trong mã nguồn. Ngoài ra LGPL/GPL của một số
thư viện và các giấy phép bên thứ ba cũng yêu cầu giữ ghi công. Cụ thể:

| Mẫu thông báo | Số file | Ví dụ |
|---|---|---|
| `This file is part of the Collabora Office project.` + đoạn MPL 2.0 | 30 229 | gần như mọi file trong `engine/` |
| `Copyright the Collabora Online contributors.` + `SPDX-License-Identifier: MPL-2.0` | 1 188 | `browser/src/docdispatcher.ts:5`, `windows/coda/CODA/CODA.cpp` |
| `Copyright the Collabora Office contributors.` | 363 | `engine/…` |
| `This file is part of the LibreOffice project.` | 49 | `engine/…` |
| Văn bản giấy phép / ghi công bên thứ ba | 24 | `COPYING`, `engine/COPYING*`, `THIRDPARTYLICENSES`, `CODA-THIRDPARTYLICENSES.html`, `SBOM.md`, `README.FILENOTICES.md`, `AUTHORS`, `browser/LICENSE`, `debian/copyright`, `browser/admin/font/OFL.txt` |

Danh sách đầy đủ từng file: `docs/khao-sat/ban-quyen-giu-nguyen.csv`.

Quy tắc khi thay thương hiệu:
- **Không** dùng tìm-thay hàng loạt "Collabora" → "SenOffice" trên toàn repo: sẽ
  phá hỏng header bản quyền (vi phạm MPL) và các định danh API.
- File **mới** do SenOffice viết có thể thêm dòng
  `Copyright the SenOffice contributors.` cùng header MPL; file **sửa đổi** giữ
  header cũ, có thể bổ sung dòng copyright của SenOffice bên dưới.
- Trong hộp thoại "Giới thiệu" nên ghi rõ: *"SenOffice dựa trên Collabora Online
  và LibreOffice"* – vừa đúng giấy phép, vừa không gây nhầm lẫn nhãn hiệu.
- "Collabora", "Collabora Office", "LibreOffice" là **nhãn hiệu**: phải gỡ khỏi
  tên sản phẩm, logo, mã định danh gói; chỉ được nhắc đến dưới dạng ghi công
  ("dựa trên…").

---

## 4. Thêm nút lệnh mới trên thanh công cụ Sen Văn bản

### 4.1. Cơ chế

Thanh công cụ dạng tab ("notebookbar") của Writer được khai báo bằng JSON trong
`browser/src/control/Control.NotebookbarWriter.js`:
- `getHomeTab()` (dòng 649), `getInsertTab()` (dòng 1286)…; mỗi phần tử có
  `id`, `type`, `text`, `command`.
- `type: 'bigtoolitem'` với `command: '.uno:XXX'` → gửi lệnh UNO thẳng vào lõi.
- `type: 'bigcustomtoolitem'` → khi bấm, gọi `app.dispatcher.dispatch(command)`
  (`browser/src/control/jsdialog/Widget.Toolitem.ts:82-106`), tức là chạy hàm JS
  đã đăng ký trong `actionsMap` của `browser/src/docdispatcher.ts`.
- Biểu tượng: nếu không khai báo `icon`, tên biểu tượng tự suy ra từ `command`
  (`app.LOUtil.getIconNameOfCommand`, `browser/src/app/LOUtil.ts:485`) →
  `browser/images/lc_<command viết thường>.svg` (bản tối: `browser/images/dark/`).
- Chèn nội dung có định dạng: gửi thông điệp `paste mimetype=text/html` qua
  socket, giống cách khung AI chèn văn bản
  (`browser/src/control/Control.AIChatSidebar.ts:2951-2970`).
- Chế độ thanh công cụ cổ điển (compact) khai báo ở
  `browser/src/control/Control.TopToolbar.js`; menu ở `Control.Menubar.ts`.

### 4.2. Ví dụ: nút "Chèn mẫu văn bản theo NĐ 30/2020"

**Bước 1 – Khai báo nút** trong tab "Chèn" (`Control.NotebookbarWriter.js`,
hàm `getInsertTab`, ngay sau nhóm `insert-page-control` ~dòng 1310):

```js
			{ type: 'separator', id: 'insert-insertpagebreak-break', orientation: 'vertical' },
			{
				'id': 'insert-nd30-template',
				'type': 'bigcustomtoolitem',
				'text': _('Mẫu NĐ 30/2020'),
				'command': 'insertnd30template',
				// icon tự suy ra: images/lc_insertnd30template.svg
				'accessibility': { focusBack: true, combination: 'N3', de: null }
			},
			{ type: 'separator', id: 'insert-nd30-template-break', orientation: 'vertical' },
```

(`text` nên viết bằng tiếng Anh rồi dịch trong `browser/po/ui-vi.po` nếu muốn giữ
cơ chế đa ngôn ngữ; ở đây ghi tiếng Việt trực tiếp cho dễ hiểu.)

**Bước 2 – Đăng ký hành động** trong hàm khởi tạo của `Dispatcher`
(`browser/src/docdispatcher.ts`, cạnh `this.actionsMap['remotelink']` dòng 106):

```ts
		this.actionsMap['insertnd30template'] = function () {
			if (app.map.getDocType() !== 'text') return;
			// Phần đầu văn bản hành chính theo Phụ lục I, Nghị định 30/2020/NĐ-CP:
			// bảng 2 cột không viền, phông Times New Roman.
			const html =
				'<table style="width:100%;border-collapse:collapse;font-family:\'Times New Roman\'">' +
				'<tr>' +
				'<td style="width:40%;text-align:center;vertical-align:top">' +
				'<p style="margin:0;font-size:13pt">TÊN CƠ QUAN CHỦ QUẢN</p>' +
				'<p style="margin:0;font-size:13pt"><b>TÊN CƠ QUAN BAN HÀNH</b></p>' +
				'<p style="margin:0;font-size:13pt">Số: &nbsp;&nbsp;&nbsp;/&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;&nbsp;&nbsp;</p></td>' +
				'<td style="width:60%;text-align:center;vertical-align:top">' +
				'<p style="margin:0;font-size:13pt"><b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b></p>' +
				'<p style="margin:0;font-size:14pt"><b><u>Độc lập - Tự do - Hạnh phúc</u></b></p>' +
				'<p style="margin:0;font-size:14pt"><i>…, ngày … tháng … năm …</i></p></td>' +
				'</tr></table>' +
				'<p style="text-align:center;font-family:\'Times New Roman\';font-size:14pt"><b>TÊN LOẠI VĂN BẢN</b></p>' +
				'<p style="text-align:center;font-family:\'Times New Roman\';font-size:14pt"><b>Trích yếu nội dung văn bản</b></p>' +
				'<p style="text-align:justify;font-family:\'Times New Roman\';font-size:14pt">Nội dung văn bản …</p>';

			const header = 'paste mimetype=text/html;charset=utf-8\n';
			if (window.ThisIsAMobileApp) {
				// Bản desktop/mobile dùng cầu nối chỉ nhận chuỗi → mã hóa base64
				// (ChildSession::paste ở kit/ tự giải mã), giống Control.AIChatSidebar.ts.
				const utf8 = new TextEncoder().encode(html);
				const b64 = window.btoa(Array.from(utf8, (b) => String.fromCodePoint(b)).join(''));
				app.socket.sendMessage(header + b64);
			} else {
				app.socket.sendMessage(new Blob([header, html]));
			}
			app.map.focus();
		};
```

**Bước 3 – Biểu tượng**: thêm `browser/images/lc_insertnd30template.svg` (24×24)
và `browser/images/dark/lc_insertnd30template.svg`. `browser/Makefile.am:148`
tự quét mọi `.svg` trong `browser/images` nên không phải khai báo thêm.

**Bước 4 – (tuỳ chọn) Thêm vào menu** `Control.Menubar.ts`, mục "Insert" của
Writer: `{name: _('Mẫu NĐ 30/2020'), id: 'insertnd30template', type: 'action'}`
– menu `type: 'action'` cũng đi qua `app.dispatcher.dispatch(id)`.

**Bước 5 – Build và thử**: `make -C browser` (hoặc `make` ở thư mục build) rồi
chạy lại app; vào tab **Chèn** → bấm **Mẫu NĐ 30/2020**.

Hướng mở rộng tốt hơn cho bản thật:
- Lưu mẫu thành file `.ott` (định dạng mẫu ODF, có sẵn kiểu đoạn, lề trang
  30-35/20-25 mm, khổ A4 đúng NĐ 30) trong thư mục mẫu của app, rồi mở tài liệu
  mới từ mẫu thay vì dán HTML; HTML dán vào chỉ giữ được định dạng cơ bản.
- Nếu tạo file TS mới (ví dụ `src/control/SenTemplates.ts`) thì phải thêm vào
  **cả hai** danh sách trong `browser/Makefile.am` (quanh dòng 751 và 1650).

---

## 5. Chạy trên Windows 10 và đóng gói .exe/.msi

### 5.1. Khả năng chạy trên Windows 10

| Hạng mục | Hiện trạng | Kết luận |
|---|---|---|
| Phiên bản tối thiểu khai báo | `windows/coda/AppxManifest.xml.in:20`: `MinVersion="10.0.17763.0"` (Windows 10 **1809**), `MaxVersionTested="10.0.22621.0"` | Hỗ trợ Windows 10 từ 1809 |
| Mốc chính thức của lõi | `engine/README.md:37`: *"Runtime: Windows 10"* | Phù hợp |
| API Windows dùng trong `CODA.cpp` | `DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2` (dòng 4724, cần ≥ 1703), `PROC_THREAD_ATTRIBUTE_DESKTOP_APP_POLICY` (dòng 2436, ≥ 1703), `DWMWA_USE_IMMERSIVE_DARK_MODE` (dòng 2114, chỉ có hiệu lực từ 20H1; bản cũ hơn chỉ không có thanh tiêu đề tối) | Không có API chỉ-Windows-11 |
| Kiến trúc | x64 (và ARM64 qua `2026_cross.vsconfig`) | **Không hỗ trợ Windows 32-bit** |
| WebView2 Runtime | Bắt buộc; nếu thiếu, `CreateCoreWebView2EnvironmentWithOptions` lỗi và app thoát (`CODA.cpp:2571-2579`, gọi `fatal`) | Windows 11 có sẵn; Windows 10 đa số đã được cài qua Windows Update/Edge, nhưng **không đảm bảo** (máy LTSC, máy không có mạng) → bộ cài phải tự cài WebView2 |
| VC++ runtime | Manifest phụ thuộc `Microsoft.VCLibs.140.00.UWPDesktop` | Bộ cài .exe/.msi phải kèm VC++ Redistributable x64 |

Lưu ý vòng đời: Windows 10 đã hết hỗ trợ thường kỳ từ 14/10/2025 (chỉ còn ESU
có trả phí). Microsoft cho biết vẫn tiếp tục cập nhật WebView2 Runtime trên
Windows 10 thêm một thời gian sau mốc này – cần kiểm tra mốc cụ thể trên trang
của Microsoft trước khi cam kết hỗ trợ dài hạn. Khuyến nghị kiểm thử trên
Windows 10 22H2 x64 sạch (không có Edge cập nhật) và Windows 10 LTSC 2019/2021.

### 5.2. Hiện trạng đóng gói APPX/MSIX

`windows/coda/package_appx.py` dùng `MakeAppx.exe`, `MakePri.exe`, `SignTool.exe`
(Windows SDK) để tạo gói APPX từ thư mục `program/`; manifest khai báo:
liên kết loại file ODF/OOXML (sinh tự động từ bộ lọc của lõi), giao thức
`ms-word`, `ms-excel`, `ms-powerpoint`, `ms-visio`, `vnd.libreoffice.command`,
và 3 COM shell extension (thumbnail, property, IFilter) chạy qua
`com:SurrogateServer` (`AppxManifest.xml.in:39-50`). `package_appx.py` còn sửa
`bootstrap.ini` để đặt `UserInstallation=$SYSUSERCONFIG/<distname>/appx`.

Nhược điểm cho SenOffice: cần chứng chỉ ký tin cậy hoặc Microsoft Store; nhiều
cơ quan nhà nước chặn cài APPX ngoài Store; không cài cho mọi người dùng (per-machine) dễ dàng.

### 5.3. Đóng gói thành .msi hoặc .exe

Đầu vào: thư mục `online/windows/coda/x64/Release/program/` (exe + engine + giao
diện) sau khi build Release.

**Phương án A – MSI bằng WiX Toolset (v5/v6)** – hợp với triển khai qua GPO/Intune/SCCM:
1. Thu thập file: dùng `wix` harvest (hoặc `heat` ở WiX 3) cho cả thư mục
   `program/` (hàng nghìn file) → `ComponentGroup`.
2. Khai báo `Package Name="SenOffice" Manufacturer="SenOffice"
   UpgradeCode="<GUID cố định>"`, cài vào `[ProgramFiles64Folder]SenOffice`.
3. Lối tắt Start Menu: "SenOffice", và nếu muốn 3 lối tắt "Sen Văn bản / Sen Bảng
   tính / Sen Trình chiếu" (hiện `CODA.cpp:4823` chỉ nhận danh sách file; muốn mở
   thẳng tài liệu trống từng loại cần thêm tham số dòng lệnh, ví dụ
   `--new-writer`, vì giao diện đã có hành động `new-*` – `docdispatcher.ts:1581`).
4. Liên kết loại file: `ProgId` + `Extension` cho `.odt .ods .odp .docx .xlsx
   .pptx .doc .xls .ppt …` (tái sử dụng danh sách mà `package_appx.py` sinh ra).
5. **Shell extension**: tự đăng ký `HKLM\Software\Classes\CLSID\{…}\InprocServer32`
   cho 3 DLL thumbnail/property/IFilter (CLSID trong
   `engine/shell/source/win32/shlxthandler/`), vì không còn manifest APPX làm việc
   này. Hàm `registerOdfShellExtensions()` (`CODA.cpp:2317`) hiện viết khóa
   HKCU qua `reg.exe` để thoát "silo" của APPX – với MSI có thể chuyển phần này
   vào bộ cài và bỏ khỏi app.
6. Phụ thuộc: dùng **WiX Burn bundle** (.exe) để chuỗi cài
   `vc_redist.x64.exe` và **WebView2 Evergreen Bootstrapper**
   (`MicrosoftEdgeWebview2Setup.exe /silent /install`) hoặc **Evergreen
   Standalone** (cài offline). Kiểm tra đã có WebView2 bằng khóa
   `HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}`
   (giá trị `pv`).
7. Ký số Authenticode (`signtool sign /fd SHA256 /tr <timestamp>`) cả exe, dll và
   msi để tránh cảnh báo SmartScreen.

**Phương án B – .exe bằng Inno Setup 6** – đơn giản, nhanh làm:

```iss
[Setup]
AppId={{<GUID>}
AppName=SenOffice
AppPublisher=SenOffice
DefaultDirName={autopf}\SenOffice
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputBaseFilename=SenOffice-Setup-x64
SignTool=signtool

[Files]
Source: "build\program\*"; DestDir: "{app}\program"; Flags: recursesubdirs ignoreversion
Source: "redist\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "redist\MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\SenOffice"; Filename: "{app}\program\SenOffice.exe"

[Registry]
Root: HKA; Subkey: "Software\Classes\.odt\OpenWithProgids"; ValueType: string; ValueName: "SenOffice.odt"; ValueData: ""
Root: HKA; Subkey: "Software\Classes\SenOffice.odt\shell\open\command"; ValueType: string; ValueData: """{app}\program\SenOffice.exe"" ""%1"""
; … lặp lại cho các phần mở rộng khác

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; Check: not IsWebView2Installed
```

**Những điểm phải sửa trong mã khi bỏ APPX** (ước lượng nhỏ, làm ở giai đoạn sau):
- Thay `UserInstallation` trong `bootstrap.ini` (đang do `package_appx.py:307`
  sửa) bằng `$SYSUSERCONFIG/SenOffice`.
- Đăng ký shell extension như trên.
- **Cập nhật phần mềm**: bản APPX dựa vào Store; bản .exe/.msi **không có** cơ chế
  tự cập nhật – chọn: phát hành qua WinGet/Intune, hoặc tự viết trình cập nhật
  (lưu ý mâu thuẫn với mục 6 "không gửi dữ liệu ra ngoài").
- `engine/msicreator/` và `engine/instsetoo_native/` là công cụ tạo MSI của
  LibreOffice cổ điển – **không** áp dụng trực tiếp cho app này, chỉ để tham khảo.

---

## 6. Các điểm gửi dữ liệu ra ngoài và cách tắt

### 6.1. Kết luận chính

- **Không có telemetry / thống kê sử dụng** trong mã bản Windows (đã tìm
  `telemetry`, `matomo`, `piwik`, `sentry`, `analytics`… – không có kết quả trong
  phần được build).
- **Không có kiểm tra cập nhật tự động**: `COOLWSD::processFetchUpdate`
  (`wsd/COOLWSD.cpp:4017-4060`, gọi `INFOBAR_URL`) nằm trong `#if !MOBILEAPP`
  nên không được biên dịch vào bản desktop; `windows/coda/config.h.in` để
  `INFOBAR_URL`, `FEEDBACK_URL` là `#undef`, `WELCOME_URL ""`, `HELP_URL ""`.
  Lõi engine của fork này không còn tùy chọn `--enable-online-update`.
- **Không có báo lỗi tự động (crash report)**: không có breakpad/crashreporter
  trong cấu hình `CODAWindows.conf`.
- Trình chiếu chào mừng tải **cục bộ** (`browser/src/map/handler/Map.Welcome.js:22-34`,
  dòng gọi `welcomeUrl` từ xa đã bị chú thích).

### 6.2. Bảng các điểm kết nối ra ngoài

| # | Điểm kết nối | Vị trí trong mã | Khi nào xảy ra | Cách tắt |
|---|---|---|---|---|
| 1 | **Dịch vụ AI**: `api.openai.com`, `api.groq.com`, `api.together.xyz`, `api.mistral.ai`, hoặc URL tùy chỉnh – gửi **nội dung tài liệu/đoạn chọn** và API key | `windows/coda/CODA/CODA.cpp:3632` (`winHttpRequest`), `:3748`, `:3776-3798`; `wsd/AIUtil.cpp:66-69`; `wsd/AIChatSession.cpp`; `common/AIHttpTransport.cpp`; giao diện `browser/src/control/Control.AIChatSidebar.ts`, `Notebookbar.AIAssistantTab.ts` | Chỉ khi người dùng tự nhập API key và dùng tính năng AI | Gỡ lời gọi `registerAIHttpTransport()` (`CODA.cpp:4840`); giữ `window.showAISidebar=false`, `window.showAINotebookbar=false` (`browser/js/global.js:302,304`) và ẩn mục cài đặt AI; triệt để: bỏ `AIChatSession.cpp`, `AIUtil.cpp`, `AIHttpTransport.cpp` khỏi `CODA.vcxproj` |
| 2 | **Zotero** (`api.zotero.org`, `www.zotero.org/styles`) – gửi API key, mã người dùng | `browser/src/control/Control.Zotero.js:154-1460` | Khi người dùng nhập Zotero API key | Đặt `window.zoteroEnabled = false` (`browser/js/global.js:308`) |
| 3 | **Chữ ký điện tử eIDEasy** (`id.eideasy.com`) | `browser/src/control/Control.ESignature.ts:57-311`, `wsd/ClientRequestDispatcher.cpp:2451` | Chỉ khi được cấu hình nhà cung cấp eIDEasy | Bỏ cấu hình; nếu chỉ dùng chữ ký số bằng chứng thư trên máy thì giữ `documentSigningEnabled` nhưng gỡ luồng eIDEasy |
| 4 | **Liên kết mở trình duyệt ngoài** (không tự gửi dữ liệu, chỉ khi người dùng bấm): GitHub issues, forum, help.collaboraoffice.com, collaboraonline.com, gerrit, FAQ, INFO_URL | `Control.Menubar.ts:2741,2743`; `FormulaErrorHelpSection.ts:81`; `PresenterConsole.js:1095`; `Control.AboutDialog.ts:147`; `Util.ts:226`; `orchestrator.mk:26`; `welcome/welcome.html`; mở bằng `ShellExecuteW` (`CODA.cpp:1056`) | Người dùng bấm | Thay bằng URL SenOffice hoặc gỡ mục menu |
| 5 | **Tiện ích mở rộng (Apps Script shim)** – script có thể gọi `UrlFetchApp` tới URL bất kỳ | `browser/src/control/Control.Extension.ts:1700-1760` (`fetch(url, …)`) | Khi tiện ích có mã gọi mạng | Gỡ tiện ích mẫu; nếu giữ hệ thống tiện ích thì chặn `fetch` ra ngoài hoặc chỉ cho phép danh sách trắng |
| 6 | **Nội dung tài liệu**: ảnh/OLE liên kết từ URL, liên kết ngoài, hàm Calc `WEBSERVICE()`/`FILTERXML`, liên kết DDE | Lõi engine (`engine/sc/source/core/tool/interpr7.cxx:244`, …) | Khi mở tài liệu có liên kết ngoài (mặc định "cập nhật khi được hỏi") | Đặt cấu hình mặc định trong `engine/officecfg`: `Calc/Content/Update/Link = 1` (never) (`Calc.xcs:266`), `Writer/Content/Update/Link` (`Writer.xcs:776`) = never, `Common/Security/Scripting/BlockUntrustedRefererLinks = true` (`Common.xcs:2068`), `DisableActiveContent = true` (`Common.xcs:2103`) |
| 7 | **WebView2 / Microsoft Edge Runtime**: tự cập nhật runtime (EdgeUpdate), dữ liệu chẩn đoán theo cài đặt Windows, SmartScreen | `CODA.cpp:2539-2590` (tạo môi trường WebView2, `AdditionalBrowserArguments` dòng 2558) | Ngầm, do Microsoft | Dùng **Fixed Version runtime** đóng kèm app (không qua EdgeUpdate); tắt kiểm tra danh tiếng (`ICoreWebView2Settings8::put_IsReputationCheckingRequired(FALSE)`); cân nhắc thêm cờ Chromium vào `AdditionalBrowserArguments` (cần thử nghiệm, WebView2 không đảm bảo hỗ trợ mọi cờ); chính sách nhóm của Edge WebView2 cho máy cơ quan |
| 8 | **Phông chữ / tài nguyên CDN** | Không tìm thấy tải phông/JS từ CDN trong `cool.html.m4`; mọi tài nguyên phục vụ qua scheme `cool://` cục bộ | – | – |
| 9 | **Thời điểm build (không phải lúc chạy)**: tarball từ `gerrit.collaboraoffice.com/src` (`engine/Makefile.fetch:260`); npm registry (`browser/npm-shrinkwrap.json.in`); NuGet (`msbuild /restore`, gói WebView2); công cụ từ `gerrit.collaboraoffice.com/extern`, `download.qt.io` (`windows/.config/admin_deps.winget`); bản dịch từ `gerrit.collaboraoffice.com/translations` | Máy build | Tạo mirror nội bộ: `--with-external-tar`, registry npm nội bộ, nguồn NuGet nội bộ |

Các tính năng ở chế độ server (WOPI, Smart Picker `remotelink`, cộng tác
`/co/collab`, DeepL – `window.deeplEnabled=false` ở `global.js:298`) không hoạt
động khi bản Windows chỉ mở file cục bộ.

---

## 7. Tính năng có thể gỡ bỏ để tinh gọn

Mức rủi ro: **Thấp** = độc lập, gỡ ít ảnh hưởng; **TB** = có phụ thuộc chéo, cần
kiểm thử; **Cao** = dễ gây lỗi build/chức năng, chỉ làm khi thật cần.

### 7.1. Tầng giao diện / app

| Tính năng | Vị trí chính | Lợi ích | Rủi ro | Ghi chú |
|---|---|---|---|---|
| Bảng quản trị server (admin console) | `browser/admin/` | Giảm bundle, bỏ chuỗi "Collabora Online" | **Thấp** | Không dùng ở desktop; chỉ cần bỏ khỏi `browser/Makefile.am` |
| Hộp thoại kiểm tra server | `Control.ServerAuditDialog.ts` | Bỏ 15 URL Collabora | **Thấp** | Chỉ dành cho quản trị server |
| Trợ lý AI | `Control.AIChatSidebar.ts`, `Notebookbar.AIAssistantTab.ts`, `wsd/AIChatSession.cpp`, `wsd/AIUtil.cpp`, `common/AIHttpTransport.cpp`, phần AI trong `CODA.cpp` | Bỏ kết nối ra ngoài, giảm mã | **TB** | Nhiều chỗ tham chiếu (`registerAIHttpTransport`, menu, cài đặt); làm theo hướng tắt cờ trước, xóa mã sau |
| Zotero | `Control.Zotero.js`, phần CSP | Bỏ kết nối ra ngoài | **Thấp–TB** | Tắt bằng cờ `zoteroEnabled`; xóa mã cần dọn tham chiếu trong `ServerConnectionService.ts`, menu Tham chiếu |
| Hệ thống tiện ích mở rộng + 6 tiện ích mẫu | `browser/extensions/`, `Control.Extension.ts`, `wsd/Extensions.cpp`, `--enable-quickjs` | Bỏ đường gọi mạng tùy ý, bỏ mã định danh `com.collaboraoffice.*` | **TB** | Xóa 6 tiện ích mẫu: rủi ro thấp; gỡ cả cơ chế: TB |
| Chữ ký điện tử qua eIDEasy | `Control.ESignature*.ts` | Bỏ dịch vụ nước ngoài | **Thấp–TB** | Giữ ký số bằng chứng thư cục bộ nếu cần cho văn bản hành chính |
| Cộng tác thời gian thực / mở từ xa / Smart Picker | `Permission.js` (`_showCollabEditChoiceDialog`), `qt/RemoteOpen.*`, `main.js:254-376`, `wsd` `/co/collab` | Đơn giản hóa | **TB** | Chủ yếu dùng ở Qt/WASM; kiểm tra lại luồng Windows |
| Bảng điều khiển người thuyết trình (Presenter console) | `browser/src/slideshow/PresenterConsole.js` | Nhỏ | **TB** | Người dùng trình chiếu có thể cần – nên giữ |
| Trình chiếu chào mừng / "Có gì mới" / Gửi phản hồi | `browser/welcome/`, `Map.Welcome.js`, `Map.Feedback.js` | Bỏ nội dung Collabora | **Thấp** | Thay bằng welcome riêng qua `--with-app-branding` |
| Giao diện di động (mobile wizard, bottom bar…) | `Control.Mobile*.js/ts` | Giảm bundle | **Cao** | Dùng lại cho Android/iOS sau này – **không nên gỡ** |
| Draw (vẽ) | `Control.NotebookbarDraw.js`, `engine/sd` dùng chung với Impress | Ít | **Cao** | Draw dùng chung lõi `sd` với Impress; chỉ có thể ẩn liên kết `.odg` |

### 7.2. Tầng đóng gói / nền tảng (thư mục không cần cho Windows)

| Hạng mục | Vị trí | Rủi ro | Ghi chú |
|---|---|---|---|
| Đóng gói server | `debian/`, `docker/`, `snap/`, `nix/`, `coolwsd.service`, `coolwsd.spec.in`, `coolwsd-systemplate-setup` | **Thấp** | Không ảnh hưởng bản Windows |
| Vỏ Linux Qt + flatpak + FreeBSD | `qt/` (riêng `qt/freebsd` chiếm ~3 700 dòng "Collabora") | **Thấp** | Lưu ý `browser/src/qtapp/` và nhánh `ThisIsQtApp` trong JS – để nguyên cũng được |
| Vỏ macOS, WASM | `macos/`, `wasm/` | **Thấp** | Có thể giữ trong repo nhưng không build |
| Android, iOS | `android/`, `ios/` | – | **Giữ lại** vì là lộ trình giai đoạn 2, 3 |
| Kiểm thử Cypress | `cypress_test/` | **Thấp** với sản phẩm, **TB** với chất lượng | Nên giữ để kiểm thử hồi quy |

### 7.3. Tầng lõi (engine) – qua cấu hình `CODAWindows.conf`

| Hạng mục | Thay đổi | Lợi ích | Rủi ro |
|---|---|---|---|
| Ngôn ngữ giao diện | `INCLUDE:Langs` (41 ngôn ngữ) → `--with-lang=vi en-US` | Build nhanh hơn, bộ cài nhỏ hơn | **Thấp** – phần giao diện web vẫn đa ngôn ngữ riêng |
| Từ điển chính tả | `--with-myspell-dicts` (mọi ngôn ngữ) → chỉ `vi`, `en_US` (chỉnh `engine/dictionaries`) | Giảm vài chục MB | **Thấp** |
| Python nhúng | `--enable-python=fully-internal` → `--disable-python` | Giảm ~50–100 MB | **TB–Cao** – mất macro Python, một số tiện ích chuyển đổi/wizard; cần kiểm thử kỹ |
| Phông chữ đi kèm | `--with-fonts` | Giữ để hiển thị đúng; cân nhắc thêm phông tiếng Việt chuẩn | Gỡ: **Cao** (hiển thị sai văn bản) |
| Ký hiệu gỡ lỗi | bỏ `--enable-symbols` ở bản phát hành | Build nhanh, nhỏ hơn rất nhiều | **Thấp** (khó phân tích lỗi; nên lưu PDB riêng) |
| Bộ lọc định dạng ít dùng (StarOffice, Lotus, WordPerfect, Mac cũ…) | các thư viện `libwpd`, `libmwaw`, `libstaroffice`, `libvisio`… | Giảm dung lượng | **Cao** – cần sửa hệ build gbuild, dễ vỡ liên kết; không khuyến nghị giai đoạn đầu |
| Đã tắt sẵn | Java, Base/DB (`--disable-database-connectivity`), OpenCL, help, gallery, templates, Skia | – | – |

**Khuyến nghị thứ tự thực hiện**: (1) tắt bằng cờ/cấu hình (AI, Zotero,
eIDEasy, ngôn ngữ, từ điển, liên kết ngoài) → (2) bỏ thư mục không build cho
Windows → (3) xóa mã tính năng sau khi đã có bộ kiểm thử hồi quy.

---

## Phụ lục – Phương pháp khảo sát

- Đọc trực tiếp mã nguồn tại commit `70a8dda48`; tìm kiếm bằng `git grep`.
- Bảng thương hiệu sinh bằng `docs/khao-sat/quet-thuong-hieu.py`: tìm mọi dòng
  khớp `collabora|libreoffice|coda` (không phân biệt hoa thường, bỏ qua file nhị
  phân và từ điển chính tả), rồi phân loại theo quy tắc (header bản quyền ở 25
  dòng đầu hoặc dòng có "Copyright"; URL; mã định danh gói; bản dịch; định danh
  mã; chú thích; dữ liệu kiểm thử). Ảnh được liệt kê theo tên/thư mục
  (`logo`, `brand`, `Assets`, `mipmap`, `AppIcon`, `.ico`…).
- Các con số về thời gian build, cấu hình máy và giới hạn GitHub Actions là
  **ước tính/tham khảo**, cần xác nhận khi dựng máy build thật.
