# Emil Mathew — Sheet Music OMR Backend

This backend receives a PDF/PNG/JPG/TIFF score, runs Audiveris in batch mode, extracts the resulting MusicXML, and returns it to the ChordLab frontend.

## Render deployment

1. Put these files in a GitHub repository, for example `emil-omr-backend`.
2. In Render choose **New → Web Service** and connect the repository.
3. Runtime: **Docker**. Plan: **Free** for testing.
4. Deploy and wait for `/health` to report `ok: true` and `audiveris_exists: true`.
5. Copy the service URL, e.g. `https://emil-mathew-omr.onrender.com`.
6. Paste that URL into the OMR BACKEND URL field in the website.

The free Render web service can spin down after 15 minutes without inbound traffic, so the first OMR request after idle can be slow. Larger/complex scores may exceed the free instance's resources; start with a clear 1–2 page score.

## Local test

Build and run with Docker:

```bash
docker build -t emil-omr .
docker run --rm -p 10000:10000 emil-omr
```

Then POST a score to `http://localhost:10000/omr` as multipart field `file`.
