# Populated-data migration contract

Status: current

Owner: storage maintainers

Scope: local rehearsal for the current checkout

Use the checked-in populated synthetic dataset and an absent disposable work directory:

```text
python -B verify_migration.py --dataset fixtures/populated.json --workdir .runtime/trial
```

The verifier copies the source dataset before migration, confirms the source remains byte-identical, and removes the disposable trial. It proves the supported transformation for this representative fixture only. It does not execute against shared storage, validate production backups, demonstrate rollback, or prove compatibility with unrepresented records.
