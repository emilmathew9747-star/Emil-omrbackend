import os, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title='Emil Mathew OMR Backend', version='1.0.0')
origins = [x.strip() for x in os.getenv('ALLOWED_ORIGINS','*').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

MAX_BYTES = 25 * 1024 * 1024
ALLOWED = {'.pdf','.png','.jpg','.jpeg','.tif','.tiff'}
AUDIVERIS = os.getenv('AUDIVERIS_BIN','/opt/audiveris/bin/Audiveris')

@app.get('/health')
def health():
    return {'ok': True, 'engine': 'Audiveris', 'audiveris_exists': Path(AUDIVERIS).exists()}

def find_musicxml(folder: Path):
    files = list(folder.rglob('*.mxl')) + list(folder.rglob('*.musicxml')) + list(folder.rglob('*.xml'))
    if not files:
        return None
    # Prefer compressed MusicXML produced by Audiveris.
    return sorted(files, key=lambda p: p.stat().st_size, reverse=True)[0]

def read_musicxml(path: Path):
    if path.suffix.lower() in {'.xml','.musicxml'}:
        return path.read_text(encoding='utf-8', errors='replace')
    with zipfile.ZipFile(path, 'r') as z:
        names = [n for n in z.namelist() if n.lower().endswith(('.xml','.musicxml'))]
        if not names:
            raise RuntimeError('MusicXML file was produced, but no XML score was found inside it.')
        # Ignore META-INF/container.xml when possible.
        names.sort(key=lambda n: ('META-INF' in n, len(n)))
        return z.read(names[0]).decode('utf-8', errors='replace')

def basic_xml_title(xml: str):
    m = re.search(r'<work-title>(.*?)</work-title>', xml, re.S)
    return re.sub('<[^>]+>', '', m.group(1)).strip() if m else 'Recognized score'

@app.post('/omr')
async def omr(file: UploadFile = File(...)):
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, 'Unsupported file. Use PDF, PNG, JPG or TIFF.')
    data = await file.read()
    if not data:
        raise HTTPException(400, 'The uploaded file is empty.')
    if len(data) > MAX_BYTES:
        raise HTTPException(413, 'File is larger than 25 MB.')
    if not Path(AUDIVERIS).exists():
        raise HTTPException(500, 'Audiveris is not installed on this server.')

    with tempfile.TemporaryDirectory(prefix='emil-omr-') as td:
        root = Path(td); inp = root / ('score' + suffix); out = root / 'out'; out.mkdir()
        inp.write_bytes(data)
        cmd = [AUDIVERIS, '-batch', '-transcribe', '-export', '-output', str(out), str(inp)]
        env = os.environ.copy()
        # Keep Java within a small free-instance memory budget where possible.
        env.setdefault('JAVA_TOOL_OPTIONS', '-Xmx384m')
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=240, env=env)
        except subprocess.TimeoutExpired:
            raise HTTPException(504, 'OMR timed out. Try a shorter or clearer score.')
        if proc.returncode != 0:
            tail = (proc.stdout or '')[-3000:]
            raise HTTPException(500, 'Audiveris could not transcribe this score. ' + tail)
        mxl = find_musicxml(out)
        if not mxl:
            raise HTTPException(500, 'Audiveris finished but did not produce MusicXML. Try a clearer score.')
        try:
            xml = read_musicxml(mxl)
        except Exception as e:
            raise HTTPException(500, str(e))
        return JSONResponse({'ok': True, 'title': basic_xml_title(xml), 'musicxml': xml, 'engine': 'Audiveris', 'version': '5.11.0'})
