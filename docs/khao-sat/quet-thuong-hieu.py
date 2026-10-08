#!/usr/bin/env python3
"""Quét mọi vị trí có 'Collabora' / 'LibreOffice' / 'CODA' trong repo và phân loại.

Đầu ra (trong thư mục outdir):
  thuong-hieu-can-thay.csv      : các vị trí cần thay / cần xem xét
  ban-quyen-giu-nguyen.csv      : thông báo bản quyền / giấy phép (GIỮ NGUYÊN)
  anh-logo.csv                  : các file ảnh / biểu tượng mang thương hiệu
  thong-ke.txt                  : số liệu tổng hợp
"""
import csv
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

repo, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)

PAT = re.compile(r'collabora|libreoffice|\bcoda\b|\bCODA|coda[-_.]|coda(?=[A-Z])|[a-z]Coda\b', re.I)
GREP_PAT = r'collabora|libreoffice|coda'

LICENSE_RE = re.compile(
    r'this file is part of the|copyright|spdx-license|mozilla public|mpl[- ]?2|'
    r'license|licence|giấy phép|all rights reserved', re.I)
LICENSE_FILES = re.compile(
    r'(^|/)(COPYING[^/]*|LICENSE[^/]*|THIRDPARTYLICENSES[^/]*|CODA-THIRDPARTYLICENSES\.html|'
    r'AUTHORS|ChangeLog|NEWS|SBOM\.md|README\.FILENOTICES\.md|copyright|credits[^/]*|'
    r'license[^/]*\.(txt|html|md|xml))$', re.I)
URL_RE = re.compile(r'(https?|ssh|git)://|www\.|[a-z0-9-]+\.(collabora[a-z]*|libreoffice|documentfoundation)\.(com|org|net)|'
                    r'(collaboraoffice|collaboraonline|libreoffice|documentfoundation)\.(com|org|net)', re.I)
PKG_RE = re.compile(
    r'\b(com|org)\.collabora[\w.]*|\bcom\.collaboraoffice[\w.]*|\borg\.libreoffice[\w.]*|'
    r'CollaboraProductivityLtd[\w.]*|vnd\.(libreoffice|collabora)[\w.-]*|'
    r'PRODUCT_BUNDLE_IDENTIFIER|applicationId|<Identity\b|Publisher="CN=|'
    r'\bApplication Id="CODA"|PACKAGE_ID|AppUserModelID|ProgID|\bnamespace\s+\'org\.', re.I)
JAVA_PKG_RE = re.compile(r'^\s*(package|import)\s+org\.libreoffice', re.I)
# Định danh trong mã nguồn, không hiển thị cho người dùng: đổi tên gây vỡ API/build.
IDENT_RE = re.compile(
    r'LibreOfficeKit|\bLOK|lok_|LIBREOFFICEKIT|\bisCODesktop|CODesktop|CODA_[A-Z_]+|coda_[a-z_]+|'
    r'CODocumentBroker|COOLWSD|ENABLE_CODA|\bCODA\.(sln|vcxproj|cpp|rc|ico)|CODALib|coda-qt|'
    r'collabora_|_collabora|Collabora[A-Z]\w+|libreoffice_|LIBREOFFICE_|LibreOffice[A-Z]\w+|'
    r'\$\(LIBO_|libo_|LIBO_|org\.libreoffice\.androidlib|LOActivity|\.uno:|'
    r'--with-distro=CODA|CODAWindows|brand_cp|vnd\.libreoffice\.command|"coda"|\'coda\'|coda\.|'
    r'qt/coda|windows/coda|/coda/|\bcodaapp\b|\bCODA\b(?=\s*[(=:;,)\]])')
COMMENT_RE = re.compile(r'^\s*(//|#|\*|/\*|<!--|;|--|%|rem\b|\'|dnl\b)', re.I)

