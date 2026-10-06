import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Emil Mathew OMR Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Emil Mathew OMR Backend",
        "engine": "HOMR"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "engine": "HOMR"
    }


@app.post("/omr")
async def convert_sheet(file: UploadFile = File(...)):

    allowed = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff"
    }

    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Please upload PDF, PNG, JPG, JPEG, TIF or TIFF."
        )

    workdir = Path(tempfile.mkdtemp(prefix="emil_omr_"))

    try:
        input_file = workdir / f"input{suffix}"

        with open(input_file, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # HOMR works with images.
        # Convert the first PDF page to PNG.
        if suffix == ".pdf":
            png_prefix = workdir / "page"

            subprocess.run(
                [
                    "pdftoppm",
                    "-png",
                    "-r",
                    "200",
                    "-f",
                    "1",
                    "-singlefile",
                    str(input_file),
                    str(png_prefix),
                ],
                check=True,
            )

            input_file = workdir / "page.png"

        output_dir = workdir / "output"
        output_dir.mkdir()

        result = subprocess.run(
            [
                "homr",
                str(input_file),
                "--output_dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr or result.stdout or "HOMR failed."
            )

        musicxml_files = list(output_dir.rglob("*.musicxml"))

        if not musicxml_files:
            musicxml_files = list(output_dir.rglob("*.xml"))

        if not musicxml_files:
            raise RuntimeError(
                "HOMR finished but did not produce a MusicXML file."
            )

        # Copy result outside the cleanup directory so Render can
        # finish sending it before the temporary working directory is removed.
        final_file = Path(tempfile.mktemp(suffix=".musicxml"))
        shutil.copy2(musicxml_files[0], final_file)

        return FileResponse(
            path=str(final_file),
            filename="emil_omr_result.musicxml",
            media_type="application/vnd.recordare.musicxml+xml",
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="OMR processing timed out."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        shutil.rmtree
