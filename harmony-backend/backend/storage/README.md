# Local Storage Layout

This directory mirrors the no-database storage plan from `backend-design-v1.md`.

```text
storage/
  seeds/          JSON arrays committed to Git and used as startup seed data
  runtime/        JSONL files generated while the service runs; ignored by Git
  kb/faiss_index/ placeholder for a future persistent FAISS index
```

`app/storage/` is the Python repository layer. This `storage/` directory is business data.