IMG_EXT = ('.png', '.ico', '.icns', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.xcf', '.tiff')
IMG_NAME_RE = re.compile(r'collabora|libreoffice|coda|logo|brand|splash|about|intro|appicon|app_icon|'
                         r'ic_launcher|AppIcon|Square\d+x\d+|StoreLogo|favicon|mipmap|\.ico$|\.icns$', re.I)
IMG_DIR_RE = re.compile(r'(^|/)(Assets|branding|brand[^/]*|mipmap[^/]*|AppIcon[^/]*\.appiconset|icons?)(/|$)', re.I)

TRANSLATION_RE = re.compile(r'(\.po|\.pot|\.ts|\.xlf)$|/po/|/translations/|/l10n/', re.I)


TEST_RE = re.compile(r'(^|/)(qa|uitest|test|tests|cypress_test|unittest|fixtures|documentation|dev-notes|fuzzer|samples)(/|$)|\.fods$|\.fodt$|\.fodp$', re.I)
DICT_RE = re.compile(r'\.(dic|aff|dat|idx)$|/dictionaries/.*th_|/thes_', re.I)
PO_META_RE = re.compile(r'^"?(Language-Team|Report-Msgid-Bugs-To|X-Generator|Last-Translator|Project-Id-Version)', re.I)


def classify(path, line_no, text):
    stripped = text.strip()
    if JAVA_PKG_RE.search(stripped) is None and re.match(r'(from|import)\s+libreoffice', stripped):
        return 'định danh trong mã (không hiển thị)', 'KHÔNG ĐỔI (module Python nội bộ)'
    if TEST_RE.search(path) and not (LICENSE_FILES.search(path) or LICENSE_RE.search(stripped) and line_no <= 25):
        return 'dữ liệu kiểm thử / tài liệu nội bộ', 'KHÔNG BẮT BUỘC'
    if TRANSLATION_RE.search(path) and PO_META_RE.search(stripped.lstrip('#').strip()):
        return 'siêu dữ liệu bản dịch', 'KHÔNG BẮT BUỘC'
    if path.startswith('engine/') and re.search(r'org\.libreoffice|org\.openoffice|vnd\.libreoffice|com\.collabora', stripped, re.I) \
            and not re.search(r'distro-configs|instsetoo|scp2|setup_native|sysui|postprocess|desktop/win32|shell/source/win32', path):
        return 'định danh trong mã (không hiển thị)', 'KHÔNG ĐỔI (tên dịch vụ UNO/cấu hình nội bộ)'
    if LICENSE_FILES.search(path) or (LICENSE_RE.search(stripped) and (line_no <= 25 or 'copyright' in stripped.lower())):
        return 'ban-quyen-MPL', 'GIỮ NGUYÊN'
    if JAVA_PKG_RE.search(stripped):
        return 'mã định danh gói (namespace Java)', 'XEM XÉT (đổi kèm toàn bộ thư mục android/)'
    if PKG_RE.search(stripped):
        return 'mã định danh gói', 'THAY → vn.senoffice.desktop (hoặc tương ứng)'
    if URL_RE.search(stripped):
        if TRANSLATION_RE.search(path):
            return 'URL (bản dịch)', 'THAY (sửa chuỗi gốc rồi sinh lại bản dịch)'
        if COMMENT_RE.search(stripped):
            return 'URL (trong chú thích)', 'KHÔNG BẮT BUỘC'
        return 'URL', 'THAY / GỠ'
    if TRANSLATION_RE.search(path):
        return 'chữ (bản dịch)', 'THAY (sinh lại từ bản dịch)'
    if IDENT_RE.search(text):
        return 'định danh trong mã (không hiển thị)', 'KHÔNG ĐỔI (đổi gây vỡ build/API)'
    if COMMENT_RE.search(stripped):
        return 'chữ (chú thích mã)', 'KHÔNG BẮT BUỘC'
    return 'chữ', 'THAY'


def area(path):
    top = path.split('/', 1)[0]
    if path.startswith('windows/'):
        return 'vỏ Windows'
    if top in ('qt', 'macos', 'android', 'ios', 'wasm'):
        return 'vỏ ' + top
    if top == 'browser':
        return 'giao diện web'
    if top == 'engine':
        return 'lõi engine'
    if top in ('wsd', 'kit', 'common', 'net'):
        return 'lõi online (C++)'
    return 'khác (' + top + ')'


ls = subprocess.run(['git', '-C', repo, 'ls-files', '-z'], capture_output=True, check=True).stdout
files = [f.decode('utf-8', 'surrogateescape') for f in ls.split(b'\0') if f]

grep = subprocess.run(['git', '-C', repo, 'grep', '-n', '-I', '-i', '-E', GREP_PAT],
                      capture_output=True).stdout.decode('utf-8', 'replace')

stats = Counter()
stats_area = defaultdict(Counter)
replace_rows, license_rows = [], []
for raw in grep.splitlines():
    try:
        path, ln, text = raw.split(':', 2)
        ln = int(ln)
    except ValueError:
        continue
    if not PAT.search(text):
        continue
    if DICT_RE.search(path):
        continue
    kind, action = classify(path, ln, text)
    stats[kind] += 1
    stats_area[area(path)][kind] += 1
    snippet = ' '.join(text.strip().split())[:160]
    row = [path, ln, kind, action, area(path), snippet]
    (license_rows if kind == 'ban-quyen-MPL' else replace_rows).append(row)

img_rows = []
for f in files:
    if f.lower().endswith(IMG_EXT) and (IMG_NAME_RE.search(os.path.basename(f)) or IMG_DIR_RE.search(f)):
        if f.startswith('engine/icon-themes/') and 'brand' not in f:
            continue
        img_rows.append([f, '-', 'ảnh', 'THAY bằng logo SenOffice', area(f), ''])
        stats['ảnh'] += 1
        stats_area[area(f)]['ảnh'] += 1

hdr = ['duong_dan', 'dong', 'loai', 'hanh_dong', 'khu_vuc', 'trich_doan']
agg = {}
for r in license_rows:
    a = agg.setdefault(r[0], [r[0], [], r[2], r[3], r[4], r[5]])
    a[1].append(str(r[1]))
def notice_kind(t):
    t = t.lower()
    if 'part of the collabora office project' in t: return 'header MPL: Collabora Office project'
    if 'part of the libreoffice project' in t: return 'header MPL: LibreOffice project'
    if 'collabora online contributors' in t: return 'Copyright the Collabora Online contributors'
    if 'collabora office contributors' in t: return 'Copyright the Collabora Office contributors'
    if 'copyright' in t: return 'dòng Copyright khác'
    return 'văn bản giấy phép / ghi công'
license_rows = [[a[0], ' '.join(a[1]), notice_kind(a[5]), 'GIỮ NGUYÊN'] for a in agg.values()]
stats['so file co thong bao ban quyen'] = len(license_rows)
for name, rows, h in (('thuong-hieu-can-thay.csv', replace_rows, hdr),
                   ('ban-quyen-giu-nguyen.csv', license_rows, ['duong_dan', 'cac_dong', 'loai_thong_bao', 'hanh_dong']),
                   ('anh-logo.csv', img_rows, hdr)):
    rows.sort(key=lambda r: (r[0], r[1] if isinstance(r[1], int) else 0))
    with open(os.path.join(outdir, name), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(h)
        w.writerows(rows)

with open(os.path.join(outdir, 'thong-ke.txt'), 'w', encoding='utf-8') as fh:
    for k, v in stats.most_common():
        fh.write(f'{k}\t{v}\n')
    fh.write('\n')
    for a in sorted(stats_area):
        fh.write(a + '\t' + ', '.join(f'{k}={v}' for k, v in stats_area[a].most_common()) + '\n')
print(open(os.path.join(outdir, 'thong-ke.txt'), encoding='utf-8').read())
